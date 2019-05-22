"""
Given a list file, sorts equal-confidence predictions according to DK score.

Usage:
sort_by_dk.py a.list dk.list > a_sort.list
"""
import sys
from hiv_utils import *


# read_list(fn) returns: { gene : {"conf":float, "class":0/1}}
a=read_list(sys.argv[1])
b=read_list(sys.argv[2])

# sort a in decreasing order by conf
alist = [ (gene, a[gene]["conf"], a[gene]["class"]) for gene in a ] 
alist.sort(key=lambda x : -1*x[1])

# make same-conf bins
bins=[]
bin=[ alist[0] ]
for (gene, conf, label) in alist[1:]:
	if bin[0][1]==conf:
		bin.append( (gene, conf, label) )
	else:
		bins.append(bin)		
		bin=[ (gene, conf, label) ]
bins.append(bin)
#print len(bins)

final=[]
# don't sort if conf==0
for i in range(len(bins)):
	bin=bins[i]
	if bin[0][1]==0.0:
		final.extend(bin)
	else:
		# sort within bin using b's scores
		bin.sort(key=lambda x : -1*b[x[0]]["conf"])	
		final.extend(bin)


print "# Sorted %d equal-confidence bins in %s according to scores given by %s" % (len(bins), sys.argv[1], sys.argv[2])
#print len(final)
tot=len([x for x in final if x[1] > 0])
print "# Recalculated scores for %d non-zero-conf items." % tot
i=0.0
for (gene, conf, label) in final:
	if conf > 0:
		newconf = 1.0-(i/tot)
	else:
		newconf=0.0
	print "%.8f\t%d\t%s" % (newconf, label, gene)
	i+=1.0

