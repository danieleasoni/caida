#include "FlowStats.h"

#include <iostream>
#include <boost/array.hpp>
#include <boost/accumulators/accumulators.hpp>
#include <boost/accumulators/statistics.hpp>

#include "constants.h"
#include "utils.h"

using namespace std;
using namespace boost::accumulators;
using namespace boost::accumulators::extract;

typedef accumulator_set<double, stats<tag::min, tag::max, tag::mean,
        tag::median, tag::variance> > stats_acc_t;
typedef accumulator_set<double, stats<tag::extended_p_square> > quantile_acc_t;

FlowStats::FlowStats(unsigned long id, struct timeval first_ts,
                     unsigned long first_bytes)
        : _id(id), _first_ts(first_ts), _last_ts(first_ts), _pkt_count(1),
          _total_bytes(first_bytes)
#ifdef NETSEC_ADVANCED_FLOW_STATS
        , _pkt_count_per_second (NSConstants::MaxFlowLifetime, 0),
          _total_bytes_per_second (NSConstants::MaxFlowLifetime, 0) {
    _pkt_count_per_second.at(0) += 1;
    _total_bytes_per_second.at(0) += first_bytes;
}
#else
{}
#endif

bool FlowStats::is_expired(const struct timeval *at_time) const {
    struct timeval time_diff_from_first;
    struct timeval time_diff_from_last;
    if (_expired_flag) return true;
    if (at_time == NULL) at_time = &_last_ts;
    timeval_sub(&_first_ts, at_time, &time_diff_from_first);
    timeval_sub(&_last_ts, at_time, &time_diff_from_last);
    return (time_diff_from_first.tv_sec >= NSConstants::MaxFlowLifetime)
           || (time_diff_from_last.tv_sec >= NSConstants::MaxFlowInactiveTime);
}

float FlowStats::get_flow_duration() const {
    return timeval_to_seconds(&_last_ts) - timeval_to_seconds(&_first_ts);
}

void FlowStats::mark_as_expired() {
#ifdef NETSEC_ADVANCED_FLOW_STATS
    if (_expired_flag) return;
    while (_pkt_count_per_second.back() == 0) {
        _pkt_count_per_second.pop_back();
    }
    while (_total_bytes_per_second.back() == 0) {
        _total_bytes_per_second.pop_back();
    }
#endif
    _expired_flag = true;
}

void FlowStats::register_packet(const struct timeval *ts,
                                unsigned long num_bytes) {
    if (_expired_flag) {
        throw FlowExpiredException("Cannot register packet on expired flow");
    }
    _last_ts = *ts;
    _pkt_count += 1;
    _total_bytes += num_bytes;
    // Increase packet count and byte count for the current second
    struct timeval time_diff;
    timeval_sub(&_first_ts, ts, &time_diff);
#ifdef NETSEC_ADVANCED_FLOW_STATS
    _pkt_count_per_second.at(time_diff.tv_sec) += 1;
    _total_bytes_per_second.at(time_diff.tv_sec) += num_bytes;
#endif
}

std::ostream& operator<<(std::ostream &strm, const FlowStats &fs) {
    const char * sep = NSConstants::FIELD_SEPARATOR;
    strm << fs._id << sep << fs.get_flow_duration() << sep;
    strm << fs._pkt_count << sep << fs._total_bytes << sep;
#ifdef NETSEC_ADVANCED_FLOW_STATS
    // Compute statistics
    stats_acc_t pkt_stats_acc;
    stats_acc_t byte_stats_acc;
    boost::array<double, 5> probs = {0.1, 0.25, 0.5, 0.75, 0.9};
    quantile_acc_t pkt_quantile_acc (tag::extended_p_square::probabilities = probs);
    quantile_acc_t byte_quantile_acc (tag::extended_p_square::probabilities = probs);
    pkt_stats_acc = for_each(fs._pkt_count_per_second.begin(),
                             fs._pkt_count_per_second.end(), pkt_stats_acc);
    byte_stats_acc = for_each(fs._total_bytes_per_second.begin(),
                              fs._total_bytes_per_second.end(), byte_stats_acc);
    pkt_quantile_acc = for_each(fs._pkt_count_per_second.begin(),
                                fs._pkt_count_per_second.end(), pkt_quantile_acc);
    byte_quantile_acc = for_each(fs._total_bytes_per_second.begin(),
                                 fs._total_bytes_per_second.end(),
                                 byte_quantile_acc);
    // Print packet statistics
    strm << extract::mean(pkt_stats_acc) << sep << sqrt(extract::variance(pkt_stats_acc)) << sep;
    strm << extract::min(pkt_stats_acc) << sep << extract::max(pkt_stats_acc) << sep;
    strm << extract::median(pkt_stats_acc) << sep;
    for (int i=0; i < probs.size(); ++i) {
        strm << extended_p_square(pkt_quantile_acc)[i] << sep;
    }
    // Print bytes statistics
    strm << extract::mean(byte_stats_acc) << sep << sqrt(extract::variance(byte_stats_acc)) << sep;
    strm << extract::min(byte_stats_acc) << sep << extract::max(byte_stats_acc) << sep;
    strm << extract::median(byte_stats_acc) << sep;
    for (int i=0; i < probs.size(); ++i) {
        strm << extended_p_square(byte_quantile_acc)[i] << sep;
    }
#endif
    return strm;
}

