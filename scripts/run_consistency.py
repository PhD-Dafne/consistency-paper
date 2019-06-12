import igraph
import leidenalg
import numpy as np
import itertools
import pandas as pd
import nwtools.communities, nwtools.consensus, nwtools.common
import click
import os

def load_graph(edge_file, node_file, sepn=',', sepe=',', idcol='id', weightcol='Weight'):
    edges_df = pd.read_csv(edge_file, na_filter=False, sep=sepe)
    edges_df = edges_df.rename({weightcol: 'weight'}, axis=1)
    edges_df['distance'] = 1.0 / edges_df['weight']
    edges_df['Source'] = edges_df.Source.astype(str)
    edges_df['Target'] = edges_df.Target.astype(str)
    
    # Reorder source and target so that source < target
    source = edges_df[['Source', 'Target']].apply(min, axis=1).values 
    target = edges_df[['Source', 'Target']].apply(max, axis=1).values
    edges_df['Source'] = source
    edges_df['Target'] = target
    
    nodes = pd.read_csv(node_file, index_col=idcol, sep=sepn)
    
    graph = nwtools.common.igraph_from_pandas_edgelist(edges_df, attributes=['weight', 'distance'])
    
    return edges_df, nodes, graph

def get_node_consistency(graph, edges_df, thres_list=None):
    suffix = ''
    names = graph.vs.get_attribute_values('name')
    nodes_df = pd.DataFrame(index=names)
    nodes_df['degree'+suffix] = pd.Series(graph.degree(), index=names)
    nodes_df['weighted_degree'+suffix] = pd.Series(graph.strength(weights='weight'), index=names)
    nodes_df['eigenvector_centrality'+suffix] = pd.Series(
        graph.eigenvector_centrality(directed=False), index=names)
    nodes_df['betweenness'+suffix] = pd.Series(graph.betweenness(directed=False), index=names)
    edges_unstacked = edges_df.set_index(['Source', 'Target']).consistency.unstack()
    
    stabilities_unstacked = edges_unstacked.add(edges_unstacked.transpose(), fill_value=0)

    nodes_df['consistency_mean'] = stabilities_unstacked.mean(axis=0)
    nodes_df['consistency_min'] = stabilities_unstacked.min(axis=0)
    nodes_df['consistency_max'] = stabilities_unstacked.max(axis=0)
    nodes_df['consistency_std'] = stabilities_unstacked.apply(np.std, axis=0)
    nodes_df['consistency_mean_min_std'] = nodes_df['consistency_mean'] - nodes_df['consistency_std']
    if thres_list is None:
        thres_list = [0.8, 0.9, 1.0]
    for thres in thres_list:
        perc_consistent_neigbors =  (stabilities_unstacked>=thres).sum(axis=0) / (~stabilities_unstacked.isna()).sum(axis=0)
        nodes_df['consistency_neighbors_{:.1f}'.format(thres)] =perc_consistent_neigbors
        
    return nodes_df


@click.command()
@click.argument('edge_file', type=click.Path(exists=True))
@click.argument('node_file', type=click.Path(exists=True))
@click.option('--sepn', '-sn', default=',')
@click.option('--sepe', '-se', default=',')
@click.option('--idcol', '-i', default='id')
@click.option('--weightcol', '-w', default='Weight')
@click.option('--threshold', '-t', default=0.5)
@click.option('--nriter', '-n', default=100)
@click.option('--out_dir', '-o', default=os.getcwd(), type=click.Path())
def run_consistency(edge_file, node_file, out_dir, sepn, sepe, idcol, weightcol, threshold, nriter):
    print('Load data...')
    edges_df, nodes_df, graph = load_graph(edge_file, node_file, sepn, sepe, idcol, weightcol)
    graph.write_pickle('graph.pkl')
    node_names = graph.vs['name']
    
    # Get initial partitions
    print('Get initial {} partitions'.format(nriter))
    partitions = nwtools.consensus.get_initial_partitions(graph, weights='weight', nr_partitions=nriter) 
    partitions_df = pd.DataFrame([p.membership for p in partitions], columns=graph.vs['name'])
    partitions_df.to_csv(os.path.join(out_dir, 'partitions.csv'), index=False)
    
    # Get consensusmatrix
    print('Consensus clustering with t={:.2f}'.format(threshold))
    consensus_matrix, consensus_membership = nwtools.consensus.consensus_partition(graph, initial_partition=partitions,
                        nr_partitions=len(partitions),
                        threshold=threshold,
                        weights='weight')
    np.save('consensus.npy', consensus_matrix)
    
    # Get edge consistency and create edge dataframe
    print('Calculating edge consistency..')
    graph = nwtools.consensus.get_edge_consistency(graph, consensus_matrix)
    edges_att_df = consensus_df = pd.DataFrame({'Source': [min(node_names[e.source], node_names[e.target]) 
                                                           for e in graph.es],
                                 'Target': [max(node_names[e.source], node_names[e.target])  for e in graph.es],
                                'consensus': graph.es['consensus'],
                                'consistency': graph.es['consistency']})

    edges_att_df = edges_att_df.merge(edges_df,
                                      left_on=['Source', 'Target'], 
                                      right_on=['Source', 'Target'])
    edges_att_df.to_csv('edges-consistency.csv', index=False)
    
    # Get node consistency
    print('Calculating node consistency..')
    nodes_att_df = get_node_consistency(graph, edges_att_df)
    nodes_att_df = nodes_att_df.merge(nodes_df, left_index=True, right_index=True, how='left')
    nodes_att_df['consensus'] = pd.Series(consensus_membership, index=node_names)
    nodes_att_df.to_csv('nodes-consistency.csv')
    
    print('Done.')

if __name__ == '__main__':
    run_consistency()