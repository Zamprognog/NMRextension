#!/bin/bash

# This script emulates the provided Python snippet to process and sort rules.
# It extracts rules from a file, sorts them by confidence score in descending
# order, and prints the top N processed rules.

## --- Configuration ---

# The number of top rules to retrieve.
# It defaults to 13, as specified in the prompt, but can be overridden by a
# command-line argument (e.g., `./script.sh 5`).
N=${1:-13}

# The path to the input file containing the rules.
RULES_FILE="../rule_mining/YAGO3-10/mined_rules-100"

## --- Script Logic ---

# 1. Check if the rules file exists to prevent errors.
if [ ! -f "$RULES_FILE" ]; then
    echo "Error: The rules file was not found at '$RULES_FILE'" >&2
    exit 1
fi

# 2. Execute the processing pipeline.
#    The script chains together several standard Unix tools to achieve the result.
#    Each `|` (pipe) sends the output of one command to the input of the next.

awk -F'\t' '{gsub(/<=\s*/, "", $(NF-1)); print $(NF-1) "\t" $NF}' "$RULES_FILE" | \
    sort -k1,1nr | \
    head -n "$N" | \
    cut -f2- | \
    sed 's/(/ /g; s/,/ /g; s/)//g'