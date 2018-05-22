#include "FlowId.h"

#include <string.h>
#include <sstream>

using namespace std;

FlowId::FlowId(char const* source_ip, char const* dest_ip, u_int source_port,
        u_int dest_port, int proto)
        : source_port(source_port), dest_port(dest_port), proto(proto) {
    strcpy(this->source_ip, source_ip);
    strcpy(this->dest_ip, dest_ip);
}

FlowId::FlowId(FlowId const& flow_id_to_copy)
        : source_port(flow_id_to_copy.source_port),
        dest_port(flow_id_to_copy.dest_port), proto(flow_id_to_copy.proto) {
    strcpy(this->source_ip, flow_id_to_copy.source_ip);
    strcpy(this->dest_ip, flow_id_to_copy.dest_ip);
}


string FlowId::get_fivetuple_str() const {
    stringstream sstm;
    sstm << source_ip << "#" << dest_ip << "#" << proto << "#" << source_port
       << "#" << dest_port;
    return sstm.str();
}
