from __future__ import print_function
import sys, os
from collections import namedtuple
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as NP
from types import *
import time

from plot_flow_stats import get_new_filename

USAGE = "Usage: python eval_classes_cost.py infile"

OUTDIR = "figs"

#LIFETIME_COL = 1
#PKT_COUNT_COL = 2
#TOTAL_BYTES_COL = 3
LIFETIME_COL = 2
PKT_COUNT_COL = 3
TOTAL_BYTES_COL = 4
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

    def bandwidth(self):
        """
        Returns the average bandwidth of the flow.
        This function will raise an exception if the duration of the flow
        is 0.
        """
        return self.total_data / self.duration

    def fits_in_cluster(self, cluster):
        """
        A data point fits into a cluster if its total data is less or equal than
        the total data of the cluster, and if its bandwidth is higher or equal
        than the bandwidth of the cluster.
        """
        return (self.total_data <= cluster.total_data and
                (self.duration * cluster.total_data
                 <= cluster.duration * self.total_data))

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
        self.additional_set_ups = 0
        self.flow_count = 0

    def add_data_point(self, data_point, count_times=1):
        """
        Consider a new data point, increasing the total counts for original and
        padding data, and for original duration and duration increase.
        """
        # Get the costs of assigning the data point to the different clusters.
        # For clusters into which the point does not fit, None is stored.
        assignment_costs = [None] * len(self.cluster_list)
        for idx, cluster in enumerate(self.cluster_list):
            if not data_point.fits_in_cluster(cluster):
                continue
            assignment_costs[idx] = data_point.get_assignment_cost(cluster)

        # Assign the data point to the best-fitting cluster (if any)
        # else split the flow into multiple ones
        if assignment_costs != [None] * len(assignment_costs):
            data_point.cluster_idx = (
                    assignment_costs.index(min([x for x in assignment_costs
                                                if x is not None])))
            # Add the information of the data point to the cost accumulators.
            self.tot_original_data += count_times * data_point.total_data
            self.tot_padding_data += count_times * (
                    self.cluster_list[data_point.cluster_idx].total_data
                    - data_point.total_data)
            self.tot_original_duration += count_times * data_point.duration
            self.tot_duration_increase += count_times * get_absolute_slowdown(
                    data_point, self.cluster_list[data_point.cluster_idx])
            # Increase the flow counts (total and per cluster)
            self.flow_count += count_times
            self.cluster_assignment_counts[
                    data_point.cluster_idx] += count_times
        else: # No fitting cluster, flow has to be split (or is unassignable)
            # Find the best cluster in terms of bandwidth
            cluster_bandwidth_list = map(lambda x: x.bandwidth(),
                                         self.cluster_list)
            if data_point.duration == 0:
                target_cluster_idx = cluster_bandwidth_list.index(
                        min(cluster_bandwidth_list))
            else:
                bw_differences = map(
                        lambda x: data_point.bandwidth() - x.bandwidth(),
                        self.cluster_list)
                if all([x<0 for x in bw_differences]):
                    # The data point cannot be assigned because its bandwidth is
                    # too low. Add to the count of unassignable points
                    # and return.
                    self.unassignable_flows_count += 1
                    self.flow_count += 1
                    return
                min_bw_diff = min(filter(lambda x: x>=0, bw_differences))
                indices_and_tot_data = [(i, self.cluster_list[i].total_data)
                                        for i, x in enumerate(bw_differences)
                                        if x == min_bw_diff]
                target_cluster_idx = [x[0] for x in indices_and_tot_data
                    if x[1] == max([y[1] for y in indices_and_tot_data])][0]
            target_cluster = self.cluster_list[target_cluster_idx]

            # Split flows into multiple points (try to fit as many as possible
            # into the cluster with the closest bandwidth), add them
            # recursively
            num_fits = data_point.total_data // target_cluster.total_data
            reduced_lifetime = (data_point.duration *
                    target_cluster.total_data / data_point.total_data)
            new_point = DataPoint(reduced_lifetime, target_cluster.total_data)
            self.add_data_point(new_point, count_times=num_fits)
            self.additional_set_ups += num_fits

            # Add the remaining data as another data point
            remaining_data = data_point.total_data % target_cluster.total_data
            if remaining_data > 0:
                reduced_lifetime = (data_point.duration *
                        remaining_data / data_point.total_data)
                self.add_data_point(DataPoint(reduced_lifetime, remaining_data))

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
        return (self.unassignable_flows_count /
                float(self.flow_count - self.additional_set_ups))

    def get_additional_setup_fraction(self):
        if self.flow_count == 0:
            return 0;
        return self.additional_set_ups / float(self.flow_count)


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
    assert len(cluster_list) > 0
    for cluster in cluster_list:
        assert cluster.duration > 0
    cost_acc = CostAccumulator(cluster_list)
    for data_point in get_data_point_iterator():
        cost_acc.add_data_point(data_point)
    print("Total data cost: ", cost_acc.get_total_data_cost())
    print("Total slowdown cost: ", cost_acc.get_total_slowdown_cost())
    print("Unassignable fraction: ", cost_acc.get_unassignable_fraction())
    tot_assigned_flows = sum(cost_acc.cluster_assignment_counts)
    relative_assignment = [float(x)#/tot_assigned_flows
                           for x in cost_acc.cluster_assignment_counts]
    print("Additional setup fraction: ",
          cost_acc.get_additional_setup_fraction())
    print("Cluster assignment counts:")
    for percent, cluster in zip(relative_assignment,
            [(c.duration, c.total_data) for c in cluster_list]):
        print(percent, cluster)

def plot_flowlet_costs(flowlet_data, flowlet_duration=100,
        sequential=[1,10,100], parallel=[1,10,100],
        xlabel='Amount of data sent by 100s flowlet', ylabel='data_cost',
        basefilename="costs_vs_flowlet_rate"):
    assert len(sequential) > 0 and len(parallel) > 0
    accumulators = []
    for data in flowlet_data:
        acc = CostAccumulator([DataPoint(flowlet_duration*s, data*p)
                               for s in sequential for p in parallel])
        accumulators.append(acc)
    for data_point in get_data_point_iterator():
        for acc in accumulators:
            acc.add_data_point(data_point)
    data_costs = [acc.get_total_data_cost() for acc in accumulators]
    slowdown_costs = [acc.get_total_slowdown_cost() for acc in accumulators]
    unassignable = [acc.get_unassignable_fraction() for acc in accumulators]
    filename = get_new_filename(os.path.join(OUTDIR, basefilename), ".eps")
    fig = plt.plot(flowlet_data, data_costs)
    ax = plt.gca()
    #PCM=ax.get_children()[2]
    plt.xlabel(xlabel, fontsize=16)
    plt.ylabel(ylabel, fontsize=16)
    ax.set_yscale('log')
    ax.set_xscale('log')
    plt.savefig(filename)
    plt.close()


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
    #durations = [[1, 10, 100], [1, 10, 30, 60, 100], [1, 3, 6, 10, 30, 60, 100]]

    flowlet_data = NP.logspace(4,8,num=40)
    plot_flowlet_costs(flowlet_data)

#    durations = [[10, 10, 10, 100, 100, 100, 1000, 1000]] #[[0.1, 1, 10, 30, 60, 100]]
#    datas = [[10**4, 10**5, 10**6, 10**5, 10**6, 10**7, 10**6, 10**7],
#             #[10**6, 2*10**6, 3*10**6, 4*10**6, 5*10**6, 10*10**6],
#            ]#, [10**4, 10**5], [10**4, 10**5, 10**6]]
#    for cluster_list in [[DataPoint(t, d)
#                          for t, d in zip(duration, data)]
#                          #for t in duration
#                          #for d in data]
#                        for duration in durations
#                        for data in datas]:
#        print("#########################################")
#        cluster_list = filter(lambda x: x.bandwidth()<900000, cluster_list)
#        compute_and_print_costs(cluster_list)


