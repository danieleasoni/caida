from __future__ import print_function
import sys, os
import matplotlib.pyplot as plt
import numpy as NP
from types import *
import time

USAGE = "Usage: python histograms.py infile"

BUCKETS = [0,5,10,15,20,25,30,35,40,45,50]

def get_new_filename(base, ext=""):
    return str(base) + "_" + time.strftime("%Y%m%d-%H%M%S") + str(ext)

def plot_histogram(data_file, delimiter=None, converters=None, col_num=0):
    assert type(col_num) is IntType, "col_num is not an integer: %r" % col_num
    v = NP.loadtxt(data_file, delimiter=delimiter, converters=converters, usecols=(col_num,))
    fig = plt.hist(v, bins=BUCKETS)
    if not os.path.exists("figs"):
        os.makedirs("figs")
    plt.savefig(get_new_filename("figs/distribution", ".eps"))
    plt.savefig(get_new_filename("figs/distribution", ".pdf"))
    fig = plt.hist(v, cumulative=True, histtype='step', bins=BUCKETS)
    plt.savefig(get_new_filename("figs/distribution", ".eps"))
    plt.savefig(get_new_filename("figs/distribution", ".pdf"))

COL_NUM=3

if __name__ == "__main__":
    converters = {COL_NUM : lambda s: float(s if s != 'inf' else -1)}
    if len(sys.argv) < 2:
        plot_histogram(sys.stdin, converters=converters, col_num=COL_NUM)
    else:
        try:
            with open(sys.argv[1], 'r') as data_file:
                plot_histogram(data_file, converters=converters, col_num=COL_NUM)
        except IOError as e:
            print("Unable to open file", file=sys.stderr)
            print(str(e), file=sys.stderr)
            print(USAGE, file=sys.stderr)
            sys.exit(1)

