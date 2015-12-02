
LIBS=-lpcap

all: get_flow_stats

get_flow_stats: get_flow_stats.cpp daniele_utils.o
	g++ $^ -o $@ $(LIBS) -std=c++11

daniele_utils.o: daniele_utils.cpp daniele_utils.h
	g++ -c $< -o $@ -std=c++11

clean:
	rm get_flow_stats daniele_utils.o

.PHONY: clean all
