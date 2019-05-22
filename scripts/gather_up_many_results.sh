# Gathers results for a given top directory, for a range of add-limits.
# Creates results directories if they don't exist already.
# This is kind of buggy and doesn't fail gracefully if you run it incorrectly :(
# Usage: bash gather_up_many_results.sh gams_top_dir date_string nickname"
# Date string will identify the result file for you (like dec07) "
# You may want nickname to match the top directory's nickname, as in hiv_0.75_{nickname}.

if [[ $# -ne 5 ]]; then
	echo "Usage: gather_up_many_results.sh gams_top_dir date_string nickname hidden_by_sample_file master_node_label_file"
	echo "Date string will identify the result file for you (like dec07) "
	echo "Nickname gives you another identifier; you may want it to match the top directory's nickname, as in hiv_0.75_{nickname}"
	exit
fi

topdir=$1
date=$2
name=$3
hidden=$4
labels=$5

# sample percentage
i=0.75

# range of add-limits
for j in 500 750 1000 5000
do
	if [ ! -e ${date}_${i}_${j}_${name}_results.list ]; then
	
		if [[ ! -d results_${j}_${name} ]]; then
			mkdir results_${j}_${name}/
		fi

		if [[ ! -d results_${j}_${name}/gdx ]]; then
			mkdir results_${j}_${name}/gdx
		fi
		
		if [[ ! -d results_${j}_${name}/res ]]; then
			mkdir results_${j}_${name}/res
		fi

		bash ./scripts/gather_results.sh "${topdir}/*/add_${j}" results_${j}_${name}/gdx/ results_${j}_${name}/res/ ${date}_${i}_${j}_${name} hits_and_ints $hidden $labels
	else
		echo "${date}_${i}_${j}_${name}_results.list already exists"
	fi
done
