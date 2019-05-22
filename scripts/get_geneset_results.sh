#!/bin/bash
# Evaluates a directory of list files against a directory of gene sets (tab) files.
# Produces a new list file for each comparison (in the list directory).
# 
# Usage: bash get_geneset_lists.sh list_dir_pat geneset_dir output_dir

if [ $# != 3 ]; then
	echo "Usage: bash get_geneset_lists.sh list_dir geneset_dir output_dir"
	exit
fi

list_dir=$1
geneset_dir=$2
output=$3

# check existence of script and args
if [[ ! -e scripts/do_geneset_pr.py ]]; then
	echo "I can't find scripts/do_geneset_pr.py."
	exit
fi

if [[ ! -e scripts/sort_by_dk.py ]]; then
	echo "I can't find scripts/sort_by_dk.py."
	exit
fi

for f in $master $list_dir $geneset_dir; do
	if [[ ! -e $f ]]; then
		echo "Can't find $f"
		exit
	fi
done

if [[ ! -d $output ]]; then
	echo "Making output directory " $output
	mkdir $output
fi


# run
for listf in ${list_dir}/*.list; do
	# get the list file's basename
	base=${listf%.list}
	nopathbase=${base##*/}
	#echo $base
		
	for genef in ${geneset_dir}/*.tab; do
		# get the gene set name
		gs=${genef%.tab}
		gs=${gs##*/}

		python scripts/make_geneset_list.py ${listf} ${genef} > ${output}/${nopathbase}_${gs}.list	
		echo "Made ${output}/${nopathbase}_${gs}_test.list"
	done
done



