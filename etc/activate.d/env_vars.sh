#!/bin/sh

echo "Setting environment variables"

export R_LIBS_BACKUP=$R_LIBS
export R_LIBS="$CONDA_BASE/envs/NeatSeq-Flow/lib/R/library"

