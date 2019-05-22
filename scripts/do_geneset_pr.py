"""
Given a list file with confidence values, replaces
the labels in that list file with binary values indicating
presence in a gene set file. 
Poduces a list file.

python ...py a.list master_labels.tab geneset.tab col
where "col" gives the appropriate column into geneset.tab.

"""
import sys
import numpy

def main(argv):
	listfn=argv[1]
	masterfn=argv[2]	
	genesetfn=argv[3]
	gcol=int(argv[4])

	# read list file
	# { gene : {"conf":float, "class":0/1}}
	confs=read_list(listfn)
	print "# read confs for %d genes" % len(confs)

	# read original labels: { g : hit OR hit|interface OR interface OR unknown }
	# so we can remove non-hidden input genes from the total recall
	master=read_master_labels(masterfn)
				
	# read gene set 
	targets=read_set(genesetfn, col=gcol)		
	tarbg = set.intersection(targets, master)
	print "# %d target genes provided in %s; %d in background network" % (len(targets), genesetfn, len(tarbg))

	cov = set.intersection(tarbg, set(confs.keys() ))
	ever = [ g for g in cov if confs[g]["conf"]>0 ]
	never_found =  [ g for g in cov if confs[g]["conf"]==0 ]

	missing = set.difference(tarbg, set(confs.keys() ))
	print "# %d targets given confs (%d never recalled, %d inaccessible)" % (len(ever), len(never_found), len(missing))

	input_tars_total = set([ g for g in targets if master.get(g, "unknown") != "unknown"] )
	input_tars_never_hidden = set( [ g for g in input_tars_total if g not in confs ] )
	print "# %d targets in total input; %d targets in non-hidden input" % ( len(input_tars_total), len(input_tars_never_hidden))


	# any remaining targets that WEREN'T input but ARE in the background network?
	mf = [ m for m in missing if master.get(m, "unknown") not in ["hit", "hit|interface", "interface"] ]
	if len(mf) > 0:
		print >> sys.stderr, "%d targets didn't receieve conf and aren't input?"

	# sort in descending order
	order=[ (g, gmap["conf"]) for (g,gmap) in confs.items() ]
	order.sort(key=lambda x : -x[1])
	
	# gene, conf
	for (g,c) in order:
		# class=1 if in target set
		cl = 0
		if g in targets:
			cl=1
		print "%f\t%d\t%s" % (c, cl, g)		
		
	# random guessing line
	prop = float(len(cov)) / len(order)
	print "# set arrow 1 from 0,%.3f to 1,%.3f nohead lt 2" % (prop, prop)
	
	
def read_set(fn, col=0):
	""" 
	Reads a gene set. Gene ID is in the provided column.
	"""
	gset=set()
	with open(fn) as f:
		for line in f:
			if "#" == line[0]:
				continue
			sp=line.strip().split("\t")			
			gene=sp[col]
			gset.add(gene)
	return gset

def read_list(fn):
	"""
	Reads a list file for the PR tool.
	Returns: { gene : {"conf":float, "class":0/1}}
	"""
	confs={}
	with open(fn) as f:
		for line in f:
			if "#" == line[0]:
				continue
			sp=line.strip().split("\t")
			try:
				conf=float(sp[0])
				cl=int(sp[1])
			except ValueError:
				# not correctly formatted - must be comment line
				continue
			gene=sp[2]
			if gene in confs:
				print >> sys.stderr, "duplicate", gene
			confs[gene]={"conf":conf, "class":cl}
	return confs
	
	
def read_master_labels(fn):
	"""
	Reads the master label file	
	Labels: hit, interface, hit|interface, unknown
	"""
	labels={}	# gene : label
	with open(fn) as f:
		for line in f:
			if "#" in line:
				continue
			sp=line.strip().split("\t")
			g=sp[0]
			l=sp[1]
			if g in labels:
				print >> sys.stderr, g
			labels[g]=l

	return labels

if __name__=="__main__":
	sys.exit(main(sys.argv))






