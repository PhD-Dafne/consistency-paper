import igraph as ig
import leidenalg
import numpy as np
import pandas as pd
import nwtools.communities, nwtools.consensus, nwtools.common
import click
import os


def read_data(datapath):
    partitions_df = pd.read_csv(os.path.join(datapath, 'partitions.csv'),
                                na_filter=False)
    graph = ig.Graph.Read_Pickle(os.path.join(datapath, 'graph.pkl'))

    initial_partition = [leidenalg.ModularityVertexPartition(graph,
                                                             initial_membership=row.values,
                                                             weights='weight')
                         for i, row in partitions_df.iterrows()]

    return graph, initial_partition


@click.command()
@click.argument('datapath', type=click.Path(exists=True))
@click.option('--stepsize', '-s', default=0.1)
@click.option('--out_dir', '-o', default=os.getcwd(), type=click.Path())
def consensus_clustering(datapath, stepsize, out_dir):
    graph, initial_partition = read_data(datapath)

    cons_modularities = []
    cons_memberships = []
    t_range = np.arange(0, 1, stepsize)
    for t in t_range:
        print('threshold: {}'.format(t))
        cm, consensus_membership = nwtools.consensus.consensus_partition(graph,
                                                                         weights='weight',
                                                                         initial_partition=initial_partition,
                                                                         nr_partitions=len(
                                                                             initial_partition),
                                                                         threshold=t,
                                                                         verbose=True)
        cons_memberships.append(consensus_membership)
        cons_modularities.append(leidenalg.ModularityVertexPartition(graph,
                                                                     initial_membership=consensus_membership,
                                                                     weights='weight').quality())

    df_cons_memberships = pd.DataFrame(cons_memberships).transpose()
    df_cons_memberships.columns = ['{:.3f}'.format(t) for t in t_range]
    df_cons_memberships.index = graph.vs['name']
    df_cons_memberships.to_csv(
        os.path.join(datapath, 'consensus_thresholds.csv'))

    df_modularities = pd.DataFrame({'threshold': t_range,
                                    'modularity': cons_modularities})
    df_modularities.to_csv(os.path.join(datapath, 'thresholds_modularity.csv'),
                           index=False)


if __name__ == '__main__':
    consensus_clustering()
