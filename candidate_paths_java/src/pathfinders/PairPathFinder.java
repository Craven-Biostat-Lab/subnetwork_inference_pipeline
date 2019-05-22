package pathfinders;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

import structures.Configuration;
import structures.Graph;
import structures.PairDirectory;
import structures.PairDirectory.PartialOrder;
import structures.Path;
import structures.PathManager;
import utilities.DebugTools;
import exceptions.InvalidValueException;

/**
 * Finds paths between pairs.
 * Option for iterative deepening.
 * @author chasman
 *
 */
public class PairPathFinder extends PathFinder {
	
	/*
	 * Source-target pairs
	 */
	protected PairDirectory stPairs;
	/*
	 * Search depth.
	 */
	protected int depth;
	
	public PairPathFinder(String name, PairDirectory index, int depth) {
		this.name = name;
		this.stPairs = index;
		this.depth = depth;
	}

	/*
	 * The basic PairPathFinder finds paths for the source-target pairs
	 * in the PairIndex. It stops searching immediately when an item in 
	 * the source's target set is located.
	 * 
	 * Any further restrictions (e.g., requirements for candidate TFs/RBPs)
	 * will be made in subclasses.
	 * @param 
	 * @param depth
	 * @return
	 */
	@Override
	public PathManager findPaths(Graph g) {
		PathManager found = new PathManager();
				
		// stop if depth==0
		if (depth==0) return found;

		// get the start nodes
		Set<String> startNodes = stPairs.getFirsts();
		// search for each start node
		for (String node : startNodes) {	
			if (!g.contains(node)) {
				if (DebugTools.DEBUG) System.out.println("Node not in graph: " + node);
				continue;		
			}

			PathManager npaths = this.findPaths(g, node, this.depth);

			if (DebugTools.DEBUG && npaths.size() > 0) {
				System.out.println(String.format("Found %d paths for starting node %s.", 
						npaths.size(), node));
			}

			// npaths is null if node not in graph
			if (npaths != null) found.addAll(npaths);			
		}
		
		return found;
	}
	
	/**
	 * Iteratively deepens search depth. 
	 * Stop search from each source when at least "stop"*targets reached,
	 * or depth+addDepth reached.
	 * @param g
	 * @param addDepth
	 * @param stop	fraction of required targets
	 * @return
	 */
	public PathManager findPathsIterative(Graph g, int addDepth, double stop) {
		PathManager found = new PathManager();
		
		// stop if depth==0
		if (depth==0) return found;

		// get the start nodes
		Set<String> startNodes = stPairs.getFirsts();
		// search for each start node
		for (String node : startNodes) {
			Set<String> targets = stPairs.getSeconds(node);
			// targets in graph?
			HashSet<String> tot = new HashSet<String>(g.nodes());
			tot.retainAll(targets);
			if (DebugTools.DEBUG) {
				System.out.format("%s has %d targets in graph \n", node, tot.size());
			}
			
 			
			if (!g.contains(node)) {
				if (DebugTools.DEBUG) System.out.println("Node not in graph: " + node);
				continue;		
			}

			// iterative deepening loop
			double cov=0.0;
			int atDepth=this.depth;
			
			PathManager npaths=null;
			while (cov < stop && atDepth < (this.depth+addDepth)) {
				npaths = this.findPaths(g, node, atDepth);
				if (DebugTools.DEBUG && npaths.size() > 0) {
					System.out.println(String.format("Found %d paths for starting node %s at depth %d.", 
							npaths.size(), node, atDepth));
				}
				// how many targets covered? allows targets as internal.
				
				int tfound=0;
				for (String t : targets) {
					if (npaths.contains(t)) {
						tfound++;
					}
				}				
				
				cov=((double) tfound) / targets.size();
				atDepth++;				
				
				
				if (DebugTools.DEBUG) {
					System.out.format("\tCovered %f (%d) of %d targets.\n", cov, tfound, targets.size());
					for (Path p : npaths.allPaths()) {
						System.out.println(p.toString());
					}
				}
			}			

			// npaths is null if node not in graph
			if (npaths != null) found.addAll(npaths);			
		}
		
		return found;
	}
	

	/**
	 * Path ends when we reach one of the source's targets
	 * or we run out of depth.
	 */
	@Override
	protected PathStatus verify(Path p, int depth) {
		// are first and final nodes a pair?
		String first = p.getNode(0);
		String last = p.getNode(-1);
		boolean isEndpoint = this.stPairs.getOrder(first, last)==PartialOrder.ABOVE;

		// yes! save and stop.
		if (isEndpoint) return PathStatus.SAVE_AND_STOP;

		// ran out of depth - stop.
		if (depth==0) return PathStatus.STOP;

		// keep going otherwise.
		return PathStatus.CONTINUE;		
	}
	
	/**
	 * Reads a pairpathfinder given a line and config.
	 * It takes a PairIndex object to designate start and endpoints.
	 * 5 is the depth.
	 * 
	 * PATHFINDER	name	PairPathFinder	pairIndex	5 
	 * 
	 * @param line
	 * @param config
	 * @return
	 */
	public static PairPathFinder readPathFinder(String[] line, Configuration config)
	throws InvalidValueException {
		String err = "";

		if (line.length < 5 || !line[2].equals("PairPathFinder")) {
			throw new InvalidValueException("Does not declare a PairPathFinder: " + Arrays.toString(line));
		}

		String name = line[1];
		
		PairDirectory pairs;
		int depth=0;

		pairs = config.getPairDirectory(line[3]);
		if (pairs==null) {
			err="Invalid PairDirectory: " + line[3];
		}

		try {
			depth = Integer.parseInt(line[4]);	
		} catch (NumberFormatException nfe) {
			err="Invalid depth:" + line[4];
		}		
		
		if (err.length() > 0 ) {
			throw new InvalidValueException(err);
		}

		return new PairPathFinder(name, pairs, depth);
	}
	
	
	public String toString() {	
		return String.format("PairPathFinder %s pairs=%s, depth=%d", 
				this.name, this.stPairs.filename(), this.depth);
	}

}
