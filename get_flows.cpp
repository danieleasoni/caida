/*
 *  Original program by Tony Lukasavage
 *  Taken from: http://tonylukasavage.com/blog/2010/12/19/offline-packet-capture-analysis-with-c-c----amp--libpcap/
 *  date: 09/11/2015 (original post: 19/12/2010)
 */

#include <string.h>
#include <iostream>
#include <sstream>
#include <pcap.h>
#include <map>
#include <net/ethernet.h>
#include <netinet/ip.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>
#include <arpa/inet.h>

using namespace std;

map<string,long> flows;
unsigned long flow_counter = 0;

void packetHandler(u_char *userData, const struct pcap_pkthdr* pkthdr, const u_char* packet);

int main(int argc, char *argv[]) {
  pcap_t *descr;
  char errbuf[PCAP_ERRBUF_SIZE];
  const char *in_file = "";

  if (argc != 2) {
      cerr << "Expecting 1 command line argument (input pcap file)" << endl;
      return 1;
  }

  for (int i=1; i<argc; i++) {
      in_file = argv[i];

      // open capture file for offline processing
      descr = pcap_open_offline(in_file, errbuf);
      if (descr == NULL) {
          cerr << "pcap_open_offline() failed on file " << argv[i] << ": " << errbuf << endl;
          return 1;
      }

      // start packet processing loop, just like live capture
      if (pcap_loop(descr, 0, packetHandler, NULL) < 0) {
          cerr << "pcap_loop() failed: " << pcap_geterr(descr) << endl;
          return 1;
      }

      pcap_close(descr);
  }

  return 0;
}

void packetHandler(u_char *userData, const struct pcap_pkthdr* pkthdr, const u_char* packet) {
  const struct ip* ipHeader;
  const struct tcphdr* tcpHeader;
  const struct udphdr* udpHeader;
  char sourceIp[INET_ADDRSTRLEN];
  char destIp[INET_ADDRSTRLEN];
  u_int sourcePort = 0, destPort = 0;
  bool fwd;
  int data_length = 0;
  stringstream sstm;
  string fivetuple;
  pair<map<string,long>::iterator,bool> ret_value;
  unsigned long current_flow;

  ipHeader = (struct ip*)packet;
  inet_ntop(AF_INET, &(ipHeader->ip_src), sourceIp, INET_ADDRSTRLEN);
  inet_ntop(AF_INET, &(ipHeader->ip_dst), destIp, INET_ADDRSTRLEN);

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

  fwd = (strcmp(sourceIp,destIp) < 0);

  if (fwd)
      sstm << sourceIp << "#" << destIp << "#" << (int)ipHeader->ip_p << "#" << sourcePort << "#" << destPort;
  else
      sstm << destIp << "#" << sourceIp << "#" << (int)ipHeader->ip_p << "#" << destPort << "#" << sourcePort;
  fivetuple = sstm.str();

  ret_value = flows.emplace(fivetuple, flow_counter);
  if (ret_value.second) {
      flow_counter++;
  }
  current_flow = ret_value.first->second;

  if (fwd)
      cout << current_flow << "\t" << sourceIp << "\t" << destIp << "\t" << (int)ipHeader->ip_p << "\t" << sourcePort << "\t" << destPort << "\t>\t";
  else
      cout << current_flow << "\t" << destIp << "\t" << sourceIp << "\t" << (int)ipHeader->ip_p << "\t" << destPort << "\t" << sourcePort << "\t<\t";

  data_length = pkthdr->len;
  cout << data_length << "\t" << pkthdr->ts.tv_sec << "\t" << pkthdr->ts.tv_usec << endl;

}
