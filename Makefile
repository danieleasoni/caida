
LIBS=-lpcap -lboost_system -lboost_filesystem

all: get_flow_stats

get_flow_stats: get_flow_stats.cpp utils.o FlowStats.o FlowStatsTable.o
	g++ $^ -o $@ $(LIBS) -std=c++11

FlowStats.o: FlowStats.cpp FlowStats.h constants.h
	g++ -c $< -o $@ -std=c++11

FlowStatsTable.o: FlowStatsTable.cpp FlowStatsTable.h FlowStats.h
	g++ -c $< -o $@ -std=c++11

utils.o: utils.cpp utils.h
	g++ -c $< -o $@ -std=c++11

clean:
	rm get_flow_stats utils.o FlowStats.o FlowStatsTable.o

.PHONY: clean all
