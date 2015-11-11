
LIBS=-lpcap

all: get_flows get_flow_stats fast_extract

get_flows: get_flows.cpp
	g++ $< -o $@ $(LIBS) -std=c++11

get_flow_stats: get_flow_stats.cpp
	g++ $< -o $@ $(LIBS) -std=c++11

fast_extract: fast_extract.cpp
	g++ $< -o $@ $(LIBS) -std=c++11

clean:
	rm get_flows get_flow_stats fast_extract

.PHONY: clean all
