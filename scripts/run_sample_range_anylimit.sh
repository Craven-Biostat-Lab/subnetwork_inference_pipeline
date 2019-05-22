# Starts running a range of GAMS jobs (serial is implemented).
# Args: top directory, start ID, stop ID.
# Skip if a log or gdx file already exists.
# If fourth argument is "serial", then run
# the jobs in serial - wait to finish before starting the next.

if [ "$#" -lt 3 ]; then
	echo "Too few args. Usage: topdir limit start stop"
	echo "Runs in serial mode."
	exit	
fi


topdir=$1
limit=$2
start=$3
stop=$4
mode="serial"
hidemode="both"	# hits, ints, both

if [ "$#" -eq 5 ]; then
	echo "Only serial mode is implemented."
	exit
	#mode=$4
	#echo "${mode} mode"
fi

# assuming topdir like ../subsets_0.25_name
# and sample dirs within are /subsets_0.25_name/sample_0.75_0_hits/
# and limit dirs within that are /subsets_0.25_name/sample_0.75_0_hits/add_50
#echo $topdir

# use percent=75 because that's what I've settled on
p=0.75
echo "sample percent: ${p}"

pwd=$(pwd)
cd ${topdir}
for i in $(seq $start $stop); do
	base=sample_${p}_${i}_hits/add_${limit}

	if [ ! -d ${base} ]; then
		echo "Skipping $i; no directory ${base}"
		cd ${pwd}/${topdir}
		continue
	fi
	cd $base
	if [ -e *.log ]; then
		echo "Skipping $i; found log file"
		cd ${pwd}/${topdir}
		continue
	fi
	if [ -d 225* ]; then
		echo "Skipping $i; found cplex temp directories"
		cd ${pwd}/${topdir}
		continue
	fi

	if [ ! -e run*.gms ]; then
		echo "Skipping $i; no gams file."
		cd ..
		continue
	fi
	gms=$(ls run*.gms)

	samplesetfn=../hiv_${p}_${i}_moresets.gms

	if [ ! -e ${samplesetfn} ]; then
		echo "No set file for sample ${i} - you've gotta make it. Skipping."
		cd ${pwd}/${topdir}
		continue
	fi

#	if [ $mode == "serial" ]; then
		echo "gams serial"
		gams $gms lo=2
#	else

#		gams $gms lo=2 &
#		echo "gams parallel"
#	fi

	pid=$!
	echo "Running $i $gms with pid $pid"
	cd ${pwd}/${topdir}
done
cd ${pwd}



