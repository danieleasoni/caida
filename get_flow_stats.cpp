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
#include <time.h>
#include <net/ethernet.h>
#include <netinet/ip.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>
#include <arpa/inet.h>

#include "utils.h"

using namespace std;

struct flow_stats {
    unsigned long id;
    struct timeval first_ts;
    struct timeval last_ts;
    unsigned long count;
    unsigned long total_data;
};

unsigned long flow_counter = 0;

typedef map<string,struct flow_stats>::iterator map_iter_type;

struct packetHandler_args {
    map<string,struct flow_stats> *flows;
};

void packetHandler(u_char *userData, const struct pcap_pkthdr* pkthdr, const u_char* packet);

string create_fivetuple_id(const char *sourceIp, const char *destIp, int ipProto,
                           u_int sourcePort, u_int destPort, bool forward=true) {
  stringstream sstm;
  if (forward)
      sstm << sourceIp << "#" << destIp << "#" << ipProto << "#" << sourcePort << "#" << destPort;
  else
      sstm << destIp << "#" << sourceIp << "#" << ipProto << "#" << destPort << "#" << sourcePort;
  return sstm.str();
}

void generate_stats_file(const string filename, map<string, struct flow_stats> *flows) {
  float flow_duration;
  float pkts_per_sec;
  float bytes_per_sec;
  ofstream statFile;
  statFile.open(filename);
  for (map_iter_type iterator = flows->begin(); iterator != flows->end(); iterator++) {
      flow_duration = timeval_to_seconds(&(iterator->second.last_ts)) - timeval_to_seconds(&(iterator->second.first_ts));
      pkts_per_sec = iterator->second.count / flow_duration;
      bytes_per_sec = iterator->second.total_data / flow_duration;
      statFile << iterator->second.id << "\t" << iterator->second.count << "\t" << flow_duration << "\t" << pkts_per_sec << "\t" << bytes_per_sec << endl;
  }
  statFile.close();
}

void output_packet_description(ostream &out, unsigned long flowid, char *sourceIp, char *destIp,
                               int ipProto, u_int sourcePort, u_int destPort,
                               const struct pcap_pkthdr* pkthdr, bool forward=true) {
  if (forward)
      out << flowid << "\t" << sourceIp << "\t" << destIp << "\t"
          << ipProto << "\t" << sourcePort << "\t" << destPort << "\t>\t";
  else
      out << flowid << "\t" << destIp << "\t" << sourceIp << "\t"
          << ipProto << "\t" << destPort << "\t" << sourcePort << "\t<\t";

  out << pkthdr->len << "\t" << pkthdr->ts.tv_sec << "\t" << pkthdr->ts.tv_usec << endl;
}

int main(int argc, char *argv[]) {
  pcap_t *descr;
  char errbuf[PCAP_ERRBUF_SIZE];
  const char *in_file = "";
  float flow_duration;
  float pkts_per_sec;
  float bytes_per_sec;
  ofstream outFile;
  string outFile_name, statFile_name;
  time_t tim;
  map<string,struct flow_stats> flows;
  struct packetHandler_args pkthandler_args = {&flows};

  if (argc < 2) {
      cerr << "Usage: " << argv[0] << " pcap_file..." << endl;
      return 1;
  }

  outFile_name = get_new_filename("processing_status", ".tmp");
  outFile.open(outFile_name);

  for (int i=1; i<argc; i++) {
      in_file = argv[i];
      time(&tim);
      outFile << ctime(&tim) << " Processing file " << i << ": " << in_file << endl;

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

  time(&tim);
  outFile << ctime(&tim) << " Starting generation of flow stats" << endl;

  statFile_name = get_new_filename("flow_stats");
  generate_stats_file(statFile_name, &flows);

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
  pair<map_iter_type,bool> ret_value;
  unsigned long current_flow;
  struct flow_stats *current_flow_stats_ptr;
  struct flow_stats tmp_flow_stats;
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

  fivetuple = create_fivetuple_id(sourceIp, destIp, (int)ipHeader->ip_p, sourcePort, destPort);

  // Get pointer to the flow_stats struct in flows map that has the key equal
  // to the current fivetuple, or create a new struct if the key is not in the map
  tmp_flow_stats = {flow_counter, pkthdr->ts, pkthdr->ts, 0L, 0L};
  ret_value = args->flows->emplace(fivetuple, tmp_flow_stats);
  if (ret_value.second) {
      flow_counter++;
  }
  current_flow_stats_ptr = &ret_value.first->second;
  current_flow_stats_ptr->count++;
  current_flow_stats_ptr->last_ts = pkthdr->ts;
  current_flow_stats_ptr->total_data = pkthdr->len;
  current_flow = current_flow_stats_ptr->id;

  output_packet_description(cout, current_flow, sourceIp, destIp, (int)ipHeader->ip_p,
                            sourcePort, destPort, pkthdr);

}

