package pathfinders;

import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Set;

import structures.Configuration;
import structures.Graph;
import structures.Graph.RType;
import structures.PairDirectory;
import structures.PathManager;
import structures.PairDirectory.PartialOrder;
import structures.Path;
import utilities.DebugTools;
import exceptions.InvalidValueException;
import filters.EdgeFilterManager;

/**
 * The SourceRegTargetPathFinder
 * finds paths between sources and targets in which the PENULTIMATE
 * node is a candidate downstream regulator for the source.
 * The final interaction can be any interaction.
 * 
 * @author chasman
 *
 */
public class SourceRegTargetPathFinder extends PairPathFinder {

	/*
	 * This kind of pathfinder will produce a BranchyPath
	 * when a sets of multiple paths differ ONLY in the last edge.
	 */
	{
		this.collapseMode = CollapseMode.ALL_BUT_LAST;
	}
	
	/*
	 * Requires that first and penultimate nodes have an ordered pair.
	 * (example: last interaction MUST be between candidate regulator
	 * and target.)
	 */
	protected PairDirectory penultimateFilter;	

	/*
	 * Allow only a limited number of edges with a particular type.
	 * (example: only allow one RNA binding protein -> Expressed Protein edge 
	 */
	protected HashMap<EdgeFilterManager, Integer> typeLimiter;


	public SourceRegTargetPathFinder(String name, 
			PairDirectory stPairs, PairDirectory candRegs, int depth) {
		super(name, stPairs, depth);
		this.penultimateFilter = candRegs;
	}
	
	/**
	 * Stops when "stop" fraction of penultimate nodes reached, or maximum depth.
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
			HashSet<String> totT = new HashSet<String>(g.nodes());
			totT.retainAll(targets);
			System.out.format("%s has %d targets in graph \n", node, totT.size());
			
			// candidate tfs/rbps
			Set<String> cands = penultimateFilter.getSeconds(node);
			
			HashSet<String> totR = new HashSet<String>();
			// in graph?
			for (String c : cands) {
				int deg = g.degree(node, RType.INCOMING) + g.degree(node, RType.UNDIRECTED);
				if (deg > 0) totR.add(c);
			}
			
			System.out.format("%s has %d candidate TFs/RBPs in graph \n", node, totR.size());
			
 			
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
				// how many targets and TFs/RBPs covered? 
				
				int tfound=0;
				for (String t : targets) {
					if (npaths.contains(t)) {
						tfound++;
					}
				}	
				HashSet<String> used = new HashSet<String>();
				for (Path p : npaths.allPaths()) {
					used.add(p.getNode(-2));
				}
				
				cov=((double) used.size()) / totR.size();
				double tcov = ((double) tfound) / targets.size();
				atDepth++;				
				System.out.format("\tCovered %f (%d) of %d candidate TFs/RBPs; %f (%d) targets.\n", 
						cov, used.size(), totR.size(), 
						tcov, tfound, targets.size());
				
				
			}			

			// npaths is null if node not in graph
			if (npaths != null) found.addAll(npaths);			
		}
		
		return found;
	}


	/**
	 * Path ends when we reach one of the source's targets
	 * VIA an approved candidate regulator for the source,
	 * or we run out of depth.
	 * 
	 */
	@Override
	protected PathStatus verify(Path p, int depth) {
			
		// does it pass the super-class? (ie, are first and last in a pair?)
		PathStatus pairVerify = super.verify(p, depth);
		if (pairVerify == PathStatus.SAVE_AND_STOP) {
			// are first and penultimate nodes a candidate source-regulator pair?
			String first = p.getNode(0);
			String penultimate = p.getNode(-2);
			// accept if source-reg pair -- the second test is for cases
			// where the source IS the reg
			boolean isRegPair = 
				(this.penultimateFilter.getOrder(first, penultimate)==PartialOrder.ABOVE)
				|| (first.equals(penultimate) && this.penultimateFilter.hasSelfPair(first));

			// yes! save and stop.
			if (isRegPair) return PathStatus.SAVE_AND_STOP;
			else return PathStatus.STOP;
		}

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

		if (line.length < 6 || !line[2].equals("SourceRegTargetPathFinder")) {
			throw new InvalidValueException("Does not declare a SourceRegTargetPathFinder: " + Arrays.toString(line));
		}

		String name = line[1];

		PairDirectory pairs, regs;
		int depth=0;

		pairs = config.getPairDirectory(line[3]);
		if (pairs==null) {
			err="Invalid source-target PairDirectory: " + line[3];
		}

		regs = config.getPairDirectory(line[4]);
		if (regs==null) {
			err="Invalid source-regulator PairDirectory: " + line[4];
		}

		try {
			depth = Integer.parseInt(line[5]);	
		} catch (NumberFormatException nfe) {
			err="Invalid depth:" + line[5];
		}		

		if (err.length() > 0 ) {
			throw new InvalidValueException(err);
		}

		return new SourceRegTargetPathFinder(name, pairs, regs, depth);
	}

}
