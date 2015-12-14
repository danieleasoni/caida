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

#include "FlowStatsTable.h"
#include "utils.h"

using namespace std;

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
  const char *in_file = "";
  ofstream outFile, statFile;
  string outFile_name, statFile_name;
  time_t curr_time;
  FlowStatsTable flow_table;
  struct packetHandler_args pkthandler_args = {&flow_table};

  if (argc < 2) {
      cerr << "Usage: " << argv[0] << " pcap_file..." << endl;
      return 1;
  }

  outFile_name = get_new_filename("processing_status", ".tmp");
  outFile.open(outFile_name);

  for (int i=1; i<argc; i++) {
      in_file = argv[i];
      time(&curr_time);
      outFile << ctime(&curr_time) << " Processing file " << i << ": " << in_file << endl;

      // open capture file for offline processing
      descr = pcap_open_offline(in_file, errbuf);
      if (descr == NULL) {
          cerr << "pcap_open_offline() failed on file " << in_file << ": " << errbuf << endl;
          return 1;
      }

      // start packet processing loop, just like live capture
      if (pcap_loop(descr, 0, packetHandler, (u_char *)&pkthandler_args) < 0) {
          cerr << "pcap_loop() failed: " << pcap_geterr(descr) << endl;
          return 1;
      }

      pcap_close(descr);
  }

  time(&curr_time);
  outFile << ctime(&curr_time) << " Starting generation of flow stats" << endl;

  statFile_name = get_new_filename("flow_stats");
  statFile.open(statFile_name);
  flow_table.print_all_flows(statFile);
  statFile.close();

  outFile.close();

  return 0;
}

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

  output_packet_description(cout, current_flow_id, sourceIp, destIp,
                            (int)ipHeader->ip_p, sourcePort, destPort, pkthdr);

}// end main

string create_fivetuple_id(const char *sourceIp, const char *destIp,
                           int ipProto, u_int sourcePort, u_int destPort) {
  stringstream sstm;
  sstm << sourceIp << "#" << destIp << "#" << ipProto << "#" << sourcePort
       << "#" << destPort;
  return sstm.str();
}

void output_packet_description(ostream &out, unsigned long flowid,
                               char *sourceIp, char *destIp,
                               int ipProto, u_int sourcePort, u_int destPort,
                               const struct pcap_pkthdr* pkthdr) {
  out << flowid << "\t" << sourceIp << "\t" << destIp << "\t"
      << ipProto << "\t" << sourcePort << "\t" << destPort << "\t>\t";

  out << pkthdr->len << "\t" << pkthdr->ts.tv_sec << "\t" << pkthdr->ts.tv_usec << endl;
}

