package apps;

import java.io.File;
import java.io.IOException;
import java.io.PrintStream;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map.Entry;
import java.util.Set;

import pathfinders.PathFinder;
import structures.Configuration;
import structures.Edge;
import structures.EdgeLibrary;
import structures.Graph;
import structures.NodeLibrary;
import structures.Path;
import structures.PathManager;
import structures.Subgraph;
import utilities.CytoscapePrinter;
import utilities.GamsPrinter;
import utilities.GamsPrinter.LabelMode;
import utilities.GraphUtils;
import utilities.StringUtils;

/**
 * Prepared to demonstrate how to use this code to find paths!
 * First argument is the config filename.
 * 
 * Usage:
 * java	SearchTester config_filename
 * 
 * This application will:
 * -Read in a config file for a  
 * -
 * @author chasman
 *
 */
public class HIVMain {

	public static boolean DO_PATHFINDING=true;

	public static void main(String[] args) {

		Configuration config = null;
		Graph g = null;

		try {
			config = Configuration.readConfigFile(args[0]);
			g = config.buildGraph();	// has any FILTER_GRAPH 
		} catch (Exception e) {
			System.out.println(e.getMessage());
			e.printStackTrace();
			return;
		}

		// remove self loops and edgeless nodes
		g = g.removeSelfLoops();
		g = g.removeEdgeless();


		NodeLibrary libe = config.nodeLibrary();
		EdgeLibrary elibe = config.edgeLibrary();
		// Print summary of node and edge features
		System.out.println(libe.toString());
		System.out.println(elibe.toString());

		System.out.format("Read graph with %d nodes and %d edges " +
				"(after any node-based filtering specified in config).\n", g.nodes().size(), g.edges().size());

		// also make background without HIV and without complexes
		Graph hostOnly = g.copy();
		Set<String> hiv_genes = libe.get(libe.getFeature("hiv_genes"));
		for (String s : hiv_genes) {
			hostOnly.remove(s);
		}
		for (String s : libe.get(libe.getFeature("complex"))) {
			hostOnly.remove(s);
		}
		hostOnly = hostOnly.removeEdgeless();

		System.out.format("Background network consisting of only host proteins (not complexes, not HIV) contains %d connected nodes and %d edges.\n",
				hiv_genes.size(), hostOnly.nodes().size(), hostOnly.edges().size());

		// how many are directed?
		int dir=0;
		for (Edge e : g.edges()) {
			if (e.isDirected()) dir++;
		}
		System.out.format("Graph has %d directed edges.\n", dir); 

		System.out.format("Auto-filtered to graph with %d nodes and %d edges.\n", g.nodes().size(), g.edges().size());

		Set<String> interfaces = GraphUtils.request(g, libe, libe.getFeature("pinterface")),
				hits = GraphUtils.request(g, libe, libe.getFeature("rnai"));
		// seeds - accepted by filter manager
		//NodeFilterManager seedMan = config.nodeFilterManagers().get("seed_manager");
		//Graph seedG = seedMan.filter(g);

		System.out.format("\tGraph has %d hits, %d interfaces.\n", hits.size(), interfaces.size());


		// Run through the pathfinders
		ArrayList<PathFinder> pfs = config.pathFinders();
		PathManager paths = new PathManager();

		Graph gPaths=null;
		// Save all the paths into this PathManager
		// find paths?
		if (DO_PATHFINDING) {
			try {
				for (PathFinder pf : pfs) {
					PathManager found = pf.findPaths(g);
					System.out.format("Applied %s: %d paths\n", pf.toString(), found.size());
					paths.addAll(found);
				}
				System.out.format("Total: %d paths\n", paths.size());

			} catch (Exception e) {
				System.err.println(e.getMessage());
				e.printStackTrace();
			}

			gPaths = PathManager.makeGraph(paths);
			// add the subgraphs
			for (Subgraph sg : config.subgraphs().values()) {
				// screen edges
				Collection<Edge> edges = 
						PathManager.filterEdges(paths, sg.edges(), 
								config.subgraphAddModes().get(sg.name()));
				gPaths.addAll(edges);
			}

			System.out.format("Paths and subgraphs contain %d nodes and %d edges.\n", gPaths.nodes().size(), gPaths.edges().size());
		}

		// how many hits/interfaces remain?

		interfaces = GraphUtils.request(gPaths, libe, libe.getFeature("pinterface"));
		hits = GraphUtils.request(gPaths, libe, libe.getFeature("rnai"));

		System.out.format("\tPaths contain %d hits, %d interfaces.\n", hits.size(), interfaces.size());

		//		try {
		//			for (PathFinder pf : pfs) {
		//				PathManager found = pf.findPaths(g);	
		//							
		//				System.out.format("Applied pathfinder %s: found %d paths\n", pf.toString(), found.size());
		//				
		//				if (found != null) paths.addAll(found);
		//			}
		//			System.out.format("Total found: %d paths\n", paths.size());
		//
		//		} catch (Exception e) {
		//			System.err.println(e.getMessage());
		//			e.printStackTrace();
		//		}

		// Cytoscape printing - do I strip non-alphanumeric characters from node names?
		boolean cleanMode=(config.getGamsLabelMode()==LabelMode.STRIP);
		
		if (DO_PATHFINDING)
			CytoscapePrinter.printSif(gPaths, String.format("%s_paths.sif", config.getOutputPrefix()), cleanMode);

		CytoscapePrinter.printSif(g, String.format("%s_background.sif", config.getOutputPrefix()), cleanMode);		

		CytoscapePrinter.printSif(hostOnly, String.format("%s_background_no_hiv_cx.sif", config.getOutputPrefix()), cleanMode);

		CytoscapePrinter.printNodeFeatures(libe, String.format("%s_node_feats.tab", config.getOutputPrefix()), cleanMode);
		CytoscapePrinter.printEdgeFeatures(config.edgeLibrary(), String.format("%s_edge_feats.tab", config.getOutputPrefix()), cleanMode);

		System.out.println("Wrote Cytoscape files: " + config.getOutputPrefix());

		GamsPrinter printer = new GamsPrinter(g, paths, 
				config.nodeLibrary(), config.edgeLibrary(), config.subgraphs());

		// print unique edge IDs
		boolean cytoV3Format=false;	// Should attribute be tab-delimited file
		// for Cytoscape v.3+, or formatted for
		// Cytoscape v.<3?
		CytoscapePrinter.printEdgeAttribute("gamsId", printer.getEdgeIDs(), 
				String.format("%s_gamsId.edge", config.getOutputPrefix()), cytoV3Format, cleanMode);

		// print the base GAMS file - everything that isn't path related!
		String gamsPref = config.getGamsFileName();
		if (gamsPref == null || gamsPref.equals("System.out")) {
			System.err.println("Sorry, stdout is not an option for printing. Please specify a GAMS file prefix.");
			return;
		}

		// Print one master file: everything that isn't path related.
		String masterFn = String.format("%s_master.gms", gamsPref);
		// open new output file
		PrintStream gamsStream=null;
		try {
			gamsStream = new PrintStream(new File(masterFn));
			System.out.println("Opened new master gams file " + masterFn);
		} catch (IOException ioe) {
			System.err.println("Unable to print master gams file to " + masterFn);
		}
		printer.printNodeSets(gamsStream);

		// edge features - only organism and edge type
		String[] efeats = new String[] {"organism", "etype"};
		printer.printEdgeSets(gamsStream, efeats, false);		

		// Now, print all paths into a different file...
		// Print one master file: everything that isn't path related.
		String pathFn = String.format("%s_master_paths.tab", gamsPref);
		// open new output file
		PrintStream pathStream=null;
		try {
			pathStream = new PrintStream(new File(pathFn));
			System.out.println("Opened new master path file " + pathFn);
		} catch (IOException ioe) {
			System.err.println("Unable to print master path file to " + pathFn);
		}

		// print a special tab-delim format for paths:
		// pid	start	end	node|..| edge|...|
		printPathAssociationFile(config, paths, printer, pathStream);


		// print special file for subgraph edges by paths
		String subFn = String.format("%s_master_subgraphs.tab", gamsPref);
		// open new output file
		PrintStream subStream=null;
		try {
			subStream = new PrintStream(new File(subFn));
			System.out.println("Opened new master subgraph file " + subFn);
		} catch (IOException ioe) {
			System.err.println("Unable to print master subgraph file to " + subFn);
		}
		printSubgraphFile(config, paths, printer, subStream);
	}

	/**
	 * Prints out a master file associating paths with their nodes, edges,
	 * start point, and end point.
	 * Later, we can go through this file and pick out the paths relevant to 
	 * each solution.
	 * 
	 * pid	node|... edge|...	
	 * 
	 * @param config
	 * @param paths
	 * @param printer
	 * @param outStream
	 */
	protected static void printPathAssociationFile(Configuration config, PathManager paths,
			GamsPrinter printer, PrintStream outStream) {
		//outStream.format("#pid\tstart\tend\tgene_ids\teids\n");
		outStream.format("#pid\tgene_ids\teids\n");
		for (Path p : paths.allPaths()) {
			String pid = printer.gamsify(p);
			//String start = p.getNode(0), end=p.getNode(-1);
			ArrayList<String> elist = printer.gamsifyList(p.edges());
			ArrayList<String> nlist = printer.gamsifyList(p.nodes());
			//ArrayList<String> slist = printer.gamsifyList(paths.getLabels(p));
			outStream.format("%s\t%s\t%s\n", pid, 								// NO LONGER PRINT start, end, 
					StringUtils.join(nlist,"|"), StringUtils.join(elist,"|")); //, StringUtils.join(slist,"|"));
		}
	}

	/**
	 * Prints out a file associating paths with the external subgraph
	 * edges that they bring in:
	 * pathID	edge1|...	node1|...	subgraph1|...
	 * 
	 * Externally we'll use this to pick out the subnode and subedge 
	 * sets for kept paths.
	 */
	protected static void printSubgraphFile(Configuration config, PathManager paths, 
			GamsPrinter printer, PrintStream outStream) {

		// want: pathID -> edges, nodes, subgraphs		
		HashMap<String, HashSet<String>> subgraphEdges = new HashMap<String, HashSet<String>>();
		HashMap<String, HashSet<String>> subgraphNodes = new HashMap<String, HashSet<String>>();
		HashMap<String, HashSet<String>> subgraphs = new HashMap<String, HashSet<String>>();

		// over subgraphs first
		for (Subgraph sg : config.subgraphs().values()) {
			HashMap<Path, HashSet<Edge>> sedge 
			= PathManager.filterSubgraphEdgesByPath(paths, sg.edges(), 
					config.subgraphAddModes().get(sg.name()));
			// save string for paths
			for (Path p : sedge.keySet()) {
				String pid = printer.gamsify(p);
				if (!subgraphs.containsKey(pid)) {
					subgraphs.put(pid, new HashSet<String>());
				}
				subgraphs.get(pid).add(sg.name());
			}

			// save edges and nodes
			for (Entry<Path, HashSet<Edge>> entry : sedge.entrySet()) {	
				Path p = entry.getKey();
				String pid = printer.gamsify(p);
				for (Edge e : entry.getValue()) {
					if (!subgraphEdges.containsKey(pid) || !subgraphNodes.containsKey(pid)) {
						subgraphEdges.put(pid, new HashSet<String>());
						subgraphNodes.put(pid, new HashSet<String>());
					}
					if (e==null) {
						System.err.format("Null edge %s for path %s (pid %s)?\n", e, p, pid );
					}
					// something wrong here - NullPointer with gamsify?
					subgraphEdges.get(pid).add(printer.gamsify(e));					
					subgraphNodes.get(pid).addAll(printer.gamsifySet(e.nodes()));
				}
			}
		}

		// Now print the tuples 
		ArrayList<String> pids = new ArrayList<String>(subgraphs.keySet());
		Collections.sort(pids);
		outStream.format("#pid\teids\tgene_ids\tsubgraphs\n");
		for (String pid : pids) {
			String eids = StringUtils.join(subgraphEdges.get(pid), "|");
			String nids = StringUtils.join(subgraphNodes.get(pid), "|");
			String sids = StringUtils.join(subgraphs.get(pid), "|");
			outStream.format("%s\t%s\t%s\t%s\n", pid, eids, nids, sids);
		}
	}

}
