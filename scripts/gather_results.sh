# Grabs GDX files from one directory
# copies them to another
# does the processing and eval
# if there is an 8th arg, it will tell us which stage to start
# g : move GDX files
# d : dump info from GDX files
# e : extract scores 

if [[ $# -ne 7 && $# != 8 ]]; then
	echo "Usage: gather_results.sh gams_dir where_to_put_gdx where_to_dump_data prefix_for_summary_files version hidden_by_sample_file master_node_label_file [g,d,e] "
	exit
fi

master=$1
gdxdir=$2
dumpdir=$3
prefix=$4
version=$5	# hits_and_ints or just hits_only?
asidefile=$6	# hidden_by_sample.tab file
nodefile=$7	# master node label file

# if hits_and_ints, then we have a slightly different directory structure


# location of HIV script directory 
hivhome=$(pwd)
scripts=${hivhome}/scripts

# maps held-aside hits to sample ID
#asidefile=${hivhome}/dk_scores_nov2014/hiv_0.75_hidden_by_sample.tab
# labels for nodes used in DK
#nodefile=${hivhome}/data/hiv_human_master_labels.tab

if [ ! -e ${asidefile} ]; then
	echo "Can't find the hidden-by-sample file ${asidefile}. Need to update?"
fi


if [ ! -e ${nodefile} ]; then
	echo "Can't find the master node label file ${nodefile}. Need to update?"
fi


start=g
if [ "$#" -eq 8 ]; then
	# which stage?
	chosen=1
	for o in g d e;
	do	
		if [ "$o" = "$8" ]; then
			start=$o
			chosen=0
		fi			
	done
	if [ $chosen -eq 1 ]; then
		echo "Please choose one of [g,d,e] to select start point."
		exit 
	fi
fi


if [ ! -e ${asidefile} ]; then
	echo "Couldn't find hit map file ${asidefile}"
	exit
elif [ ! -e ${nodefile} ]; then
	echo "Couldn't find original label file ${nodefile}"
	exit
fi


if [ $start = g ]; then
	find ${master} -iname "*.gdx" -exec cp -n {} ${gdxdir} \;
	echo "(stage g) copied gdx files to ${gdxdir}"
	start=d
fi

if [ $start = d ]; then
	bash ${scripts}/dump_information.sh ${gdxdir} ${dumpdir} ${prefix}
	echo "(stage d) dumped info from gdx files to ${dumpdir}"
	start=e
fi

if [ $start = e ]; then
	python ${scripts}/eval_sample_results.py ${dumpdir} ${asidefile} ${nodefile} ${version} > ${prefix}_results.list
	echo "(stage e) extracted scores into ${prefix}_results.list"
fi

