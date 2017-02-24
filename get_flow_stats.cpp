/*
 *  Original program by Tony Lukasavage
 *  Taken from: http://tonylukasavage.com/blog/2010/12/19/offline-packet-capture-analysis-with-c-c----amp--libpcap/
 *  date: 09/11/2015 (original post: 19/12/2010)
 */

#include <string>
#include <iostream>
#include <cstdio>
#include <unistd.h>
#include <sstream>
#include <fstream>
#include <pcap.h>
#include <map>
#include <ctime>
#include <net/ethernet.h>
#include <netinet/ip.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>
#include <arpa/inet.h>
#include <boost/filesystem.hpp>

#include "FlowStatsTable.h"
#include "utils.h"

using namespace std;
using namespace boost::filesystem;

struct flow_stats {
    unsigned long id;
    struct timeval first_ts;
    struct timeval last_ts;
    unsigned long count;
    unsigned long total_data;
};

// Arguments passed to the packetHandler function (see below).
// In particular, a pointer to such a struct is passed as the userData param.
struct packetHandler_args {
    FlowStatsTable *flow_table;
    ostream *packet_out;
};

// This function handles a single packet, and is used by the pcap_loop function
void packetHandler(u_char *userData, const struct pcap_pkthdr* pkthdr,
                   const u_char* packet);

// Creates a string representing the fivetuple provided (to identify a flow)
string create_fivetuple_id(const char *sourceIp, const char *destIp,
                           int ipProto, u_int sourcePort, u_int destPort);

void output_packet_description(ostream &out, unsigned long flowid,
                               char *sourceIp, char *destIp,
                               int ipProto, u_int sourcePort, u_int destPort,
                               const struct pcap_pkthdr* pkthdr);

// main: processes the pcap files provided as command line arguments,
// and extrapolates the flows and statistics about them.
int main(int argc, char *argv[]) {
    pcap_t *descr;
    char errbuf[PCAP_ERRBUF_SIZE];
    ofstream packet_out, statFile;
    time_t curr_time;
    FlowStatsTable flow_table;
    struct packetHandler_args pkthandler_args = {&flow_table, &cout};
    path packet_output_dir (absolute("data_output/packets"));
    path flow_stats_output_dir (absolute("data_output/flow_stats"));
    create_directories(packet_output_dir);
    create_directories(flow_stats_output_dir);

    if (argc < 2) {
        cerr << "Usage: " << argv[0] << " pcap_file..." << endl;
        return 1;
    }

    // Set failing bits for all fstream's
    // (by default one would have to check manually if if the fstream has failed)
    packet_out.exceptions(ofstream::failbit | ofstream::badbit);
    statFile.exceptions(ofstream::failbit | ofstream::badbit);

    for (int i=1; i<argc; i++) {
        path in_file (argv[i]);
        time(&curr_time);
        if (!is_regular_file(in_file)) {
            cerr << ctime(&curr_time) << " Warning: " << in_file
                 << " does not exist, skipping.." << endl;
            continue;
        }

        cout << ctime(&curr_time) << " Processing file " << i << ": "
             << in_file << endl;

        // open capture file for offline processing
        descr = pcap_open_offline(in_file.string().c_str(), errbuf);
        if (descr == NULL) {
            cerr << "pcap_open_offline() failed on file " << in_file << ": "
                 << errbuf << endl;
            return 1;
        }

        // get new output file for packet list output
        path packet_output_file (packet_output_dir /
            in_file.stem().replace_extension(".processed_pcap"));
        packet_out.open(packet_output_file.string());
        pkthandler_args.packet_out = &packet_out;

        // Start packet processing loop, just like live capture.
        // For each packet, packetHandler is called to process it
        if (pcap_loop(descr, 0, packetHandler, (u_char *)&pkthandler_args) < 0) {
            cerr << "pcap_loop() failed: " << pcap_geterr(descr) << endl;
            return 1;
        }
        pcap_close(descr);
        packet_out.close();

        time(&curr_time);
        cout << ctime(&curr_time) << " Storing stats of expired flows" << endl;

        // get new output file for the stats of expired flows
        path flow_stats_output_file (flow_stats_output_dir /
            in_file.stem().replace_extension(".expired_flows"));
        statFile.open(flow_stats_output_file.string());

        // Check expired flows, write their stats to file, and delete the
        // entries
        if (flow_table.collect_expired_flows() > 0) {
            flow_table.print_expired_flows(statFile);
            flow_table.erase_expired_flows();
        }
        statFile.close();
    }

    return 0;
}// end main


void packetHandler(u_char *userData, const struct pcap_pkthdr* pkthdr, const u_char* packet) {
    const struct ip* ipHeader;
    const struct tcphdr* tcpHeader;
    const struct udphdr* udpHeader;
    char sourceIp[INET_ADDRSTRLEN];
    char destIp[INET_ADDRSTRLEN];
    u_int sourcePort = 0, destPort = 0;
    string fivetuple;
    unsigned long current_flow_id;
    struct packetHandler_args* args = (struct packetHandler_args *)userData;

    ipHeader = (struct ip*)packet;
    inet_ntop(AF_INET, &(ipHeader->ip_src), sourceIp, INET_ADDRSTRLEN);
    inet_ntop(AF_INET, &(ipHeader->ip_dst), destIp, INET_ADDRSTRLEN);

    // Retrieve source and destination port for TCP or UDP protocol
    if (ipHeader->ip_p == IPPROTO_TCP) {
      tcpHeader = (tcphdr*)(packet + sizeof(struct ip));
      sourcePort = ntohs(tcpHeader->source);
      destPort = ntohs(tcpHeader->dest);
    }
    if (ipHeader->ip_p == IPPROTO_UDP) {
      udpHeader = (udphdr*)(packet + sizeof(struct ip));
      sourcePort = ntohs(udpHeader->source);
      destPort = ntohs(udpHeader->dest);
    }

    fivetuple = create_fivetuple_id(sourceIp, destIp, (int)ipHeader->ip_p,
                                  sourcePort, destPort);

    current_flow_id = args->flow_table->register_new_packet(fivetuple,
                                                          &pkthdr->ts,
                                                          pkthdr->len);

    // Print out the packet description together with the ID of the flow it
    // belongs to.
    output_packet_description(*(args->packet_out), current_flow_id, sourceIp,
            destIp, (int)ipHeader->ip_p, sourcePort, destPort, pkthdr);

}


string create_fivetuple_id(const char *sourceIp, const char *destIp,
                           int ipProto, u_int sourcePort, u_int destPort) {
    stringstream sstm;
    sstm << sourceIp << "#" << destIp << "#" << ipProto << "#" << sourcePort
       << "#" << destPort;
    return sstm.str();
}


/* This function prints out the packet description of the given packet together
 * with the flow ID. The function gets as input the entire packet header, so it
 * can be changed to print out more information if required.
 */
void output_packet_description(ostream &out, unsigned long flowid,
                               char *sourceIp, char *destIp,
                               int ipProto, u_int sourcePort, u_int destPort,
                               const struct pcap_pkthdr* pkthdr) {
    out << flowid << "\t" << sourceIp << "\t" << destIp << "\t"
      << ipProto << "\t" << sourcePort << "\t" << destPort << "\t>\t";

    out << pkthdr->len << "\t" << pkthdr->ts.tv_sec << "\t" << pkthdr->ts.tv_usec << endl;
}

