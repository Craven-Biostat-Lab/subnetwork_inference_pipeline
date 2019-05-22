master=hiv_0410_bg_genes_only_nohiv.tab
geneset=ptak_indirect_interactions
col=0
dk=kernel_hints_pr/hiv_75_kernel.list

#for geneset in moped_eg hippie_tcells_sans_housekeeping ptak_indirect_interactions reactome_hiv_eg
for gfile in genesets/*.tab
do
	# get filename without path or extension
	geneset=${gfile%.*}	# rem ext
	geneset=${geneset#*/}  # rem path
	#echo $geneset
	#continue

	if [ $geneset = "ptak_indirect_interactions" ]; then
		col=1
	else
		col=0
	fi

	# baselines
	for unit in avghit avgint avgpath; do
		opref=baselines_hints/baselines_75_${unit} #may15_totals_no_ints_rank_by_${unit}
		lpref=${opref#*/} # remove orig folder
		lpref=baselines_hints/genesets/${lpref}
		echo $lpref	#, ${lpref}_${geneset}.list

		if [ ! -e ${lpref}_${geneset}.list ]; then
			python2.7 ../disco_scripts/do_geneset_pr.py $opref.list $master genesets/$geneset.tab $col > ${lpref}_${geneset}.list
		fi

		if [ ! -e ${lpref}_${geneset}_chop.opr ]; then
			bash ../auc_and_chop.sh ${lpref}_${geneset}
		fi		

	done
	

	# kernel
	for opref in kernel_hints_pr/hiv_75_kernel #kernel_pr/hiv_25_kernel_hits kernel_pr/hiv_50_kernel_hits kernel_pr/hiv_75_kernel_hits; do
	do
		lpref=${opref#*/} # remove orig folder
		lpref=kernel_hints_pr/genesets/${lpref}
		echo $lpref	
		if [ ! -e ${lpref}_${geneset}.list ]; then
			python2.7 ../disco_scripts/do_geneset_pr.py $opref.list $master genesets/$geneset.tab $col > ${lpref}_${geneset}.list
		fi

		if [ ! -e ${lpref}_${geneset}_chop.opr ]; then
			bash ../auc_and_chop.sh ${lpref}_${geneset}
		fi
	done

	# steiner
	#for b in 0.1 0.2 0.3 0.4 0.5 1.0; do
	#	lpref=steiner_pr/steiner75_${b}
	#	echo $lpref
#
#		if [ ! -e ${lpref}_${geneset}.list ]; then
#			python2.7 ../disco_scripts/do_geneset_pr.py $lpref.list $master genesets/$geneset.tab $col > ${lpref}_${geneset}.list
#		fi
#
#		
#		if [ ! -e ${lpref}_${geneset}_chop.opr ]; then
#			bash ../auc_and_chop.sh ${lpref}_${geneset}
#		fi
#	done

	#continue

	# IP
	for lf in final_results/*.list; do  #hints_mp_results/*_results.list; do
		lpref=${lf%.*}	# remove extension
		echo $lpref 
		lpref=${lpref#*/} # remove orig folder
		lpref=final_results/genesets/${lpref}
		echo $lpref, $lf


		if [ ! -e ${lpref}_${geneset}.list ]; then
			python2.7 ../disco_scripts/do_geneset_pr.py $lf $master genesets/$geneset.tab $col > ${lpref}_${geneset}.list
			bash ../auc_and_chop.sh ${lpref}_${geneset}
		fi
			
		# sort by DK
		if [ ! -e ${lpref}_${geneset}_dksort.list ]; then
			python ../disco_scripts/sort_by_dk.py ${lpref}_${geneset}.list ${dk} > ${lpref}_${geneset}_dksort.list
			bash ../auc_and_chop.sh ${lpref}_${geneset}_dksort
		fi

	done

	


done

