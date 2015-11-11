#!/bin/bash

BASE_DIR=$(pwd)
TARGET_DIR=caida_uncompressed

for FULLDIR in $BASE_DIR/caida_data_trace/* ; do
    if [ ! -d $DIRNAME ]; then
        continue
    fi

    DIRNAME=${FULLDIR##*/}
    mkdir -p $TARGET_DIR/$DIRNAME
    
    echo "Extracting into " $TARGET_DIR"/"$DIRNAME
    
    for FULL_FILE in $FULLDIR/*.pcap.gz ; do
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
