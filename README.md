CAIDA Traces Flow Extraction
============================

C++ code to process the pcap of CAIDA and obtain flow information.

When run, the code by default outputs both a list of single packets with
timestamps (enhanced with unique flow identifiers), as well as a list of flows
each with its ID, the starting time and ending time, the total amount of bytes,
and more statistical information about the flow.

Regarding flows, these are defined based on the five-tuple (source IP,
destination IP, source port, destination port, and protocol). For packets that
are neither TCP nor UDP, source and destination port are ignored (set to zero).
Flows are considered expired if no packet is seen for a certain amount of
seconds (`NSConstants::MaxFlowInactiveTime`), or if a maximum lifetime has been
exceeded (`NSConstants::MaxFlowLifetime`, which by default is set to one hour in
the file [constants.h](/constants.h), which means that flows are never expired
since CAIDA traces are one hour long).

Some scripts that may be useful to bootstrap the process:
* [download.txt](/download.txt) This file contains information about how to
  download the CAIDA traces
* [unzip_traces.sh](unzip_traces.sh) Simple script to unzip all traces

The main files for extracting packet and flow information are the following:
* [requirements.txt](/requirements.txt) Lists the requirements to build the C++
  code, go through this before starting to use the code.
* [Makefile](/Makefile) Builds the C++ code.
* [constants.h](/constants.h) Contains some global parameters and constants.
* [get_flow_stats.cpp](/get_flow_stats.cpp) contains the `main()` function, and
  to check out what the code does you should start here. 
* [FlowStatsTable.h](/FlowStatsTable.h) and
  [FlowStatsTable.cpp](/FlowStatsTable.cpp) define the `FlowStatsTable` class,
  which is a map that stores all flow stats (`FlowStats` class) for the flows
  that have been seen. Its method `FlowStatsTable::register_new_packet` also
  decides when a certain flow is considered to be expired.
* [FlowStats.h](/FlowStats.h) and [FlowStats.cpp](/FlowStats.cpp) define the
  `FlowStats` class which represents a single flow. A flow can be updated by
  calling method `FlowStats::register_packet`, which updates the statistics of the
  flow according to the new packet. An important part of this is also the print
  function, which is used to print out the stats of a flow once it has expired: in
  this function, the more advanced stats are computed.
* [utils.h](/utils.h) and [utils.cpp](/utils.cpp) defines some utility functions
  to manage timestamps and files

One important thing about stats computation: the more advanced stuff that is
done in [FlowStats.cpp](/FlowStats.cpp) can take more time and memory, so it is
recommended to comment that part out when it is not needed. (At some point this
should be made configurable by a parameter.)

The python scripts are specific for a privacy project.
