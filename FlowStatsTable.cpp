
#include "FlowStatsTable.h"

#include <memory> // For std::shared_ptr
#include <utility> // For std::move
#include <cassert>

#include "utils.h"

using namespace std;

typedef map<string,shared_ptr<FlowStats> >::iterator map_it_type;

FlowStatsTable::FlowStatsTable() {}

unsigned long FlowStatsTable::register_new_packet(const FlowId& flow_id,
                                                  const struct timeval *ts,
                                                  unsigned long num_bytes) {
    pair<map_it_type,bool> emplace_result;
    const string fivetuple = flow_id.get_fivetuple_str();

    auto flow_stat = _table.find(fivetuple);
    if (flow_stat == _table.end()) {// The packet belongs to a new flow
        shared_ptr<FlowStats> flow_stats_ptr(
                new FlowStats(_id_counter, flow_id, *ts, num_bytes));
        emplace_result = _table.emplace(fivetuple, flow_stats_ptr);
        assert (emplace_result.second); // The key must be newly inserted
        flow_stat = emplace_result.first; // Get iterator at new element
        _id_counter++; // Increase the flow id counter
    } else if (flow_stat->second->is_expired(ts)) {
        flow_stat->second->mark_as_expired();
        _expired_flows.push_back(flow_stat->second);
        _table.erase(flow_stat);
        // Recursive call after the expired flow has been removed.
        // Could be made more efficient by repeating the code above, or by
        // doing some additional checks.
        return register_new_packet(flow_id, ts, num_bytes);
    } else {
       flow_stat->second->register_packet(ts, num_bytes);
    }

    // Keep track of the most recent timestamp
    if (timeval_to_seconds(ts) > timeval_to_seconds(&_last_change_ts)) {
        _last_change_ts = *ts;
    }
    _changed_after_last_expiration = true;
    return flow_stat->second->get_id();
}

void FlowStatsTable::erase_expired_flows() {
    _expired_flows.clear();
}

int FlowStatsTable::collect_expired_flows(const struct timeval *at_time) {
    if (at_time == NULL and !_changed_after_last_expiration) {
        return _expired_flows.size();
    }
    if (at_time == NULL and
            !(_last_change_ts.tv_sec == 0 and _last_change_ts.tv_usec == 0)) {
        at_time = &_last_change_ts;
    }
    for (auto it = _table.begin(); it != _table.end(); /*in-code*/) {
        if (it->second->is_expired(at_time)) {
            it->second->mark_as_expired();
            _expired_flows.push_back(it->second);
            _table.erase(it++);
        } else {
            ++it;
        }
    }
    _changed_after_last_expiration = false;
    return _expired_flows.size();
}

std::ostream& FlowStatsTable::print_expired_flows(std::ostream &strm) {
    for (auto it = _expired_flows.begin(); it != _expired_flows.end(); ++it) {
        strm << **it << endl;
    }
    return strm;
}

std::ostream& FlowStatsTable::print_all_flows(std::ostream &strm) {
    for (auto it = _table.begin(); it != _table.end(); ++it) {
        strm << *(it->second) << endl;
    }
    return strm;
}
