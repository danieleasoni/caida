#ifndef NETSEC_FLOWID_H_
#define NETSEC_FLOWID_H_

#include <string>
#include <arpa/inet.h>

class FlowId {
public:
    char source_ip[INET_ADDRSTRLEN];
    char dest_ip[INET_ADDRSTRLEN];
    const u_int source_port = 0;
    const u_int dest_port = 0;
    const int proto;

    FlowId(char const* source_ip, char const* dest_ip, u_int source_port,
           u_int dest_port, int proto);

    FlowId(FlowId const& flow_id_to_copy);

    std::string get_fivetuple_str() const;
};

#endif // NETSEC_FLOWID_H_
