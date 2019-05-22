package structures;

import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Set;

public abstract class Library<T> {	
	
	/*
	 * Each implementation should fill this in appropriately.
	 */
	protected static final String CONTENT_TYPE="Abstract";

	/*
	 * We can look up the values stored for each item.
	 */
	protected HashMap<T, HashMap<Feature, Value>> featMap;

	/*
	 * Or the items for each feature value.
	 */
	protected HashMap<Feature, HashMap<Value, HashSet<T>>> backMap;

	/*
	 * The features we have in here.
	 */
	protected HashSet<Feature> features;

	/*
	 * Retrieve features by name.
	 */
	protected HashMap<String, Feature> featureNames;	

	protected Library() {
		this.featMap=new HashMap<T, HashMap<Feature, Value>>();
		this.backMap=new HashMap<Feature, HashMap<Value, HashSet<T>>>();
		this.features=new HashSet<Feature>();
		this.featureNames=new HashMap<String, Feature>();
	}

	/**
	 * Adds a feature and its item values to this library. 
	 * Returns "true" if successful and "false" if this feature already exists.
	 * 
	 * 
	 * @param feature
	 * @param values
	 * @return
	 */
	public boolean addValues(Feature feature, Map<T, Value> values) {
		if (this.hasFeature(feature)) return false;
		boolean canAdd = this.addFeature(feature);

		if (!canAdd) return false;

		HashMap<Value, HashSet<T>> subBack = this.backMap.get(feature);

		for (Entry<T, Value> entry : values.entrySet()) {
			T item=entry.getKey();
			Value val = entry.getValue();
			if (!featMap.containsKey(item)) featMap.put(item, new HashMap<Feature, Value>());

			// I think this would only happen if the features list got out of sync 
			assert(!hasFeature(item,feature)) : "Duplicate feature value."; 
			featMap.get(item).put(feature, val);

			// for set-valued features, we want to be able to use either the
			// combination of or any of the individual values to retrieve the items
			if (val instanceof CatSet) {
				CatSet cats = (CatSet) val;
				for (Value v : cats.getValue()) {
					if (!subBack.containsKey(v)) {
						subBack.put(v, new HashSet<T>());
					}
					subBack.get(v).add(item);
				}
			} else {
				// for continuous values, value wouldn't necessarily already
				// be in the subBack.
				if (!subBack.containsKey(val)) {
					subBack.put(val, new HashSet<T>());
				}
				subBack.get(val).add(item);
			}
		}
		return true;
	}
	
	
	
	/**
	 * Get the type of thing that is stored in this library.
	 * @return
	 */
	protected abstract String getContentType();

	/**
	 * Summarize the features in the library.
	 * @return
	 */
	public String toString() {
		StringBuilder sb = new StringBuilder(String.format("%s Library: ", this.getContentType()));
		sb.append(String.format("%d feature(s) covering %d %s(s)", this.features.size(), this.featMap.size(), this.getContentType().toLowerCase()));
		for (Feature f : this.features) {
			sb.append(String.format("\n\t%s\t%d %s(s)", f.toString(), this.get(f).size(), this.getContentType().toLowerCase()));
		}		
		return sb.toString();
	}

	
	/**
	 * Summarize the features for a given set of items.
	 * @param items
	 * @return
	 */
	public String summarize(Set<T> items) {
		StringBuilder sb = new StringBuilder(String.format("Summarizing features from %d %ss:", items.size(), this.getContentType().toLowerCase()));

		for (Feature f : this.features) {
			HashSet<T> intersect = new HashSet<T>(this.get(f));
			int orig=intersect.size();
			intersect.retainAll(items);
			sb.append(String.format("\n\t%s\t%d / %d %s(s)", f.toString(), intersect.size(), orig, this.getContentType().toLowerCase()));
		}
		
		return sb.toString();
	}

	/*
	 * Number of items in the library.
	 * @return
	 */
	public int size() {
		return this.featMap.size();
	}
	/**
	 * Gets a feature by name.
	 * @param name
	 * @return
	 */
	public Feature getFeature(String name) {
		return this.featureNames.get(name);
	}

	/**
	 * Gets the set of all features in the library (unmodifiable).
	 * @return
	 */
	public Set<Feature> getFeatures() {
		return Collections.unmodifiableSet(this.backMap.keySet());
	}

	/**
	 * Gets the features for an edge.
	 * @param e	edge
	 * @return	unmodifiable feature map, or null if no edge present.
	 */
	/**
	 * Gets the features for a item.
	 * @param e	edge
	 * @return	unmodifiable feature map, or null if no edge present.
	 */
	public Map<Feature, Value> getFeatures(T n) {
		if (this.featMap.containsKey(n)) {
			return Collections.unmodifiableMap(this.featMap.get(n));
		} else {
			return null;
		}
	}

	public Set<T> items() {
		return Collections.unmodifiableSet(this.featMap.keySet());
	}

	public boolean contains(T item) {
		return this.featMap.containsKey(item);
	}

	public boolean hasFeature(Feature feat) {
		return this.features.contains(feat);
	}

	public boolean hasFeature(T item, Feature feat) {
		return (this.features.contains(feat) && 
				featMap.containsKey(item) && featMap.get(item).containsKey(feat));
	}

	public Set<Feature> features() {
		return Collections.unmodifiableSet(this.features);
	}
	
	public Set<String> featureNames() {
		return Collections.unmodifiableSet(this.featureNames.keySet());
	}

	/**
	 * Get the value for a item for a feature
	 * @param item
	 * @param feat
	 */
	public Value getValue(T item, Feature feat) {
		if (this.hasFeature(item, feat)) 
			return featMap.get(item).get(feat);
		else return null;
	}

	/**
	 * Gets the items that have a particular feature,
	 * or null if feature not here.
	 * @return
	 */
	public Set<T> get(Feature f) {
		if (!this.hasFeature(f)) return null;
		HashMap<Value, HashSet<T>> items = this.backMap.get(f);
		HashSet<T> got = new HashSet<T>();
		for (HashSet<T> set : items.values()) {
			got.addAll(set);
		}
		return got;
	}

	/**
	 * Gets the items that have this value.
	 * For CatSet values, get any item that intersects with the requested value(s).
	 * @param f
	 * @param v
	 * @return
	 */
	public Set<T> get(Feature f, Value v) {
		if (!this.hasFeature(f)) return null;
		HashMap<Value, HashSet<T>> items = this.backMap.get(f);
		if (items==null || v==null) {
			return null;
		}
		// for discrete or continuous, this is easy. but for categorical sets, it's a little trickier...
		if (!(v instanceof CatSet)) 
			return Collections.unmodifiableSet(items.get(v));
		else {
			HashSet<T> rets = new HashSet<T>();
			CatSet c = (CatSet) v;
			for (Value subv : c.getValue()) {
				rets.addAll(items.get(subv));
			}
			return Collections.unmodifiableSet(rets);
		}
	}

	/**
	 * Adds a feature to the necessary internal structures.
	 * @param feature
	 * @return
	 */
	protected boolean addFeature(Feature feature) {
		boolean ok = this.features.add(feature);		
		if (!ok) return false;

		this.featureNames.put(feature.name(), feature);

		this.backMap.put(feature, new HashMap<Value, HashSet<T>>());
		Value[] vs = feature.values();
		for (Value v : vs) {
			this.backMap.get(feature).put(v, new HashSet<T>());
		}

		return true;
	}

	
	

}
