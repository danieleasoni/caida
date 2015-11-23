from __future__ import print_function
import sys, os
import matplotlib
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
LIFETIME_BINS = NP.linspace(0, 20, num=100)
SCATTER_SAMPLE_SIZE = 25000

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

def generate_hist_and_save(x, filename, bins=None, generate_pdf=False):
    # Generate and save normal histograms
    filename = get_new_filename(os.path.join(OUTDIR, filename), ".eps")
    fig = plt.hist(x, bins=bins)
    plt.savefig(filename)
    if generate_pdf:
        plt.savefig(os.path.splitext(filename)[0] + ".pdf")
    plt.close()
    # Generate and save cumulative distribution
    filename = os.path.splitext(filename)[0] + "_cumul.eps"
    fig = plt.hist(x, bins=bins, cumulative=True, histtype='step', normed=True)
    ax = plt.gca()
    ax.set_ylim([ax.get_ylim()[0], 1.0]) #Set maximum to 1 for normed y-axis (cumulative distrib)
    plt.savefig(filename)
    if generate_pdf:
        plt.savefig(os.path.splitext(filename)[0] + ".pdf")
    plt.close()

def generate_lifetime_bandwidth_scatter(lifetime, bandwidth, num_samples=None,
        xlabel='session lifetime (seconds)', ylabel='bandwidth'):
    assert len(lifetime) == len(bandwidth)
    if num_samples is not None:
        NP.random.seed(0)
        idx = NP.random.choice(len(lifetime), num_samples)
        lifetime = lifetime[idx]
        bandwidth = bandwidth[idx]
    # Generate and save normal scatterplot
    filename = get_new_filename(os.path.join(OUTDIR, "lifetime_vs_bw_scatter"), ".pdf")
    fig = plt.scatter(lifetime, bandwidth, c='blue', alpha=0.03, edgecolors='none')
    ax = plt.gca()
    ax.set_yscale('log')
    ax.set_xscale('log')
    ax.set_xlim([0.05, 5000])
    ax.set_ylim([0.0004, 300])
    plt.xlabel(xlabel, fontsize=16)
    plt.ylabel(ylabel, fontsize=16)
    plt.savefig(filename)
    plt.close()
    # Generate and save heatmap
    filename = get_new_filename(os.path.join(OUTDIR, "lifetime_vs_bw_heat"), ".pdf")
    fig = plt.hexbin(lifetime, bandwidth, norm=matplotlib.colors.LogNorm(), linewidths=(0,),
            xscale='log', yscale='log', cmap=plt.cm.YlOrRd)
    ax = plt.gca()
    PCM=ax.get_children()[2]
    ax.set_yscale('log')
    ax.set_xscale('log')
    ax.set_xlim([0.05, 5000])
    ax.set_ylim([0.0004, 300])
    cb = plt.colorbar(PCM, ax=ax)
    cb.set_label('# samples (out of ' + str(SCATTER_SAMPLE_SIZE) + ')')
    plt.xlabel(xlabel, fontsize=16)
    plt.ylabel(ylabel, fontsize=16)
    plt.savefig(filename)
    plt.close()

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

    # Session lifetime in seconds histogram
    #generate_hist_and_save(data_array[:,2], "lifetime_sec", bins=LIFETIME_BINS)
    # Bandwidth in packets-per-second histogram
    #generate_hist_and_save(data_array[:,3], "bwidth_pps", bins=BANDWIDTH_PPS_BINS)
    # Bandwidth in bytes-per-second histogram
    #generate_hist_and_save(data_array[:,4], "bwidth_bps", bins=BANDWIDTH_BPS_BINS)
    # Scatter plot of lifetime vs bandwidth
    generate_lifetime_bandwidth_scatter(data_array[:,2], data_array[:,4], ylabel='bandwidth (bytes per second)', num_samples=SCATTER_SAMPLE_SIZE)

    if data_file is not sys.stdin:
        data_file.close()


