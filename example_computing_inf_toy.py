#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 10:20:10 2020

@author: fbk_user
"""

import sinfpy.semantic_influence as sinf
from sinfpy.utils import similarity

import multiprocessing as mp
import pandas as pd
import sys

def filereader(filename):
    with pd.HDFStore(filename, mode = 'r') as hdf:
        edges_tfs = [name if 'edgelist_tf' in name else '' for name in hdf.keys()]
        data_tfs = [name if 'X_tf' in name else '' for name in hdf.keys()]
        E = None
        X = None
        
        if '' in edges_tfs:
            edges_tfs = list(filter(lambda a: a != '', edges_tfs))
        if '' in data_tfs:
            data_tfs = list(filter(lambda a: a != '', data_tfs))
            
        if len(data_tfs) == 0 or len(edges_tfs) == 0:
            print('Something wrong in SN...')
            sys.exit()
        else:
            
            for i in edges_tfs:
                if E is None:
                    E = hdf[i]
                else:
                    E = E.append(hdf[i])
            
            for i in data_tfs:
                if X is None:
                    X = hdf[i]
                else:
                    X = X.append(hdf[i])
    
    E = E.sort_index()
    return E,X


def participation_influence(xi_old, xi_new, xj_old, xj_new, prev_inf, threshold):
    cols = ['assists','deaths','kills','score']
    influence = 0
    sim_i = similarity(xi_old.loc[:,cols].iloc[0].values, 
                       xi_new.loc[:,cols].iloc[0].values)
    sim_j = similarity(xj_old.loc[:,cols].iloc[0].values,
                       xj_new.loc[:,cols].iloc[0].values)
    sim_ij = similarity(xi_new.loc[:,cols].iloc[0].values, 
                        xj_new.loc[:,cols].iloc[0].values)
    
    if(prev_inf > threshold) or \
        (sim_i <= threshold and sim_j > threshold) or \
        (sim_i > threshold and sim_j <= threshold):
            influence = sim_ij if sim_i > sim_j else -sim_ij
    
    return influence  


if __name__ == '__main__':
    
    fname = 'sample_data/toy_SN.h5'
    fout = 'sample_data/toy_influence.h5'
    workers = mp.cpu_count()
    
    print('READY')
    
    E, X = filereader(fname)
    ei = sinf.EdgeInfluence(E, X, participation_influence) 
                            
    updated_E = ei(workers)
    
    print('EDGE INFLUENCES COMPUTED')
    
    with pd.HDFStore(fout, mode = 'w') as hdf:
        hdf.put('edges', updated_E, format = 'table', data_columns = True)
        
    ni = sinf.NodeInfluence(updated_E, stats = True)
    influences = ni(workers)
    
    print('NODE INFLUENCE COMPUTED')

    with pd.HDFStore(fout) as hdf:
        hdf.put('nodes', influences, format = 'table', data_columns = True)

    print(influences)
