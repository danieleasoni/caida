#!/bin/bash

#BASE_DIR=$(pwd)
BASE_DIR=data.caida.org/datasets/passive-2015/equinix-chicago
TARGET_DIR=uncompressed

for FULLDIR in $BASE_DIR/* ; do
    if [ ! -d $DIRNAME ]; then
        continue
    fi

    FULLDIR=${FULLDIR%/}  # Remove trailing slash, if any
    DIRNAME=${FULLDIR##*/}  # Remove all from left up to rightmost "/"
    mkdir -p $TARGET_DIR/$DIRNAME

    echo "Extracting into " $TARGET_DIR"/"$DIRNAME

    for FULL_FILE in $FULLDIR/*dirA*.pcap.gz ; do
        filename=$(basename $FULL_FILE)
        filename_no_gz=${filename%.*}
        target_file=$TARGET_DIR/$DIRNAME/$filename_no_gz
        if [ -e $target_file ]; then
            continue;
        fi
        echo -n .
        zcat $FULL_FILE > $target_file
    done
    echo
done
