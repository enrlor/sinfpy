#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 10:25:59 2020

@author: fbk_user
"""
import numpy as np
import pandas as pd
import math
from scipy.signal import find_peaks

#Computing the cosine similarity between two property vectors.
#The elements' order is the same in both arguments.
def similarity(a,b):
    dot = np.dot(a, b)
    norma = np.linalg.norm(a)
    normb = np.linalg.norm(b)
    cos = dot / (norma * normb)
    return cos

#Computing the number of peaks of the attribute's values over time.
#The argument is the vector of the attribute's values over time, cronologically ordered.
def number_of_peaks(x):
    return len(find_peaks(x)[0])

#In case the parameter balance_inf is true, the influence value is adjusted according
# to the edge's weight, using a logarithmic function
def balance_influence(influence, weight, penality = 0.1):
    penalized_inf = influence * penality
    return float(influence - (penalized_inf * (1 - math.log(weight + 1, 2)/weight)))

#Computing the metric retention transfer defined in the paper
#to evaluate to what extend nodes impact their neighbors 
#retention in the game. It hase value in (0,+inf). 
#The lower the value, the more the node impacted its neighbors.
#it take as input the selection of nodes for which the retention transfer
#is needed, the edge list and the data list (?)
def retention_transfer(nodes_sel, E, X):
    
    nodes_sel = nodes_sel.index.tolist()
    
    E = E.reset_index()
    E_filtered = E[[a in nodes_sel or b in nodes_sel for a,b in \
                    zip(E.p1.tolist(), E.p2.tolist())]]
    E_filtered = E_filtered.groupby(['p1','p2']).agg({'timeframe':'min'})
    E_filtered = E_filtered.reset_index()
    
    X_filtered = X.groupby('characterId').agg({'timeframe':'max'})
    selection = list(set(E_filtered.p1.tolist() + E_filtered.p2.tolist()))
    X_filtered = X_filtered[[a in selection for a in X_filtered.index.tolist()]]
    X_filtered = X_filtered.reset_index()
    
    X_filtered.columns = ['node','end_tf']
    E_filtered.columns = ['p1','p2','start_tf']
    
    res = E_filtered.set_index('p1').join(X_filtered.set_index('node'), how = 'left', lsuffix = '_p1').reset_index()
    res = res.set_index('p2').join(X_filtered.set_index('node'), how = 'left', lsuffix = '_p2').reset_index()
    res.columns = ['p1','p2','start','end_p2','end_p1']
    
    nodes_sel = pd.DataFrame(columns = ['node'], data = nodes_sel)
    nodes_sel.loc[:,'how_long_retained'] = -1
    nodes_sel.loc[:,'how_long_retained'] = -1
    nodes_sel.loc[:,'how_long_also_drop'] = -1
    nodes_sel.loc[:,'retention_transfer'] = 1000000
        
    
    for n in nodes_sel.node:
        rt = []
        retained = []
        drop = []
        for _,row in res.loc[res.p1 == n,:].iterrows():
            end_n = row.end_p2
            end_i = row.end_p1
            start = row.start
            rt.append(abs((end_n - start + 1) - (end_i - start + 1)))
            retained.append((end_n - start + 1) / (end_i - start + 1))
            drop.append(-1 if end_n < end_i else (end_n - end_i + 1))
        for _,row in res.loc[res.p2 == n,:].iterrows():
            end_n = row.end_p1
            end_i = row.end_p2
            start = row.start
            rt.append(abs((end_n - start + 1) - (end_i - start + 1)))
            retained.append((end_n - start + 1) / (end_i - start + 1))
            drop.append(-1 if end_n < end_i else (end_n - end_i + 1))
        
        nodes_sel.loc[nodes_sel.node == n, 'retention_transfer'] = np.mean(rt)
        nodes_sel.loc[nodes_sel.node == n, 'how_long_retained'] = np.mean(retained)
        nodes_sel.loc[nodes_sel.node == n, 'how_long_also_drop'] = np.mean(drop)
        nodes_sel.loc[nodes_sel.node == n, 'n_neighbora'] = len(retained)
        
    return nodes_sel