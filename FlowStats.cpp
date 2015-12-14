#include "FlowStats.h"

#include <iostream>

#include "constants.h"
#include "utils.h"

FlowStats::FlowStats(unsigned long id, struct timeval first_ts,
                     unsigned long first_bytes)
        : _id(id), _first_ts(first_ts) {
    _last_ts = first_ts;
    _pkt_count = 1;
    _total_bytes = first_bytes;
}


bool FlowStats::is_expired(const struct timeval *at_time) const {
    struct timeval time_diff;
    if (at_time == NULL) at_time = &_last_ts;
    timeval_sub(at_time, &_first_ts, &time_diff);
    return (time_diff.tv_sec >= NSConstants::MaxFlowLifetime);
}

float FlowStats::get_flow_duration() const {
    return timeval_to_seconds(&_last_ts) - timeval_to_seconds(&_first_ts);
}

void FlowStats::register_packet(const struct timeval *ts,
                                unsigned long num_bytes) {
    _last_ts = *ts;
    _pkt_count += 1;
    _total_bytes += num_bytes;
}

std::ostream& operator<<(std::ostream &strm, const FlowStats &fs) {
    const char * sep = NSConstants::FIELD_SEPARATOR;
    strm << fs._id << sep << fs.get_flow_duration() << sep;
    strm << fs._pkt_count << sep << fs._total_bytes;
    return strm;
}

