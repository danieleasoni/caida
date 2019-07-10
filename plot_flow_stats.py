from __future__ import print_function
import sys, os
import matplotlib
matplotlib.use('Agg')
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
LIFETIME_BINS = NP.linspace(0, 3600, num=100)
SCATTER_SAMPLE_SIZE = 250000

PROTOCOL_COL = 1
LIFETIME_COL = 2
PKT_COUNT_COL = 3
TOTAL_BYTES_COL = 4
#LIFETIME_COL = 1
#PKT_COUNT_COL = 2
#TOTAL_BYTES_COL =3
#BANDWIDTH_COL = 14

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

def generate_hist_and_save(x, filename, bins=50, generate_pdf=False):
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

def generate_scatter(x, y, num_samples=None,
        xlabel='Session lifetime (seconds)', ylabel='bandwidth',
        basefilename="lifetime_vs_bw"):
    assert len(x) == len(y)
#    if num_samples is not None:
#        NP.random.seed(0)
#        idx = NP.random.choice(len(x), num_samples)
#        x = x[idx]
#        y = y[idx]
#    # Generate and save normal scatterplot
#    filename = get_new_filename(os.path.join(OUTDIR, basefilename + "_scatter"), ".pdf")
#    fig = plt.scatter(x, y, c='blue', alpha=0.03, edgecolors='none')
#    ax = plt.gca()
#    ax.set_yscale('log')
#    ax.set_xscale('log')
#    ax.set_xlim([0.005, 62])
#    plt.xlabel(xlabel, fontsize=16)
#    plt.ylabel(ylabel, fontsize=16)
#    plt.savefig(filename)
#    plt.close()

    # Generate and save heatmap
    filename = get_new_filename(os.path.join(OUTDIR, basefilename + "_heat"), ".eps")
    fig = plt.hexbin(x, y, norm=matplotlib.colors.LogNorm(), linewidths=(0,),
            xscale='log', yscale='log', cmap=plt.cm.Greys)#cmap=plt.cm.YlOrRd)
    ax = plt.gca()
    PCM=ax.get_children()[2]
    ax.set_yscale('log')
    ax.set_xscale('log')
    ax.set_xlim([0.005, 3000])
    ax.set_ylim([85, 800000000])
#    ax.set_xlim([0.05, 5000])
#    ax.set_ylim([0.0004, 300])
#    cb = plt.colorbar(PCM, ax=ax)
#    cb.set_label('Number of samples (out of ' + str(len(y)) + ')')
    plt.xlabel(xlabel, fontsize=16)
    plt.ylabel(ylabel, fontsize=16)
#    X = NP.logspace(-3,4,num=50)
#    Y0 = X
#    plt.loglog(X,Y0, 'k')
#    plt.text(X[-1]/12, Y0[-1]/3, '1 B/s')
#    Y1 = X * 100
#    plt.loglog(X,Y1, 'k')
#    plt.text(X[-1]/20, Y1[-1]/3, '100 B/s')
#    Y2 = X * 10000
#    plt.loglog(X,Y2, 'k')
#    plt.text(X[-1]/20, Y2[-1]/3, '10 kB/s')
#    Y3 = X * 1000000
#    plt.loglog(X,Y3, 'k')
#    plt.text(X[-1]/150, Y3[-1]/25, '1 MB/s')
#    # Plot cluster points
#    s1, = plt.loglog([0.1,1,10,30,60,100], [10**4]*6, 'wo', label=r'$S_1$', markersize=8)
#    s2, = plt.loglog([1,10,30,60,100], [10**5]*5, 'co', label=r'$S_2$', markersize=8)
#    s3, = plt.loglog([10,30,60,100], [10**6]*4, 'ko', label=r'$S_3$', markersize=8)
#    plt.legend(loc=2, numpoints=1)
    # Plot cluster points
    s1, = plt.loglog([10,100, 1000], [10**4, 10**5, 10**6], 'wo', label=r'$S_1$', markersize=8)
    s2, = plt.loglog([10,100, 1000], [10**5, 10**6, 10**7], 'co', label=r'$S_2$', markersize=8)
    s3, = plt.loglog([10,100], [10**6, 10**7], 'ko', label=r'$S_3$', markersize=8)
    #plt.show()
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
    #generate_hist_and_save(data_array[:,LIFETIME_COL], "lifetime_sec", bins=LIFETIME_BINS)
    # Bandwidth in packets-per-second histogram
    #generate_hist_and_save(data_array[:,3], "bwidth_pps", bins=BANDWIDTH_PPS_BINS)
    # Bandwidth in bytes-per-second histogram
    #generate_hist_and_save(data_array[:,BANDWIDTH_COL], "bwidth_bps") #, bins=BANDWIDTH_BPS_BINS)
    # Scatter plot of lifetime vs number of packets
#    generate_scatter(data_array[:,LIFETIME_COL], data_array[:,PKT_COUNT_COL],
#                     ylabel='num. of packets per flow',
#                     basefilename="packet_num_vs_lifetime",
#                     num_samples=SCATTER_SAMPLE_SIZE)
    # Scatter plot of lifetime vs total data
    if any(data_array[:,LIFETIME_COL] <= 0.0):
        print("Some flows have a non-positive lifetime, ",
              "cannot plot them logarithmically.", file=sys.stderr)
        print("Hint: use  awk '$" + str(LIFETIME_COL+1) +
              " != 0 { print $0 }' to filter.", file=sys.stderr)
        sys.exit(1)
    generate_scatter(data_array[:,LIFETIME_COL], data_array[:,TOTAL_BYTES_COL],
                     ylabel='Total data per flow (bytes)',
                     basefilename="total_data_vs_lifetime",
                     num_samples=SCATTER_SAMPLE_SIZE)
    # Scatter plot of lifetime vs bandwidth
    #generate_scatter(data_array[:,LIFETIME_COL], data_array[:,BANDWIDTH_COL],
    #                 ylabel='bandwidth (bytes per second)',
    #                 num_samples=SCATTER_SAMPLE_SIZE)

    if data_file is not sys.stdin:
        data_file.close()


