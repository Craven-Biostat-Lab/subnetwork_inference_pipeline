#!/bin/bash
cwd=${PWD}

tar -xzf python.tar.gz
export PATH=${cwd}/python/bin:$PATH
mkdir home
export HOME=${cwd}/home


id=${1}


#FILES COPIED IN FROM OTHER PARTS OF PIPELINE
label_file=${cwd}/data/hiv_human_master_labels.tab
hidden_by_file=${cwd}/data/hiv_0.90_hidden_by_sample.tab
path_file=${cwd}/data/hiv_len3_master_paths.tab
subgraph_file=${cwd}/data/hiv_len3_master_subgraphs.tab
setfn=${cwd}/data/hiv_len3_master.gms


hidemode=both

threads=8
p=0.90
addlimit=750

echo "creating pathfiles"
${cwd}/python/bin/python scripts/create_custom_pathfile_batch.py ${id} ${id} ${hidemode} ${label_file} ${hidden_by_file} ${path_file} ${subgraph_file} hiv_${p}_%d_moresets.gms



# required level of overrepresentation of active complexes
cxodds=2.0
# optimality tolerance for min-node and max-path objective functions
mintol=0.05
maxtol=0.05

# original file locations
optreplace=${cwd}/model/cplex.opt_replace
runreplace=${cwd}/model/run_sample_maxpath_replace.gms

echo ${optreplace}

cplexlim=${cwd}/cplex.opt_${addlimit}

# location for new subdirectories!
outdir=hiv_${p}_${name}

# gams file parameters
# global
modelfn=${cwd}/model/model.gms


echo "creating cplex"
sed s/{THREADS}/${threads}/ ${optreplace} > ${cplexlim}

mv ${cplexlim} cplex.opt

#sample file
f=${cwd}/sample_${p}_${id}_hits.gms

base=${f##*/}  # remove path
base=${base%.*} # remove extension 
echo $base

samplesetfn=${cwd}/hiv_${p}_${id}_moresets.gms

echo "creating run by"
sed "s,{ALL_SETS},${setfn},; s,{SCORE_FILE},${f},; s,{OUTPUT_FILE},${base}_${addlimit}_result,; s,{MODEL},${modelfn},; s,{CX_ODDS},${cxodds},; s,{MIN_NODE_OPT_TOL},${mintol},; s,{MAX_PATH_OPT_TOL},${maxtol},; s,{SPEC_SET},${specfn},;s,{SAMPLE_SETS},${samplesetfn},; s,{LIMIT},${addlimit},;" ${runreplace} > run_${base}.gms

/mnt/gluster/data2/gams/gams run_${base}.gms -lo=2
#ls -l /mnt/gluster/data2/gams

rm ${samplesetfn}
rm cplex.opt
rm run_${base}.gms
rm run_${base}.log
rm run_${base}.lst
gdxfile=${base}_${addlimit}_result.gdx
ls -l


#echo ${cwd}/${gdxfile}
for i in sigma x y
do
echo ${i}
/mnt/gluster/data2/gams/gdxdump ${cwd}/${gdxfile} symb=${i} |grep ".L 1," | awk -v i="${i}" -F"," '{print $1}' |awk -v i="${i}" -F".L " '{print i"\t"$1"\t"$2}' >> ${base}_${addlimit}_result_dump
done	

rm ${gdxfile}
