
LIBS=-lpcap

all: get_flow_stats

get_flow_stats: get_flow_stats.cpp utils.o
	g++ $^ -o $@ $(LIBS) -std=c++11

FlowStats.o: FlowStats.cpp FlowStats.h
	g++ -c $< -o $@ #-std=c++11

utils.o: utils.cpp utils.h
	g++ -c $< -o $@ -std=c++11

clean:
	rm get_flow_stats utils.o FlowStats.o

.PHONY: clean all
