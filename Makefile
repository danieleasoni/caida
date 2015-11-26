
LIBS=-lpcap

all: get_flow_stats

get_flow_stats: get_flow_stats.cpp
	g++ $< -o $@ $(LIBS) -std=c++11

clean:
	rm get_flow_stats

.PHONY: clean all
