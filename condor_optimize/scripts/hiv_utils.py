"""
Useful functions related to generating GAMS jobs for the HIV project
"""
import sys

def test():
	nums=[1,2,3,5,7,9,10,11,12,13,15]
	its=[ "a%d" % i for i in nums ] + [ "b%d" % i for i in nums ] + ["whee"]
	final = collapse_ids(its)
	print_gams_set("boop", "yay", its, cols=20)
	print_gams_set("boop(a,b,c)", "yay", [], collapse=False, cols=20)
	print_gams_set("boop(a)", "yay", [], collapse=False, cols=20)

	imap={ "t0":[ "a%d" % i for i in nums ], "t1":[ "b%d" % i for i in nums ], 
		"t2":[ "c%d" % i for i in range(0,100,2)]}
	print_gams_map("tuple(a,b)", "is a tuple", imap)
	print_gams_map("tuple(a,b)", "is a tuple", imap)
	
def read_master_labels(fn):
	"""
	Reads the master label file	
	Labels: hit, interface, hit|interface, unknown
	"""
	labels={}	# label : set()
	with open(fn) as f:
		for line in f:
			if "#" in line:
				continue
			sp=line.strip().split("\t")
			g=sp[0]
			l=sp[1]
			if l not in labels:
				labels[l]=set()
			labels[l].add(g)

	return labels

def read_master_pathfile(fn, hide=None, pos=[], def_pf="all"):
	"""
	Reads the master path file.
	If "aside" and "positions" provided, omits paths that contain an 'aside' node in one of the
	specified positions.
	For example, positions=[1,-2] corresponds to omitting held-aside hits and interfaces.

	Input format:
	pid	nodes	edges
	p33	E6709|E9374|E7284|E155871       edge34216|edge1385|edge85594	pathfinder
	
	Allows default pathfinder to be specified under "def_pf" if the file doesn't contain
	that column.

	Returns:
	({pathfinder : { p : {"nodes":(), "edges"=()}} , total_paths_from_orig_file)
	"""
	paths={} # {pathfinder :	{ p : {"nodes":(), "edges"=() } } }
	tot=0
	with open(fn) as f:
		for line in f:
			if "#" in line:
				continue
			sp=line.strip().split("\t")
			pid=sp[0]
			tot+=1
			nodes=tuple(sp[1].split("|"))
			edges=tuple(sp[2].split("|"))
			
			if len(sp) < 4:
				finder=def_pf
			else:
				finder=sp[3]

			if hide != None:
				skip=False
				for p in pos:
					if nodes[p] in hide:
						skip=True
						#print sp
						#print "\t%s found hidden node %s in position %d" % (pid, nodes[p], p)
						break				 
				if skip:
					continue

			if finder not in paths:
				paths[finder]={}
			paths[finder][pid]={"nodes":nodes, "edges":edges}	

	return (paths,tot)

def read_master_subgraph_file_by_paths(fn):
	"""
	Reads a master subgraph file, keeping the path structure.
	{ subgraph : { pid : {nodes, edges} }
	"""
	subgraphs={}

	with open(fn) as f:
		for line in f:
			if "#" in line:
				continue
			sp=line.strip().split("\t")
			pid=sp[0]
			edges=tuple(sp[1].split("|"))			
			nodes=tuple(sp[2].split("|"))
			subs=tuple(sp[3].split("|"))

			# store info
			for s in subs:
				if s not in subgraphs:
					subgraphs[s]={}
				if pid not in subgraphs[s]:
					subgraphs[s][pid]={}
				for (name, items) in [("nodes",nodes), ("edges",edges)]:
					if name not in subgraphs[s][pid]:
						subgraphs[s][pid][name]=set()
					subgraphs[s][pid][name] = set.union(subgraphs[s][pid][name], items)
	return subgraphs

def read_master_subgraph_file(fn, paths=None):
	"""
	Reads subgraph nodes and edges from the master file.
	If 'paths' submitted, returns only those nodes/edges
	that are brought in by the requested paths.
	Otherwise, returns all.

	Input format:
	pid	edges	nodes	subgraphs
	p1000068        edge54156       E23327|E155030  sub0

	Output format:
	{ subgraph : {"nodes":set(), "edges":set()} }
	"""
	subgraphs={}

	with open(fn) as f:
		for line in f:
			if "#" in line:
				continue
			sp=line.strip().split("\t")
			pid=sp[0]
			edges=tuple(sp[1].split("|"))			
			nodes=tuple(sp[2].split("|"))
			subs=tuple(sp[3].split("|"))

			# if paths provided, skip if not in requested path set
			if paths != None and pid not in paths:
				continue
						
			# store info
			for s in subs:
				if s not in subgraphs:
					subgraphs[s]={"nodes":set(), "edges":set()}
				for (name, items) in [("nodes",nodes), ("edges",edges)]:
					subgraphs[s][name] = set.union(subgraphs[s][name], items)
	return subgraphs

def print_gams_set(name, description, items, collapse=True, cols=80, out=sys.stdout):
	""" Prints a set or list of SINGLE items into GAMS set format. 
	Cols gives us a soft maximum of characters per line.
	By default, collapses item set for us.
	By default, prints to stdout.
	"""
	tol=5	# tolerance on line width
	out.write("Set %s \"%s (%d)\" \n/" % (name, description, len(items)))

	# check empty
	if len(items)==0:
		# how many nulls? 1+ number of commas in set name
		sp=name.split(",")
		nulls = "%s" % (".".join( ["null"]*len(sp)))
		out.write("%s /;\n" % nulls)
		return		

	# not empty? OK!
	if collapse:
		its = collapse_ids(items)
	else:
		its = items

	curline = its[0]
	for i in its[1:]:
		# if space, add to the end of the current line
		if len(curline) < (cols-tol):
			curline = "%s, %s" % (curline, i)
		# otherwise, print current line and start anew
		else:
			out.write("%s,\n" % curline)
			curline=i
	out.write("%s /;\n" % curline)

def print_gams_map(name, description, itemmap, collapse=True, cols=80, out=sys.stdout):
	"""
	Prints a map { a : iterable(b) } into a GAMS set with tuple format
	a.(b0, ... , bN)
	Collapses within parens by default.
	"""
	tol=5	# tolerance on line width
	out.write("Set %s \"%s (%d) \" \n/ " % (name, description, len(itemmap)))

	# check empty
	if len(itemmap)==0:
		# how many nulls? 1+ number of commas in set name
		sp=name.split(",")
		nulls = "%s" % (".".join( ["null"]*len(sp)))
		out.write("%s /;\n" % nulls)
		return		

	# print: a.(b0, ... )
	alist = itemmap.keys()
	for j in range(0, len(alist)):
		a=alist[j]	
		bset=itemmap[a]

		bits=list(bset)
		if collapse:
			bits=collapse_ids(bset)
	
		curline = "%s.(%s" % (a, bits[0])
		for i in bits[1:]:
			# if space, add to the end of the current line
			if len(curline) < (cols-tol):
				curline = "%s, %s" % (curline, i)
			# otherwise, print current line and start anew
			else:
				out.write("%s,\n" % curline)
				curline=i

		comma=""
		if j<len(alist)-1:
			comma=", "
		# avoid double space by writing to stdout
		out.write("%s)%s" % (curline, comma))	

	out.write("/;\n")

def collapse_ids(items):
	"""
	Given a set of items with numbers (e.g., edge9, edge10, edge11, edge30, edge3012),
	collapses items with consecutive numbers:
	(edge9*edge11, edge30, edge3012)
	"""		
	import re
	final=[]

	# split into (letterstring, integer)
	pat=re.compile(r"^([A-Za-z]+)(\d+)$")
	bypref = {}	# { prefix : [ints] }
	for i in items:
		m = pat.match(i)
		# if no match, add as a single item
		if m == None:
			final.append(i)
			continue
		(pref, num) = m.groups()
		if pref not in bypref:	
			bypref[pref]=[]
		bypref[pref].append(int(num))
	
	for (pref, vals) in bypref.items():
		srt = sorted(vals)		
		# divide into sub-lists of consecutive, increasing values
		consecutive=divide_ints(srt)
		merged=merge_ints(pref, consecutive)
		final.extend(merged)
	return final

def merge_ints(pref, consec):
	""" Takes a list of consecutive sub-lists of values, merges into 
	a single list in which prefix is applied to the beginning of each
	value and consecuctive sub-lists of > 2 items are merged."""
	merged=[]
	for sub in consec:
		if len(sub) < 3:
			merged.extend([ "%s%d" % (pref, i) for i in sub ])
		else:
			merged.append( "%s%d*%s%d" % (pref, sub[0], pref, sub[-1]))
	return merged
	
		
def divide_ints(vals):
	"""
	Given a *sorted* list of integer values, divide into
	consecutive sub-lists.
	"""
	consec=[]	# master list of lists
	buffy=[vals[0]]	# current sub-list
	for v in vals[1:]:	
		# not consecutive? save the current list and start anew.
		if v > (buffy[-1] + 1):
			consec.append(list(buffy))
			buffy=[]
		buffy.append(v)
	consec.append(list(buffy))

	return consec

def get_nodes(fn):
	""" Gets set of relevant nodes from a dumped info file."""
	nodes=set()
	with open(fn) as f:
		for line in f:
			if "#" == line[0]:
				continue
			sp=line.strip().split("\t")
			# move down to the y-variable portion - nodes
			if sp[0] != "y":
				continue
			n=sp[1].replace('"',"")	
			# ERROR NODE
			if "GDX file" in n:
				return None
			nodes.add(n)
	return nodes

def read_hitmap(fn, sol=None):
	"""
	Reads held-aside hits by solution ID
	solID\tcount_aside\tgene1|gene2|...

	If "sol" not provided, get all solutions.
	If sol is integer valued, get just that solution.

	"""
	
	allhits=set()
	hitmap={} # {sol : hits}
	with open(fn) as f:
		for line in f:
			if "#" == line[0]:
				continue
			sp=line.strip().split("\t")
			sid=int(sp[0])
				
			# if specific solution requested, just skip others
			if sol != None and sol != sid:
				continue

			if len(sp) > 2:
				hits=sp[2].split("|")
			else:
				hits=[]
			hitmap[sid]=set(hits)
			# keep track of number of hits
			allhits = set.union(allhits, hits)
			#print sid, hitmap[sid]

	return (hitmap, allhits)


def read_labels(fn):	
	""" reads labeled nodes from tab file"""
	nodes={}
	with open(fn) as f:
		for line in f:
			if "#" == line[0]:
				continue
			sp=line.strip().split("\t")
			nodes[sp[0]]=sp[1]
	return nodes

def read_set(fn):
	"""
	Reads nodes from file. node in first column.
	"""
	ints=set()
	with open(fn) as f:
		for line in f:
			if "#" == line[0]:
				continue
			sp=line.strip().split("\t")
			ints.add(sp[0])
	return ints


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
	

# tester
if __name__=="__main__":
	sys.exit(test())
