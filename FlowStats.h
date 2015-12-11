#ifndef NETSEC_FLOWSTATS_H_
#define NETSEC_FLOWSTATS_H_

#include <ctime>
#include <ostream>

/* FlowStats contains the main statistics of a flow */
class FlowStats {
    friend std::ostream& operator<<(std::ostream &, const FlowStats &);
    const unsigned long _id;
    const struct timeval _first_ts; // Timestamp of the first packet
    struct timeval _last_ts; // Timestamp of the last packet
    unsigned long _pkt_count; // Total number of packet seen for this flow
    unsigned long _total_bytes; // Total number of bytes seen for this flow

public:
    // Fast constructor that takes the information about the first packet
    FlowStats(unsigned long id, struct timeval first_ts,
              unsigned long first_bytes);

    // Check if a flow is expired at the time provided
    bool is_expired (const struct timeval *at_time) const;

    // Return the duration of the flow (so far) in seconds
    float get_flow_duration () const;

    // Count a packet for the statistics of this flow
    void register_packet(const struct timeval *ts, unsigned long num_bytes);
};

std::ostream& operator<<(std::ostream &, const FlowStats &);


#endif // NETSEC_FLOWSTATS_H_
