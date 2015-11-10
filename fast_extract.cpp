/*
 *  Original program by Tony Lukasavage
 *  Taken from: http://tonylukasavage.com/blog/2010/12/19/offline-packet-capture-analysis-with-c-c----amp--libpcap/
 *  date: 09/11/2015 (original post: 19/12/2010)
 */

#include <string.h>
#include <iostream>
#include <fstream>
#include <pcap.h>
#include <net/ethernet.h>
#include <netinet/ip.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>
#include <arpa/inet.h>

using namespace std;

void packetHandler(u_char *userData, const struct pcap_pkthdr* pkthdr, const u_char* packet);

int main(int argc, char *argv[]) {
  pcap_t *descr;
  char errbuf[PCAP_ERRBUF_SIZE];
  const char *in_file = "";
  const char *out_file = "";

  if (argc != 3) {
      cerr << "Expecting 2 command line args (input pcap file and output file)" << endl;
      return 1;
  }

  in_file = argv[1];
  out_file = argv[2];

  // open capture file for offline processing
  descr = pcap_open_offline(in_file, errbuf);
  if (descr == NULL) {
      cerr << "pcap_open_live() failed: " << errbuf << endl;
      return 1;
  }

  // start packet processing loop, just like live capture
  if (pcap_loop(descr, 0, packetHandler, NULL) < 0) {
      cerr << "pcap_loop() failed: " << pcap_geterr(descr) << endl;
      return 1;
  }

//  cout << "capture finished" << endl;

  return 0;
}

void packetHandler(u_char *userData, const struct pcap_pkthdr* pkthdr, const u_char* packet) {
  const struct ether_header* ethernetHeader;
  const struct ip* ipHeader;
  const struct tcphdr* tcpHeader;
  const struct udphdr* udpHeader;
  char sourceIp[INET_ADDRSTRLEN];
  char destIp[INET_ADDRSTRLEN];
  u_int sourcePort = 0, destPort = 0;
  bool fwd;
//  u_char *data;
  int data_length = 0;
//  string dataStr = "";

  ethernetHeader = (struct ether_header*)packet;
  if (ntohs(ethernetHeader->ether_type) == ETHERTYPE_IP) {
      cout << "IP packet" << endl;
      ipHeader = (struct ip*)(packet + sizeof(struct ether_header));
      inet_ntop(AF_INET, &(ipHeader->ip_src), sourceIp, INET_ADDRSTRLEN);
      inet_ntop(AF_INET, &(ipHeader->ip_dst), destIp, INET_ADDRSTRLEN);

      if (ipHeader->ip_p == IPPROTO_TCP) {
          tcpHeader = (tcphdr*)(packet + sizeof(struct ether_header) + sizeof(struct ip));
          sourcePort = ntohs(tcpHeader->source);
          destPort = ntohs(tcpHeader->dest);
      }

      if (ipHeader->ip_p == IPPROTO_UDP) {
          udpHeader = (udphdr*)(packet + sizeof(struct ether_header) + sizeof(struct ip));
          sourcePort = ntohs(udpHeader->source);
          destPort = ntohs(udpHeader->dest);
      }

      if (strcmp(sourceIp,destIp) < 0) {
          cout << sourceIp << "\t" << destIp << "\t" << (int)ipHeader->ip_p << "\t";
          fwd = true;
      } else {
          cout << destIp << "\t" << sourceIp << "\t" << (int)ipHeader->ip_p << "\t";
          fwd = false;
      }

      cout << (int)ipHeader->ip_p;

      if (fwd)
          cout << sourcePort << "\t" << destPort << "\t>\t";
      else
          cout << destPort << "\t" << sourcePort << "\t<\t";

//      data = (u_char*)(packet + sizeof(struct ether_header) + sizeof(struct ip) + sizeof(struct tcphdr));
      data_length = pkthdr->len - sizeof(struct ether_header);
      cout << data_length << "\t" << pkthdr->ts.tv_sec << "\t" << pkthdr->ts.tv_usec << endl;

          // convert non-printable characters, other than carriage return, line feed,
          // or tab into periods when displayed.
//          for (int i = 0; i < dataLength; i++) {
//              if ((data[i] >= 32 && data[i] <= 126) || data[i] == 10 || data[i] == 11 || data[i] == 13) {
//                  dataStr += (char)data[i];
//              } else {
//                  dataStr += ".";
//              }
//          }

          // print the results
//          cout << sourceIp << ":" << sourcePort << " -> " << destIp << ":" << destPort << "\t" << (int)ipHeader->ip_p << endl;
//          if (dataLength > 0) {
//              cout << dataStr << endl;
//          }
  }
}
