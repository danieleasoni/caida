
LIBS=-lpcap

get_flows: get_flows.cpp
	g++ $< -o $@ $(LIBS) -std=c++11

clean:
	rm get_flows

.PHONY: clean
