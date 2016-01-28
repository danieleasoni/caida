from __future__ import print_function
import sys, os
import numpy as NP
from types import *
import time
import math
from collections import namedtuple

USAGE = "Usage: python histograms.py infile"

LIFETIME_COL = 1
PKT_COUNT_COL = 2
TOTAL_BYTES_COL =3
#BANDWIDTH_COL = 14

IGNORE_1_PKT_FLOWS = True
IGNORE_0_DURATION_FLOWS = True
IGNORE_LONG_FLOWS = True
MAX_FLOW_DURATION = 3000
IGNORE_LOW_BANDWIDTH_FLOWS = True
BANDWIDTH_IGNORING_THRESHOLD = 10

ALPHA_DATA_COST = 1
ALPHA_SLOWDOWN_COST = 1

EPS = NP.finfo(float).eps

def get_absolute_slowdown(data_point, cluster):
    new_duration_without_padding = (cluster.duration * data_point.total_data
                                    / cluster.total_data)
    return new_duration_without_padding - data_point.duration

class DataPoint(object):
    """
    A data point representing a flow, containing the duration and the total
    data transmitted. Additionally, the data point may be assigned to a
    cluster, in which case cluster_idx is set to the index of the cluster.
    """

    def __init__(self, duration, total_data, cluster_idx=None):
        self.duration = duration
        self.total_data = total_data
        self.cluster_idx = cluster_idx

    def bandwidth_fits_in_cluster(self, cluster):
        """
        Check if a data point's bandwidth fits into a cluster, i.e. if it is
        higher or equal than the cluster's bandwidth
        """
        return (self.duration * cluster.total_data
                <= cluster.duration * self.total_data)

    def fits_in_cluster(self, cluster):
        """
        A data point fits into a cluster if its total data is less or equal than
        the total data of the cluster, and if its bandwidth is higher or equal
        than the bandwidth of the cluster.
        """
        return (self.total_data <= cluster.total_data and
                self.bandwidth_fits_in_cluster(cluster))

    def get_assignment_cost(self, cluster):
        """
        Get the cost (combination of relative data cost and relative slowdown
        cost) of the assignment of the data point to the input cluster
        """
        data_cost = ((cluster.total_data - self.total_data)
                     / self.total_data)
        slowdown_cost = (get_absolute_slowdown(self, cluster)
                         / (self.duration + EPS))
        return (ALPHA_DATA_COST * data_cost + ALPHA_SLOWDOWN_COST * slowdown_cost)

#    def assign_data_point(self, cluster_list):
#        """
#        Assign the data point to the best cluster in the given cluster list.
#        """


class CostAccumulator(object):
    """
    Accumulator to store information about data points and to compute the
    total data cost and slowdown cost, and the entropy fraction
    """

    def __init__(self, cluster_list):
        self.cluster_list = cluster_list
        self.cluster_assignment_counts = [0] * len(cluster_list)
        self.tot_original_data = 0
        self.tot_padding_data = 0
        self.tot_original_duration = 0
        self.tot_duration_increase = 0
        self.unassignable_flows_count = 0
        self.flow_count = 0

    def add_data_point(self, data_point, count_times=1):
        """
        Consider a new data point, increasing the total counts for original and
        padding data, and for original duration and duration increase.
        """
        if count_times == 1:
            self.flow_count += 1 # Count original flows, not the splitted ones
        assignment_costs = [None] * len(self.cluster_list)
        # Get the costs of assigning the data point to the different clusters.
        # For clusters into which the point does not fit, None is stored.
        for idx, cluster in enumerate(self.cluster_list):
            if not data_point.fits_in_cluster(cluster):
                continue
            assignment_costs[idx] = data_point.get_assignment_cost(cluster)
        # Assign the data point to the best-fitting cluster. If the point fits
        # in no cluster, try splitting the flow into two flows with the same
        # bandwith but half the duration and half the total data.
        if assignment_costs != [None] * len(assignment_costs):
            data_point.cluster_idx = (
                    assignment_costs.index(min([x for x in assignment_costs
                                                if x is not None])))
        else:
            if count_times > 1 or any(map(data_point.bandwidth_fits_in_cluster,
                                      self.cluster_list)):
                # The data point doesn't fit in any cluster, split it into
                # two data point (two flows) and add both (recursive call),
                # then return.
                split_point = DataPoint(data_point.duration / float(2),
                                          data_point.total_data / float(2))
                self.add_data_point(split_point, count_times=count_times*2)
                # Consider the original data point as assigned to the cluster
                # to which the to splitted points were assigned
                data_point.cluster_idx = split_point.cluster_idx
#                # Increase the assignment count for the cluster to which the
#                # current data point was added. Increase the count only
#                # once per original data point
#                if not splitted:
#                    self.cluster_assignment_counts[data_point.cluster_idx] += 1
            else:
                # The data point cannot be assigned because its bandwidth is
                # too low. Add to the count of unassignable points and return.
                self.unassignable_flows_count += 1
            return

        # Add the information of the data point to the cost accumulators.
        self.tot_original_data += count_times * data_point.total_data
        self.tot_padding_data += count_times * (
                self.cluster_list[data_point.cluster_idx].total_data
                - data_point.total_data)
        self.tot_original_duration += count_times * data_point.duration
        self.tot_duration_increase += count_times * get_absolute_slowdown(
                data_point, self.cluster_list[data_point.cluster_idx])
        # Increase the assignment count for the cluster to which the current
        # data point was added
        # TODO Instead of adding 1, count_times could be added
        self.cluster_assignment_counts[data_point.cluster_idx] += 1

    def get_total_data_cost(self):
        if self.tot_original_data == 0:
            assert self.tot_padding_data == 0
            return 0
        return self.tot_padding_data / self.tot_original_data

    def get_total_slowdown_cost(self):
        if self.tot_original_duration == 0:
            assert self.tot_duration_increase == 0
            return 0
        return self.tot_duration_increase / self.tot_original_duration

    def get_unassignable_fraction(self):
        if self.flow_count == 0:
            return 0;
        return self.unassignable_flows_count / float(self.flow_count)

# FIXME: this works only if all the flows start at the same time..
def get_entropy_fraction(assigned_data_points):
    """
    Get the fraction of the maximum entropy in the ideal case given the cluster
    assignments over the maximum possible entropy achievable if all flows were in
    a single anonymity set.
    The entropy of an anonymity set (of a cluster) is computed as
        log_2(n!)     where n is the size of the cluster.
    This considers an adversary that can see all inputs and outputs, but for whom
    all the associations between inputs and outputs belonging to the same cluster
    are equiprobable. The possible permutations are n!, and the bits to represent
    any such permutation are log_2(n!).
    """
    cluster_sizes = [0] * len(CLUSTER_LIST)
    for data_point in assigned_data_points:
        if data_point.cluster_idx is not None:
            cluster_sizes[data_point.cluster_idx] += 1
    get_cluster_entropy = lambda x: math.log(math.factorial(x),2)
    total_entropy = sum(map(get_cluster_entropy, cluster_sizes))
    max_entropy = get_cluster_entropy(sum(cluster_sizes))
    return total_entropy/max_entropy

CLUSTER_LIST = [DataPoint(1,1000, None),
                #DataPoint(10, 500, None),
                DataPoint(11, 210, None),
                DataPoint(60, 100, None),
                DataPoint(60,10000, None)]

def _get_data_point_iterator_from_file(data_file):
    for line in data_file:
        columns = line.split()
        if IGNORE_1_PKT_FLOWS and int(columns[PKT_COUNT_COL]) < 2:
            continue
        if IGNORE_0_DURATION_FLOWS and float(columns[LIFETIME_COL]) <= 0:
            continue
        if (IGNORE_LONG_FLOWS and
                float(columns[LIFETIME_COL]) > MAX_FLOW_DURATION):
            continue
        if (IGNORE_LOW_BANDWIDTH_FLOWS and
            (int(columns[TOTAL_BYTES_COL])
             < BANDWIDTH_IGNORING_THRESHOLD * float(columns[LIFETIME_COL]))):
            continue
        yield DataPoint(float(columns[LIFETIME_COL]),
                        float(columns[TOTAL_BYTES_COL]))

def get_data_point_iterator():
    if len(sys.argv) < 2:
        print("reading from stdin..")
        for dp in _get_data_point_iterator_from_file(sys.stdin):
            yield dp
    else:
        try:
            for filename in sys.argv[1:]:
                data_file = open(filename, 'r')

                for dp in _get_data_point_iterator_from_file(data_file):
                    yield dp

                if data_file is not sys.stdin:
                    data_file.close()
        except IOError as e:
            print("Unable to open file", file=sys.stderr)
            print(str(e), file=sys.stderr)
            print(USAGE, file=sys.stderr)
            sys.exit(1)

def compute_and_print_costs(cluster_list=CLUSTER_LIST):
    cost_acc = CostAccumulator(cluster_list)
    for data_point in get_data_point_iterator():
        cost_acc.add_data_point(data_point)
    print("Total data cost: ", cost_acc.get_total_data_cost())
    print("Total slowdown cost: ", cost_acc.get_total_slowdown_cost())
    print("Unassignable fraction: ", cost_acc.get_unassignable_fraction())
    tot_assigned_flows = sum(cost_acc.cluster_assignment_counts)
    relative_assignment = [float(x)#/tot_assigned_flows
                           for x in cost_acc.cluster_assignment_counts]
    print("Cluster assignment counts:")
    for percent, cluster in zip(relative_assignment,
            [(c.duration, c.total_data) for c in cluster_list]):
        print(percent, cluster)

if __name__ == "__main__":
#    durations = [ [5],
#                  [10],
#                  [0.1, 1, 10, 100],
#                  [0.1, 100],
#                  [0.1, 0.5, 1, 5, 10, 50, 100],
#                  [0.1, 1, 10, 50, 100],
#                  [0.1, 1, 10, 33, 66, 100]
#                ]
#    datas = [ [10**3],
#              [10**4],
#              [10**5],
#              [10**3, 10**4],
#              [10**4, 10**5],
#              [10**3, 10**4, 10**5],
#              [10**4, 2 * 10**4],
#              [10**4, 2 * 10**4, 10**5],
#              [10**4, 10**5, 10**6]
#            ]
    durations = [[0.1], [1], [10], [0.1, 1], [1,10]]
    datas = [[10**4], [10**5], [10**4, 10**5]]
    for cluster_list in [[DataPoint(t, d)
                          for t in duration
                          for d in data]
                        for duration in durations
                        for data in datas]:
        print("#########################################")
        compute_and_print_costs(cluster_list)


