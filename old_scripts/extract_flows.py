from __future__ import print_function
import sys, os, gzip
from scapy.all import *

USAGE="extract_flows.py infile.pcap.gz outfile.txt"

def write_pkt_record(p, outfile=sys.stdout):
    if IP not in p:
        return      # Only considering IP packets
    outfile.write(str(p.time))
    outfile.write("\t")
    ip_p = p.getlayer(IP)
    outfile.write("\t{}\t{}\t{}".format(ip_p.src, ip_p.dst, ip_p.proto))
    if TCP in p or UDP in p:
        outfile.write("\t{}\t{}".format(p.sport, p.dport))
    outfile.write("\n")

def extract_and_dump_pkt_info():
    if len(sys.argv) < 3:
        print("Expected input file", file=sys.stderr)
        sys.exit(1)
    try:
        with open(sys.argv[2], 'w') as outfile:
#        with gzip.open(sys.argv[1], 'rb') as zipped_file, gzip.open(sys.argv[2], 'w') as out_file:
            pcap_reader = PcapReader(sys.argv[1])
            for p in pcap_reader:
                if IP not in p:
                    return      # Only considering IP packets
                outfile.write(str(p.time))
                outfile.write("\t")
                ip_p = p.getlayer(IP)
                outfile.write("\t{}\t{}\t{}".format(ip_p.src, ip_p.dst, ip_p.proto))
                if TCP in p or UDP in p:
                    outfile.write("\t{}\t{}".format(p.sport, p.dport))
                outfile.write("\n")
    except IOError as e:
        print("Unable to open file", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    extract_and_dump_pkt_info()
