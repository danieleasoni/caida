#include "FlowStats.h"

#include <iostream>
#include <boost/accumulators/accumulators.hpp>
#include <boost/accumulators/statistics.hpp>

#include "constants.h"
#include "utils.h"

using namespace std;
using namespace boost::accumulators;
using namespace boost::accumulators::extract;

typedef accumulator_set<double, stats<tag::min, tag::max, tag::mean,
        tag::median, tag::variance> > stats_acc_t;
//typedef accumulator_set<double, stats<tag::extended_p_square_quantile> >
//    quantile_acc_t;

FlowStats::FlowStats(unsigned long id, struct timeval first_ts,
                     unsigned long first_bytes)
        : _id(id), _first_ts(first_ts), _last_ts(first_ts), _pkt_count(1),
          _total_bytes(first_bytes),
          _pkt_count_per_second (NSConstants::MaxFlowLifetime, 0),
          _total_bytes_per_second (NSConstants::MaxFlowLifetime, 0) {
    _pkt_count_per_second.at(0) += 1;
    _total_bytes_per_second.at(0) += first_bytes;
}

bool FlowStats::is_expired(const struct timeval *at_time) const {
    struct timeval time_diff;
    if (at_time == NULL) at_time = &_last_ts;
    timeval_sub(&_first_ts, at_time, &time_diff);
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
    // Increase packet count and byte count for the current second
    struct timeval time_diff;
    timeval_sub(&_first_ts, ts, &time_diff);
    _pkt_count_per_second.at(time_diff.tv_sec) += 1;
    _total_bytes_per_second.at(time_diff.tv_sec) += num_bytes;
}

std::ostream& operator<<(std::ostream &strm, const FlowStats &fs) {
    const char * sep = NSConstants::FIELD_SEPARATOR;
    strm << fs._id << sep << fs.get_flow_duration() << sep;
    strm << fs._pkt_count << sep << fs._total_bytes << sep;
    // Compute and print statistics
    stats_acc_t pkt_stats_acc;
    stats_acc_t byte_stats_acc;
//    boost::array<double> probs = {0.1, 0.25, 0.5, 0.75, 0.9};
//    quantile_acc_t pkt_quantile_acc (extended_p_square_probabilities = probs);
//    quantile_acc_t byte_quantile_acc (extended_p_square_probabilities = probs);
    pkt_stats_acc = for_each(fs._pkt_count_per_second.begin(),
                             fs._pkt_count_per_second.end(), pkt_stats_acc);
    byte_stats_acc = for_each(fs._total_bytes_per_second.begin(),
                              fs._total_bytes_per_second.end(), byte_stats_acc);
//    pkt_quantile_acc = for_each(fs._pkt_count_per_second.begin(),
//                                fs._pkt_count_per_second.end(), pkt_stats_acc);
//    byte_quantile_acc = for_each(fs._total_bytes_per_second.begin(),
//                                 fs._total_bytes_per_second.end(),
//                                 byte_stats_acc);
    strm << extract::mean(pkt_stats_acc) << sep << sqrt(extract::variance(pkt_stats_acc)) << sep;
    strm << extract::min(pkt_stats_acc) << sep << extract::max(pkt_stats_acc) << sep;
    strm << extract::median(pkt_stats_acc) << sep;
    strm << extract::mean(byte_stats_acc) << sep << sqrt(extract::variance(byte_stats_acc)) << sep;
    strm << extract::min(byte_stats_acc) << sep << extract::max(byte_stats_acc) << sep;
    strm << extract::median(byte_stats_acc);
    return strm;
}

