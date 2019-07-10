# TODO: Every time a figure is plotted, a corresponding log file should be
# created, containing the command used to create the figure, and the current git
# commit number.

FLOW_STATS_FILES=data_output/flow_stats/equinix-chicago.dirA.20150219-13{10..59}00.UTC.expired_flows

# Plot cost vs flowlet size
cat ${FLOW_STATS_FILES} | \
    awk ' $3 != 0 { print $0 } ' | \
    python "all_all_2015_dirA" eval_classes_cost.py

cat ${FLOW_STATS_FILES} | \
    awk ' $3 != 0 { print $0 } ' | \
    python "all_all_2015_dirA" eval_classes_cost.py
