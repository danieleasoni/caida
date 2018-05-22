#ifndef NETSEC_FLOWSTATS_H_
#define NETSEC_FLOWSTATS_H_

#include <ctime>
#include <ostream>
#include <stdexcept>
#include <string>
#include <vector>

#include "FlowId.h"

/* FlowStats contains the main statistics of a flow */
class FlowStats {
    friend std::ostream& operator<<(std::ostream &, const FlowStats &);
    const unsigned long _id;
    const FlowId _flow_id;
    const struct timeval _first_ts; // Timestamp of the first packet
    struct timeval _last_ts; // Timestamp of the last packet
    // Indicates whether the flow has been marked as expired and cleaned up
    bool _expired_flag = false;
    unsigned long _pkt_count; // Total number of packet seen for this flow
    unsigned long _total_bytes; // Total number of bytes seen for this flow
#ifdef NETSEC_ADVANCED_FLOW_STATS
    std::vector<unsigned int> _pkt_count_per_second;
    std::vector<unsigned long> _total_bytes_per_second;
#endif

public:
    // Fast constructor that takes the information about the first packet
    FlowStats(unsigned long id, FlowId const& flow_id, struct timeval first_ts,
              unsigned long first_bytes);

    // Check if a flow is expired at the time provided
    bool is_expired(const struct timeval *at_time=NULL) const;

    // Return the id of the flow
    unsigned long get_id() const {
        return _id;
    }

    // Return FlowId of the flow
    const FlowId& get_flow_id() const {
        return _flow_id;
    }

    // Return the duration of the flow (so far) in seconds
    float get_flow_duration () const;

    // Mark the flow as expired (do cleanup if necessary)
    void mark_as_expired ();

    // Count a packet for the statistics of this flow
    void register_packet(const struct timeval *ts, unsigned long num_bytes);
};

std::ostream& operator<<(std::ostream &, const FlowStats &);

// Exception thrown when trying to register a packet for a flow that has been
// marked as expired
class FlowExpiredException : public std::runtime_error {
public:
    FlowExpiredException(const std::string& message)
        : std::runtime_error(message) {};
};


#endif // NETSEC_FLOWSTATS_H_
