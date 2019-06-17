# consistency-paper
Code and documentation for the consitency paper

## Installation
Prerequisites:
- Python 3.5 or 3.6
- Python package [nwtools](https://github.com/PhD-Dafne/network-tools). You can install it with: `pip install -e https://github.com/PhD-Dafne/network-tools`.

## scripts
### run_consistency.py
Read a node file and edge file, and run consensus clustering for a specific threshold, and calculate edge and node consistency scores.

Example usage: `python scripts/run_consistency.py data/edges.csv data/nodes.csv`

```
Usage: run_consistency.py [OPTIONS] EDGE_FILE NODE_FILE

Options:
  -sn, --sepn TEXT  seperator for node file
  -se, --sepe TEXT  seperator for edges file
  -i, --idcol TEXT  name of ID column in nodes header
  -w, --weightcol TEXT  name of weight column in edges header
  -t, --threshold FLOAT threshold for consensus clustering
  -n, --nriter INTEGER  number of initial clusterings
  -o, --out_dir PATH
  --help
```


### consensus_clustering.py
Runs consensus clustering for different thresholds, with the same initial partitions that it reads from a file on `DATAPATH`
```
Usage: consensus_clustering.py [OPTIONS] DATAPATH

Options:
  -s, --stepsize FLOAT  stepsize for threshold list
  -o, --out_dir PATH
  --help
```

## Notebooks
There is a [notebook](https://github.com/PhD-Dafne/consistency-paper/blob/master/notebooks/Countries.ipynb) with the plots in the paper, as well as some further exploration, on an example data set.

