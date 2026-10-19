#!/bin/bash
# pipeline_busy.sh: exit 0 (and print what) if a Unity house build/load/bake is running, else exit 1.
# Use this instead of an inline `pgrep -f "unity_pipeline.sh ..."`: a wait loop whose own command line contains that pattern
# matches itself and waits forever (Oct 18). Wait:  until ! tools/house/pipeline_busy.sh >/dev/null; do sleep 30; done
ps -axo pid=,command= | awk '$0 ~ /unity_pipeline\.sh (build|load|bake|all)( |$)/ && $0 !~ /pipeline_busy|awk|until|while/ {print substr($0,1,100); f=1} END {exit f?0:1}'
