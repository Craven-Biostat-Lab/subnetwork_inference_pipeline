"""
Collects the variable info in a directory of dumped gdx files and 
produces three files: path confidence, node confidence, and edge confidence.
"""
import sys
import glob

# argv 1: pattern for matching dump files; eg: path_sol*dump
ls = glob.glob(sys.argv[1])

outpref = sys.argv[2]
print "Writing confs to files with prefix %s" % outpref

# number of times we see a path
paths={}
nodes={}
edges={}
gomap = {"sigma":paths, "x":edges, "y":nodes}

tot=0
for fn in ls:
	#print "#", fn
	bad=False
	
	seen=set()
	with open(fn) as f:
		for line in f:
			# didn't work
			if "Symbol not found" in line:
				print >> sys.stderr, "Bad file: %s" % fn
				bad=True
				break
			
			# var\t"name"\tsetting
			sp=line.strip().split("\t")
			symbol = sp[1][1:-1]

			if symbol in seen:
				continue
			try:
				setting = int(sp[2])		
			except IndexError, ValueError:
				print >> sys.stderr, "Bad format", fn, sp
				bad=True
				break

			themap = gomap[sp[0]]
			themap[symbol] = themap.get(symbol,0)+1
		if not bad:
			tot+=1

print "# %d total solutions" % tot

total=float(tot)

for var in gomap.keys():
	with open("%s_%s.tab" % (outpref, var), "w") as f:
		f.write("#item\tconf(%s)\n" % var)
		for (s, count) in gomap[var].items():
			f.write("%s\t%f\n" % (s, count/total))
			if (count/total) > 1:
				print >> sys.stderr, "Too many entries per symbol in your dump files. (%s, %d, %d)" % (s, count, total)
				sys.exit()




