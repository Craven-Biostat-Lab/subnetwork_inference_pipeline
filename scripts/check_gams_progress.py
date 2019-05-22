""" Checks progress of GAMS inference jobs. 
 Usage: python check_gams_progress.py topdir	addcount	[status_to_print]

If third argument, it's a status code. Prints out the jobs that
had that code.

Some special options for argument 2:
- "rm_incomplete" : the script will print out the commands needed to remove
log files, 225* directories, and lst files in the directories
containing jobs that are "in_progress", "in_presolve", "in_tree", or "error".
(Error includes infeasibility.)

- "clean_up" : script will print out the commands needed to remove the .lst and path set .gms file from successfully completed job directories.

- "verbose" : script will print ALL jobs with their status and most recent time.

"""


import sys
import glob
import os
import math

def main(argv):

	if len(argv) < 3:
		print "Usage: python check_gams_progress.py topdir	addcount	[status_to_print]"
		return 2
	
	# top directory
	topdir=argv[1]
	addcount=int(argv[2])

	# normal codes
	codes=("complete", "error", "in_progress", "in_presolve", "in_tree", "not_started", "multi_gdx", "multi_log")

	# print?
	pcode=None

	rmMode=False
	cleanMode=False	
	verbose=False
	
	if len(argv) > 3:
		pcode=argv[3]
		if pcode=="rm_incomplete":
			rmMode=True
		elif pcode=="clean_up":
			cleanMode=True
		elif pcode=="verbose":
			verbose=True
		elif pcode not in codes:
			print "Please request a code from (%s, rm_incomplete, clean_up, verbose)" % ", ".join(codes)
			return 2

	# sample dirs
	jobs=[d for d in os.listdir(topdir) if "sample" in d and os.path.isdir(os.path.join(topdir, d, "add_%d" % addcount))]
	# add the subdir
	jobs=[os.path.join(d, "add_%d" % addcount) for d in jobs ] 
	

	# report
	# { code : { job : info }}
	codemap=dict([ (c,{}) for c in codes ])

	for j in jobs:
		(status, etc)=check_job(os.path.join(topdir, j))
		codemap[status][j]=etc

	# avg time of complete jobs
	times={}
	for code in ["complete", "in_tree", "in_presolve", ("in_tree","in_presolve")]:
		times[code]=avg_time(code, codemap)
		
	# Print commands to erase intermediate files from incomplete/error jobs
	# (only use this when you know they aren't still running, obvy)	
	if rmMode:
		cleaned=False
		incomplete=[]		
		for c in ("in_progress", "in_presolve", "in_tree", "error"):
			incomplete = incomplete + codemap[c].keys()
		for j in incomplete:
			prefix = os.path.join(topdir, j)
			# check existence and print rm commands
			cmds = print_rm(prefix, ["*.log", "*.lst", "225*"])
			if len(cmds) > 0:
				print "\n".join(cmds)
				cleaned=True

		if not cleaned:
			print >> sys.stderr, "Nothing to clean up."

	elif cleanMode:
		cleaned=False
		# Clean up the .lst and hiv*moresets.gms from completed directories
		for j in codemap["complete"].keys():
			prefix = os.path.join(topdir, j)
			cmds = print_rm(prefix, ["*.lst", "hiv*moresets.gms"])
			if len(cmds) > 0:
				print "\n".join(cmds)
				cleaned=True
		if not cleaned:
			print >> sys.stderr, "Nothing to clean up."
		
	elif verbose:
		print "job\tstatus\tgdx_file\ttime"
		for s in codemap.keys():
			for (j, info) in codemap[s].items():
				gdx=""
				time=""
				err=False
				if isinstance(info, tuple) and len(info) == 2:
					# in progress or complete
					if info[0] != None:
						gdx=info[0]
					time="%g" % info[1]
							
				print "%s\t%s\t%s\t%s" % (j, s, gdx, time)

	elif pcode == None:
		for c in codes:
			print "%s\t%d" % (c, len(codemap[c]))
		print "# average time for completed jobs: %f hours" % times["complete"]
		print "# average time for currently running jobs: %f hours" % times[("in_tree","in_presolve")]
	else:
		if pcode in times.keys():
			print "# average time: for jobs with status %s: %f hours" % (pcode, times[pcode])
 
		for fn in codemap[pcode]:
			# is it a list or tuple?
			if isinstance(fn, basestring):
				print fn
			else:
				print "\t".join([str(x) for x in fn])	

#	complete=0	# gdx file exists
#	running=0	# 225* directory exists

def print_rm(prefix, rmsufs):
	"""
	Given a file path prefix and a list of suffices (rmsufs),
	checks for the existence/type of each prefix/suffix and
	prints either "rm X" ("rm -r X") to remove the
	existing files (directories).
	"""
	cmds=[]
	rmnames = [ glob.glob(os.path.join(prefix, x)) for x in rmsufs ]		
	for rmnL in rmnames:
		for rmn in rmnL:
			if os.path.isdir(rmn):
				cmds.append("rm -r %s" % rmn)
			elif os.path.isfile(rmn):
				cmds.append("rm %s" % rmn)

	return cmds

def avg_time(status, codemap):
	""" Get avg time of jobs with given status. One or more of 
	"complete", "in_tree", or "in_presolve" are fair game."""

	totTime=0
	ct=0

	stats=[]
	# do we have one or more status requests?
	if isinstance(status, basestring):
		stats=[status]
	else:
		stats=status

	for s in stats:
		if s not in codemap:
			continue
		for (fn,info) in codemap[s].items():
			# If incomplete, info contains (None, time)
			time=info
			# if complete, info contains GDX filename and time.
			if isinstance(info, tuple):
				time=info[1]
	
			if time==None:
				continue
			totTime+=time
			ct+=1.0
	avg=0

	if ct>0:
		avg=totTime/ct	

	return avg

def check_job(dirfn):
	"""
	Gets the status of a job
	Parameter is the directory name

	Returns: status codes, from:
		 complete, error, in_progress, not_started, multi_gdx, multi_log
	with optional second return value
	
	
	complete, (gdx_filename, time)
	multi_log or multi_gdx, [multiple gdx/log filenames found]
	error, [error lines]
	in_progress

	"""
	gdx_ls=glob.glob(os.path.join(dirfn, "*.gdx"))
	log_ls=glob.glob(os.path.join(dirfn, "*.log"))
	temp_ls=glob.glob(os.path.join(dirfn, "225*"))

	if len(log_ls)==0:
		return ("not_started", "")
		
	maybe_gdx=None
	if len(gdx_ls)==1:
		# get time from log file? 
		# possibly an old GDX or result from an error run, so only return this 
		# if no error.
		time=get_total_time(log_ls[0])
		if time != None:
			maybe_gdx = ("complete", (gdx_ls[0], time))
		
	elif len(gdx_ls)>1:
		return ("multi_gdx", gdx_ls)

	# if log exists - in progress, or error?
	non_error=None
	if len(log_ls)==1:
		(status, info)=check_log_status(log_ls[0])
		if status=="error":
			# info is lines containing error messages
			return ("error", info)
		else:
			# info is time elapsed so far
			non_error = (status, info)

	elif len(log_ls)>1:
		return ("multi_log", log_ls)
		
	# if maybe_gdx not None and no error, then it was complete.
	if maybe_gdx != None:
		return maybe_gdx
	elif non_error != None:
		return non_error
		
	
	# otherwise, assume in generic progress??
	if len(temp_ls)==1:
		return ("in_progress","")

	return ("not_started", "")

def get_total_time(fn):
	"""
	Gets total time from a log file from a completed job.
	Convert to hours.
	"""
	last = os.popen("tail -n 1 %s" % fn).read()
	#"Job run_sample_0.50_116_hits.gms Stop 04/30/14 23:47:37 elapsed 9:39:57.462"
	# hours:minutes:seconds.milliseconds
	sp=last.split("elapsed")
	if len(sp) < 2:
		#print fn, last
		return None

	sp=sp[1].strip()
	sp=sp.split(":")
	hrs=int(sp[0])
	for i in range(1, len(sp)):
		hrs += float(sp[i])/math.pow(60, i)
	return hrs	
		
def check_log_status(fn):	
	"""
	Gets stage info and most recent time information.
	If error, returns errors instead of time info.
	"""
	errs=[]
	stage="in_presolve"
	
	elapsed=""
	with open(fn) as f:
		for line in f:
			if "rror" in line:
				errs.append(line.strip())
			elif "Infeasibility row" in line:
				errs.append(line.strip())
			elif "Parallel mode:" in line:
				stage="in_tree"
			elif "Elapsed time =" in line:
				elapsed=line.strip()


	if len(errs) > 0:
		return ("error", errs)
	else:
		if elapsed != "":
			time=get_elapsed_time(elapsed)
		else:
			time=0
		# no gdx filename yet
		return (stage, (None, time))

def get_elapsed_time(line):
	"""
	Reads time from a time-indicating line. Convert to hours.
	Example: Elapsed time = 3402.43 sec. (140969.53 ticks, 100781 iterations)
	"""
	sp= line.strip().split()
	#print sp
	sec=float(sp[3])
	hr = sec/(60.0*60.0)
	return hr	


if __name__=="__main__":
	sys.exit(main(sys.argv))



