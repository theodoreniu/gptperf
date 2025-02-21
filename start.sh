#!/bin/bash

set -e

streamlit run web.py --server.address 0.0.0.0 --server.runOnSave true --server.fileWatcherType poll --browser.gatherUsageStats false
