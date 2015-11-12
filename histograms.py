from __future__ import print_function
import sys
import matplotlib.pyplot as plt
import numpy as NP
from types import *
import time

USAGE = "Usage: python histograms.py infile"

def get_new_filename(base, ext=""):
    return str(base) + "_" + time.strftime("%Y%m%d-%H%M%S") + str(ext)

def plot_histogram(data_file, delimiter=None, col_num=0):
    assert type(col_num) is IntType, "col_num is not an integer: %r" % col_num
    v = NP.loadtxt(data_file, delimiter=delimiter, usecols=(col_num,))
    fig = plt.hist(v)
    plt.savefig(get_new_filename("figs/distribution", "eps"))
    plt.savefig(get_new_filename("figs/distribution", "pdf"))
    fig = plt.hist(v, cumulative=True, histtype='step')
    plt.savefig(get_new_filename("figs/distribution", "eps"))
    plt.savefig(get_new_filename("figs/distribution", "pdf"))
    plt.show()

COL_NUM=3

if __name__ == "__main__":
    if len(sys.argv) < 2:
        plot_histogram(sys.stdin, col_num=COL_NUM)
    else:
        try:
            with open(sys.argv[1], 'r') as data_file:
                plot_histogram(data_file, col_num=COL_NUM)
        except IOError as e:
            print("Unable to open file " + sys.argv[1], file=sys.stderr)
            print(USAGE, file=sys.stderr)
            sys.exit(1)

