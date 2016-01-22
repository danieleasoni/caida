from __future__ import print_function
import sys, os
import numpy as NP
from types import *
import time
import math
from collections import namedtuple

USAGE = "Usage: python histograms.py infile"

LIFETIME_COL = 1
#PKT_COUNT_COL = 2
TOTAL_BYTES_COL =3
#BANDWIDTH_COL = 14

ALPHA_DATA_COST = 1
ALPHA_SLOWDOWNCOST = 1

EPS = NP.finfo(float).eps

#class DataPoint(object):
#    def __init__(self, duration, total_data):
#        self.duration = duration
#        self.total_data = total_data
#
#class AssignedPoint(DataPoint):
#    def __init__(self, duration, total_data, cluster_idx):
#        super(duration_total_data)
#        self.cluster_idx = cluster_idx

DataPoint = namedtuple("DataPoint", "duration total_data cluster_idx")

CLUSTER_LIST = [DataPoint(1,1000, None),
                DataPoint(10, 500, None),
                DataPoint(60,10000, None)]

def fits_in_cluster(data_point, cluster):
    """
    A data point fits into a cluster if its total data is less or equal than
    the total data of the cluster, and if its bandwidth is higher or equal than
    the bandwidth of the cluster.
    """
    return (data_point.total_data <= cluster.total_data and
            (data_point.duration * cluster.total_data
             <= cluster.duration * data_point.total_data))

def get_absolute_slowdown(data_point, cluster):
    new_duration_without_padding = (cluster.duration * data_point.total_data
                                    / cluster.total_data)
    return new_duration_without_padding - data_point.duration

def get_assignment_cost(data_point, cluster):
    """
    Get the cost (combination of relative data cost and relative slowdown cost)
    of the assignment of the input data point to the input cluster
    """
    data_cost = ((cluster.total_data - data_point.total_data)
                 / data_point.total_data)
    slowdown_cost = (get_absolute_slowdown(data_point, cluster)
                     / (data_point.duration + EPS))
    return ALPHA_DATA_COST * data_cost + ALPHA_SLOWDOWN_COST * slowdown_cost

def get_total_data_cost(assigned_data_points, cluster_list):
    tot_original_data = 0
    tot_padding_data = 0
    for dp in assigned_data_points:
        tot_original_data += dp.total_data
        tot_padding_data += (cluster_list[dp.cluster_idx].total_data
                            - dp.total_data)
    return tot_padding_data / tot_original_data

def get_total_slowdown_cost(assigned_data_points, cluster_list):
    tot_original_duration = 0
    tot_duration_increase = 0
    for dp in assigned_data_points:
        tot_original_duration += dp.duration
        tot_duration_increase += get_absolute_slowdown(dp,
                cluster_list[dp.cluster_idx])
    return tot_duration_increase / tot_original_duration

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
    get_cluster_entropy = lambda x: log(factorial(x),2)
    total_entropy = sum(map(get_cluster_entropy, cluster_sizes))
    max_entropy = get_cluster_entropy(sum(cluster_sizes))
    return total_entropy/max_entropy

def assign_data_points(to_assign):
    assigned = []
    unassignable = []


if __name__ == "__main__":
#    if not os.path.exists(OUTDIR):
#        os.makedirs(OUTDIR)
    if len(sys.argv) < 2:
        print("reading from stdin..")
        data_file = sys.stdin
    else:
        try:
            data_file = open(sys.argv[1], 'r')
        except IOError as e:
            print("Unable to open file", file=sys.stderr)
            print(str(e), file=sys.stderr)
            print(USAGE, file=sys.stderr)
            sys.exit(1)

    # Load data from file into an array
    data_array = NP.loadtxt(data_file)
    data_points_to_assign = [DataPoint(data_array[i,LIFETIME_COL],
                                       data_array[i,TOTAL_BYTES_COL])
                             for i in xrange(data_array.shape[0])]

    if data_file is not sys.stdin:
        data_file.close()

