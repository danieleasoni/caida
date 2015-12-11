#ifndef NETSEC_FLOWSTATS_TABLE_H_
#define NETSEC_FLOWSTATS_TABLE_H_

#include "FlowStats.h"

class FlowStatsTable {
    map<std::string,FlowStats *> _table;
    FlowStats *_last_change = NULL;
    std::vector<FlowStats *> _expired_flows;

    void collect_expired_flows();

public:
    FlowStatsTable();
    ~FlowStatsTable();

    FlowStats *get_last_change() {
        return _last_change;
    }

    void register_new_packet(std::string fivetuple, const struct timeval *ts,
                             unsigned long num_bytes);
    void erase_expired_flows();
}


#endif //NETSEC_FLOWSTATS_TABLE_H_

