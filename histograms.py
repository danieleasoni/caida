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

BANDWIDTH_PPS_BINS = NP.linspace(0, 20, num=100)
BANDWIDTH_BPS_BINS = NP.linspace(0, 20, num=100)

def get_new_filename(base, ext="", with_time=False):
    if with_time:
        base = str(base) + "_" + time.strftime("%Y%m%d-%H%M%S")
    current_base = base
    counter = 1
    while os.path.exists(current_base + ext):
        current_base = base + "_" + str(counter)
        counter += 1
    return current_base + ext

#def get_column_data(data_file, delimiter=None, converters=None, col_num=0):
#    assert type(col_num) is IntType, "col_num is not an integer: %r" % col_num
#    return NP.loadtxt(data_file, delimiter=delimiter, converters=converters, usecols=(col_num,))

def generate_hist_and_save(x, filename, generate_pdf=False, **kwargs):
    fig = plt.hist(x, **kwargs)
    plt.savefig(filename)
    if generate_pdf:
        plt.savefig(os.path.splitext(filename)[0] + ".pdf")
    plt.close()

def generate_bandwidth_pps_histograms(data_array):
    x = data_array[:,2]
    filename = get_new_filename(os.path.join(OUTDIR, "bwidth_pps"), ".eps")
    generate_hist_and_save(x, filename, bins=BANDWIDTH_PPS_BINS)
    filename = get_new_filename(os.path.join(OUTDIR, "bwidth_pps_cumul"), ".eps")
    generate_hist_and_save(x, filename, bins=BANDWIDTH_PPS_BINS,
                           cumulative=True, histtype='step', normed=True)

def generate_bandwidth_bps_histograms(data_array):
    x = data_array[:,3]
    filename = get_new_filename(os.path.join(OUTDIR, "bwidth_bps"), ".eps")
    generate_hist_and_save(x, filename, bins=BANDWIDTH_BPS_BINS)
    filename = get_new_filename(os.path.join(OUTDIR, "bwidth_bps_cumul"), ".eps")
    generate_hist_and_save(x, filename, bins=BANDWIDTH_BPS_BINS,
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

    # Load data from file into an array
    data_array = NP.loadtxt(data_file)

    # Bandwidth in packets-per-second histogram
    generate_bandwidth_pps_histograms(data_array)
    # Bandwidth in bytes-per-second histogram
    generate_bandwidth_bps_histograms(data_array)

    if data_file is not sys.stdin:
        data_file.close()


