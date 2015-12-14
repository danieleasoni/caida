#ifndef NETSEC_FLOWSTATS_TABLE_H_
#define NETSEC_FLOWSTATS_TABLE_H_

#include <ctime>
#include <map>
#include <memory>
#include <ostream>
#include <vector>

#include "FlowStats.h"

// FlowStatsTable keeps track of flow statistics: it registers new packets,
// considering them for the stats of the flow those packets belong to, and it
// expires old flows.
class FlowStatsTable {
    // Underlying map containing the flow stats for all flows.
    // Flows are identified through a string containing the flow's fivetuple.
    std::map<std::string,std::shared_ptr<FlowStats> > _table;
    struct timeval _last_change_ts = {0, 0};
    std::vector<std::shared_ptr<FlowStats> > _expired_flows;
    // Counter to incrementally generate the flow ids
    unsigned long _id_counter = 0;
    // Flag which indicates whether any new packet/flow has been considered
    // after the last time collect_expired_flows was called
    bool _changed_after_last_expiration = false;

public:
    FlowStatsTable();

    const struct timeval& get_last_change_ts() {
        return _last_change_ts;
    }

    // Add a new packet to the statistics of the flow it belongs to.
    void register_new_packet(const std::string fivetuple,
                             const struct timeval *ts,
                             unsigned long num_bytes);
    // Clean up all expired flows
    void erase_expired_flows();

    // Check all flows to find the expired ones, and return the number of all
    // currently expired flows.
    // If a pointer to a timeval is provided in at_time, this will be used
    // as current time to determine whether a flow is expired or not.
    int collect_expired_flows(const struct timeval *at_time=NULL);

    std::ostream& print_expired_flows(std::ostream &strm);

    std::ostream& print_all_flows(std::ostream &strm);

};


#endif //NETSEC_FLOWSTATS_TABLE_H_

