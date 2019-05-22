"""
 Evaluates an ensemble of samples.
 For each hidden node (hit or interface), calculates frequency of inferred relevance when held aside.
 For each non-hit/non-interface), calculates frequence of inferred relevance in all solutions.

Usage:
eval_sample_results.py results_dir hit_sample_matchfile.tab node_label_file.tab
where results_dir contains dumped output from "dump_information.sh".
"""
import sys
import os
import glob
from hiv_utils import *

def main(argv):
	resdir=argv[1]
	hitmapfn=argv[2]
	
	# node labels: hit, hit|interface, hiv, unknown
	labelfn=argv[3]

	hide_ints=False
	if len(argv)>4 and "ints" in argv[4]:
		hide_ints=True
		print "# Allowing interfaces to be hidden as well"

	(hitmap, allhits)=read_hitmap(hitmapfn)
	print "# read %d hits for %d samples from %s" % (len(allhits), len(hitmap), hitmapfn)

	
	labels=read_labels(labelfn)
	print "# read %d labelled nodes from %s" % (len(labels), labelfn)
	hits=[ n for (n,l) in labels.items() if "hit" in l]

	ints=[ n for (n,l) in labels.items() if "interface" in l]
	onlyhits=[ n for (n,l) in labels.items() if "hit" in l and "interface" not in l]
	other=set([ n for (n,l) in labels.items() if "unknown" in l])

	print "# kernel BG contains %d hits, %d interfaces, and %d hits that are not interfaces" % (len(hits), len(ints), len(onlyhits))
	print "# hitmap contains %d hits that are not interfaces" % len(set.difference(allhits, ints))


	# which to consider hits? anything that's held aside.
	# total possible hidden set
	totHideable=set()
	if hide_ints:
		modes=["hit","hit|interface","interface"]
	else:
		modes=["hit"]
	hset = [ n for (n,l) in labels.items() if l in modes ]
	totHideable=set.union(totHideable, hset)
	print "# total of %d targets in BG" % len(totHideable)
	
	# remove interfaces from the held-aside hit sets?
	# or just count
	temp={}
	totAside=set()
	for (sid, gs) in hitmap.items():
		if not hide_ints:
			temp[sid]=set.difference(gs,ints)
			totAside=set.union(temp[sid], totAside)
		else:
			totAside=set.union(gs, totAside)
	
	if not hide_ints:	
		hitmap=temp 
	print "# %d nodes ever held aside" % len(totAside)

	# for each non-interface hit and non-interface other node,
	# store count of "in" solutions (inferred, success) and "out" solutions (not inferred, fail)

	tallies={}	# key: EID, val: {"in":[], "out":[]}	
	for o in other:
		tallies[o]={"in":[], "out":[]}
	#for m in modes:
	hset = [ n for (n,l) in labels.items() if l in modes ]
	for h in hset:
		tallies[h]={"in":[], "out":[]}
	print "# tallying up for %d total genes" % len(tallies)

	# go through sols
	ls = glob.glob(os.path.join(resdir, "*_dump"))
	totSols=0
	countNodes=0 # use to count nodes per solution
	for f in ls:
		# result_dumped/sample_0.25_101_hits_result_dump
		sid = int(os.path.split(f)[1].split("_")[2])
		#print sid
		nodes = get_nodes(f)
		# check for dump failure - don't even count it as a real solution
		if nodes==None or len(nodes)==0:		
			continue
				
		#print nodes
	
		# which hits held aside?
		asides=hitmap.get(sid)
		if asides == None:
			print >> sys.stderr, "Solution %d has None??" % sid
			return

		for a in asides:
			if a not in tallies:
				print >> sys.stderr, "Can't find the held-aside label %s from file %s. Do we have the right master label file? Check it out: %s" % (a, f, labelfn)
				return
			
			#if a not in tallies:
			#	tallies[a]={"in":[], "out":[]}
			if "'"+str(a)+"'" in nodes or a in nodes:
				tallies[a]["in"].append(sid)
			else:
				tallies[a]["out"].append(sid)
	
		# for non-interface, non-hits 
		# will updated totals at the end
		for a in other:
			#if a not in tallies:
			#	tallies[a]={"in":[], "out":[]}
			if "'"+str(a)+"'" in nodes or a in nodes:
				tallies[a]["in"].append(sid)
		totSols+=1
		countNodes += len(nodes)

	# total recall
	rec=0
	
	vals=[]	# so we can sort them
	for (t, smap) in tallies.items():
		status=0
		if t in totHideable:
			status=1
			fail=len(smap["out"])
	
		success=len(smap["in"])
		if status==0:
			fail=totSols-success	# for non-hits, fail count is all other sols

		prop=0
		if (success+fail) > 0:
			prop=float(success)/(success+fail)

		if prop > 0 and status==1:
			rec+=1
		
		#print "%s\t%d\t%d\t%d\t%f" % (t, status, success, fail, prop)
		# conf\tstatus\teid\tsuccess\tfail
		vals.append([prop, status, t, success, fail])

	print "# %d solutions found" % totSols
	print "# %d nodes ever recalled with conf > 0" % rec
	avgNodes = countNodes/float(totSols)
	print "# On average, %d active nodes per solution" % avgNodes

	# sort in decreasing order
	vals.sort(key=lambda x : -1*x[0])
	print "#conf\tlabel\tnode\tsols_containing\tsols_omitting\tnever_held_aside"
	for (prop,status,t,success,fail) in vals:
		# if never held aside, make a note!
		special=""
		if success+fail==0:
			special="\tnever_seen"
		print "%f\t%d\t%s\t%d\t%d%s" % (prop, status, t, success, fail, special)


if __name__=="__main__":
	sys.exit(main(sys.argv))



