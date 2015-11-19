from __future__ import print_function
import sys, os
import matplotlib.pyplot as plt
import numpy as NP
from types import *
import time

USAGE = "Usage: python histograms.py infile"
OUTDIR = "figs"
# Use the converters if columns contain inf values (1 pkt flows)
# Currently not used, assuming that flows with 1 pkt have been removed
CONVERTERS = {3 : lambda s: float(s if s != 'inf' else -1),
              4 : lambda s: float(s if s != 'inf' else -1)}

BANDWIDTH_PPS_BINS = range(0, 51, 5)

def get_new_filename(base, ext=""):
    base_time = str(base) + "_" + time.strftime("%Y%m%d-%H%M%S")
    current_base = base_time
    counter = 1
    while os.path.exists(current_base + ext):
        current_base = base_time + "_" + str(counter)
        counter += 1
    return current_base + ext

def get_column_data(data_file, delimiter=None, converters=None, col_num=0):
    assert type(col_num) is IntType, "col_num is not an integer: %r" % col_num
    return NP.loadtxt(data_file, delimiter=delimiter, converters=converters, usecols=(col_num,))

def generate_hist_and_save(x, filename, generate_pdf=False, **kwargs):
    fig = plt.hist(x, **kwargs)
    plt.savefig(filename)
    if generate_pdf:
        plt.savefig(os.path.splitext(filename)[0] + ".pdf")
    plt.close()
#    plt.hist(x, histtype='step', bins=BUCKETS)
#    plt.savefig(get_new_filename("figs/distribution", ".eps"))
#    plt.savefig(get_new_filename("figs/distribution", ".pdf"))
#    plt.hist(x, histtype='step', normed=True, cumulative=True, bins=BUCKETS)
#    plt.savefig(get_new_filename("figs/distribution", ".eps"))
#    plt.savefig(get_new_filename("figs/distribution", ".pdf"))

def generate_bandwidth_pps_histograms(data_file):
    x = get_column_data(data_file, col_num=3)
    filename = get_new_filename(os.path.join(OUTDIR, "bwidth_pps"), ".eps")
    generate_hist_and_save(x, filename, bins=BANDWIDTH_PPS_BINS)
    filename = get_new_filename(os.path.join(OUTDIR, "bwidth_pps_cumul"), ".eps")
    generate_hist_and_save(x, filename, bins=BANDWIDTH_PPS_BINS,
                           cumulative=True, histtype='step', normed=True)

if __name__ == "__main__":
    if not os.path.exists(OUTDIR):
        os.makedirs(OUTDIR)
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

    # Bandwidth in packets-per-second histogram
    generate_bandwidth_pps_histograms(data_file)

    if data_file is not sys.stdin:
        data_file.close()


