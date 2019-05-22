#!/bin/bash
# Breaks ties in IP results using the kernel scores.
# Usage: bash sort_ip_by_kernel.sh ip_list_directory dk_score.list
# Where ip_list_directory contains list files for the IP results
# and dk_score.list is a filename for a list file from the dk.

if [[ $# -ne 2 ]]; then
	echo "Usage: bash sort_ip_by_kernel.sh ip_list_directory dk_score.list"
	exit
fi

# make sure script is available
if [[ ! -e scripts/sort_by_dk.py ]]; then
	echo "I can't find scripts/sort_by_dk.py."
	exit
fi

dk=$2
# make sure DK file exists
if [[ ! -e ${dk} ]]; then
	echo "I can't find DK score file ${dk}."
	exit
fi

for f in $1/*.list; do
	# get the basename
	base=${f%.list}
	python scripts/sort_by_dk.py ${f} ${dk} > ${base}_by_dk.list
	echo "Created ${base}_by_dk.list"
done



