# Uses gdxdump to dumps node, edge, path relevance variables
# from gdx files in directory $1
# into a directory specified by $2
# then summarizes into three files with prefix $3
gdxdir=$1
outdir=$2
pref=$3

echo "Deleting existing dump files"
echo $(pwd)

rm -f ${outdir}/*_dump

for fn in ${gdxdir}/*gdx
do
	f=${fn##*/}  # remove path
	f=${f%.*} # remove extension
	for i in sigma x y
	do
		gdxdump ${gdxdir}/${f}.gdx symb=${i} Format=csv | grep -v ",0" | grep -v "Val" | awk -v i="${i}" -F"," '{print 	i"\t"$1"\t"$2}' >> ${outdir}/${f}_dump
	done	
done

python scripts/gather_path_solution_info.py "${outdir}/*_dump" ${outdir}/${pref}


