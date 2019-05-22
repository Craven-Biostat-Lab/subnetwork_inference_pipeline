# Constructs sub-directories and specialized GAMS run scripts to run inference of samples.
# In this version of the script, the directory format is:
# - master_output_directory ("subsets_0.75_etc") (contains cplex options)
#	-- sample_0.75_0_hits/ (contains custom path file)
#		-- add_50 (contains gams running file, links up to cplex, path file)
#		-- add_100
#		(etc)
# Before running this, make sure you have run create-per-sample_pathfiles.sh
# to create the GAMS set for each sample. This script will link in the path-set file
# to the subdirectory.

# USAGE: set_up_for_any_limit.sh start_sample_ID end_sample_ID allowed_addl_genes nickname_for_new_directory threads_for_cplex
# nickname can be anything. This will produce a directory like "hiv_0.75_nickname".

# Lots of params are provided in this file.

# Check out #### HARD CODED THINGS ##### for some filenames that you'll want to
# change to run this with a different background network and score set!

# Things replaced in the main GAMS file:
#Filenames: {ALL_SETS}, {SPEC_SET}, {SAMPLE_SETS}, {SCORE_FILE}, {OUTPUT_FILE}, {MODEL}
#Floats (parameters): {CX_ODDS}, {MIN_NODE_OPT_TOL}, {MAX_PATH_OPT_TOL}
#

pwd=$(pwd)

if [ "$#" -ne 5 ]; then
	echo "Usage: set_up_for_any_limit.sh start end limit identifier threads_for_cplex"
	echo "where identifier gives a unique nickname for the directory that we're setting up." 
	exit
fi

# start and stop file?
start=$1
stop=$2

# allowed number of additional genes
addlimit=$3

# identifying name for output directory
name=$4

# number threads
threads=$5

echo "start $1, stop $2, limit $3, name $4"

#### HARD CODED THINGS ####

### BACKGROUND-NETWORK SPECIFIC THINGS: You will want to change this if you change the background network! ####

# sampling (kept) hit/interface percentage
p=0.75

# location of sampled hit/score files
scoredir=${pwd}/dk_scores/sample${p}

# master sets: nodes, edges, features... common to all 
setfn=${pwd}/data/hiv_len3_master.gms

# Location of per-sample pathfiles
pathfiles=pathfiles

####

# required level of overrepresentation of active complexes
cxodds=2.0
# optimality tolerance for min-node and max-path objective functions
mintol=0.05
maxtol=0.05

# original file locations
optreplace=${pwd}/model/cplex.opt_replace
runreplace=${pwd}/model/run_sample_maxpath_replace.gms

# location of sample-specific files 
pathdir=${pwd}/${pathfiles}

# location for new subdirectories!
outdir=hiv_${p}_${name}


# does output directory exist?
if [ ! -d "${outdir}" ]; then
	echo "Making directory ${outdir}"
	mkdir ${outdir}
fi


# gams file parameters
# global
modelfn=${pwd}/model/model.gms

# for making sample-specific paths - do we hide hits, interfaces, or both?
hidemode=both

#### START ####

# make a cplex option file per add-limit
cplexlim=${outdir}/cplex.opt_${addlimit}
if [ ! -e "${cplexlim}" ]; then
	sed s/{THREADS}/${threads}/ ${optreplace} > ${cplexlim}
	echo "made ${cplexlim}"
else
	echo "Already made cplex option file; using previous thread choice."
fi


# set up subdirectories - one for each sample
for i in $(seq ${start} ${stop})
do
	f=${scoredir}/sample_${p}_${i}_hits.gms
	# skip rest if no score file
	if [ ! -f ${f} ]; then
		echo "no score file" ${f}
		continue
	fi
	base=${f##*/}  # remove path
	#echo $base
	base=${base%.*} # remove extension 
	#echo ${base}	

	# does data exist? if not, skip rest
	if [ ! -f ${setfn} ]; then
		echo "no master GAMS set file" ${setfn}
		continue
	fi

	# does this sample's subdirectory exist?
	if [ ! -d "${outdir}/${base}" ]; then
		echo "Making sample directory ${outdir}/${base}"
		mkdir ${outdir}/${base}
	fi

	# go into the sample directory
	cd ${outdir}/${base}/

	# sample-specific sets - need to make
	samplesetfn=hiv_${p}_${i}_moresets.gms
	echo ${pathdir}/${samplesetfn}

	if [ -e "${samplesetfn}" ]; then
		echo "${samplesetfn} exists in " $(pwd)
	elif [ ! -e ${pathdir}/${samplesetfn} ]; then
		echo "No path file for this run - skipping"
		cd ${pwd}
		continue
	else
		echo "Linking in sample set file ${samplesetfn}"
		ln -s ${pathdir}/${samplesetfn} .

		# make sure it worked
		ok=$(wc -l ${samplesetfn} | awk '{print $1}')
		if [ $ok -lt 10 ]; then
			echo "Failed to get custom pathfile. Skipping."
			continue
		fi
	fi

	# now, for the specified add-limit...
	addir=add_${addlimit}

	if [ ! -d "${addir}" ]; then
		echo "Making run directory ${addir}"
		mkdir ${addir}
	fi

	cd ${addir}

	# link in the cplex file if not linked
	if [ ! -L "cplex.opt" ]; then
		ln -s ../../cplex.opt_${addlimit} cplex.opt
	fi

	# copy in the gams file with replacements
	# strings {ALL_SETS}=setfn, {SPEC_SET}=specfn, {SCORE_FILE}=f, {OUTPUT_FILE}=base_result.gdx, {MODEL}=modelfn
	# floats : {CX_ODDS}=cxodds, {MIN_NODE_OPT_TOL}=mintol, {MAX_PATH_OPT_TOL}=maxtol
	if [ ! -f "run_${base}.gms" ]; then
	sed "s,{ALL_SETS},${setfn},; s,{SCORE_FILE},${f},; s,{OUTPUT_FILE},${base}_${addlimit}_result,; s,{MODEL},${modelfn},; s,{CX_ODDS},${cxodds},; s,{MIN_NODE_OPT_TOL},${mintol},; s,{MAX_PATH_OPT_TOL},${maxtol},; s,{SPEC_SET},${specfn},;s,{SAMPLE_SETS},../${samplesetfn},; s,{LIMIT},${addlimit},;" ${runreplace} > run_${base}.gms
	echo "made run file" run_${base}
	else 
		echo "${outdir}/${base}/run_${base}.gms already exists?"
	fi

	# go back to top
	cd ${pwd}

done
