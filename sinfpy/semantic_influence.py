#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 10:19:52 2020

@author: enrlor
"""

import multiprocessing as mp
import pandas as pd
import numpy as np
import math

from sinfpy.utils import number_of_peaks

class EdgeInfluence:
    #Initialization of the algorithm to compute the influence at the edge level.
    #E                      is the table of edges in the form of <p1, p2, timeframe, weight>. 
    #                       the table is indexed by (p1,p2)
    #X                      is the attributes table in the form of <characterId, attributes_list..., timeframe>
    #computing_influence    is the function used to compute the edge influence from similarity.
    #                       the function signature must be the following (xi_old, xi_new, xj_old, xj_new, prev_inf, threshold)
    #                       the similarity can either be user-defined or the similarity function in sinfy.utils
    #dynamic                can either be True or False, and specifies whether the graph is dynamic.
    #                       The default value is True.
    #threshold              specifies the minimum similarity to be considered as influence.
    #                       The default value is 0.80.
    #balance_inf            can either be True of False, and specifies whether the influence needs
    #                       to be balanced according to the edge's weight. The default value is True
    #penality               used if balance_inf is True. It specifies the penality applied to the 
    #                       edge influence score.
    def __init__(self, E, X, computing_influence, dynamic = True,
                 threshold = 0.80, balance_inf = True, penality = 0.1):
        self.E = E
        self.X = X
        self.computing_influence = computing_influence
        self.threshold = threshold
        self.balance = balance_inf
        self.penality = penality
        
        if dynamic:
            self.job = self.dynamic_net_job
        else:
            self.jon = self.static_net_job
        
    #In case the parameter balance_inf is true, the influence value is adjusted according 
    # to the edge's weight, using a logarithmic function     
    def balance_influence(self, influence, weight, penality = 0.1):
        penalized_inf = influence * penality
        return float(influence - (penalized_inf * (1 - math.log(weight + 1, 2)/weight)))
    
    #The job for an individual worker computed on its slice of the data for a static network
    #where the edges do not vary in time.
    def static_net_job(self, E_slice, X):
        E_slice.loc[:,'influence'] = 0
        for e in E_slice.index.unique():
            
            influence = 0
            timeframes =  X.timeframe.unique().values
            timeframes.sort()
            i = min(e[0], e[1])
            j = max(e[0], e[1])
            
            prev_tf = timeframes[0]
            
            for tf in timeframes[1:]:
                xi_old = X.loc[[(X.characterId == i) & list(X.timeframe == prev_tf)][0], :]
                xj_old = X.loc[[(X.characterId == j) & list(X.timeframe == prev_tf)][0], :]
                xi_new = X.loc[[(X.characterId == i) & list(X.timeframe == tf)][0], :]
                xj_new = X.loc[[(X.characterId == j) & list(X.timeframe == tf)][0], :]
    		
            
                influence = self.computing_influence(xi_old, xi_new, 
                                                 xj_old, xj_new, 
                                                 self.threshold,
                                                 influence)
            
                if(self.balance):
                    influence = self.balance_influence(influence, 
                                                       len(timeframes))
                    
                E_slice.loc[e,'influence'] = influence
                
                prev_tf = tf  
                
        return E_slice
    
    #The job for an individual worker computed on its slice of the data for a dynamic network
    #where the edges may vary in time.
    def dynamic_net_job(self, E_slice, X):
        E_slice.loc[:,'influence'] = 0
        for e in E_slice.index.unique():
            
            influence = 0
            timeframes =  E_slice.loc[pd.IndexSlice[e],'timeframe']
            if (type(timeframes) == np.float64 or len(timeframes) == 0):
                continue
            else:
                timeframes = timeframes.values
            timeframes.sort()
            i = min(e[0], e[1])
            j = max(e[0], e[1])
            
            prev_tf = timeframes[0]
            
            for tf in timeframes[1:]:
                xi_old = X.loc[[(X.characterId == i) & list(X.timeframe == prev_tf)][0], :]
                xj_old = X.loc[[(X.characterId == j) & list(X.timeframe == prev_tf)][0], :]
                xi_new = X.loc[[(X.characterId == i) & list(X.timeframe == tf)][0], :]
                xj_new = X.loc[[(X.characterId == j) & list(X.timeframe == tf)][0], :]
    		
                influence = self.computing_influence(xi_old, xi_new, 
                                                 xj_old, xj_new, 
                                                 self.threshold,
                                                 influence)
            
                if(self.balance):
                    w = E_slice[[(e == i) and (t == tf) for i, t in \
                                 zip(E_slice.index, E_slice.timeframe)]].weight
                    influence = self.balance_influence(influence, w)
                    
                E_slice.loc[e,'influence'] = influence
                
                prev_tf = tf 
                
        return E_slice
            
    #When the object is called the edge influence is computed. 
    #The algorithm supports multiprocessing, so the number of available workers can be specified.
    #The default is None.
    #It returns the updated table of edges E with the edge influence scores.
    #Important: the influence value refers to the node with the lowest id; for the other node the
    #edge influence score is -influence.
    def __call__(self, n_workers = None):
        edge_list = self.E.index.unique()
        size = len(edge_list)
        load = int(size/n_workers)
        
        pool = mp.Pool(n_workers)
        workers = []

        if n_workers is None or n_workers < 2:
            workers.append(pool.apply_async(self.job, (self.E, self.X)))
        else:
            edge_list_slices = [edge_list[start_index:start_index+load] \
                for start_index in range(0, (n_workers - 1)*load, load)]
            workers = [pool.apply_async(self.job, (self.E.loc[eslice,:], self.X)) \
                for eslice in edge_list_slices]

            #last worker size may be bigger
            start_index = (n_workers - 1)*load
            edge_list_slice = edge_list[start_index:] 
            E_slice = self.E.loc[edge_list_slice,:] 
            workers.append(pool.apply_async(self.job, (E_slice, self.X)))

        updated_E = None
        for worker in workers:
            worker.wait()
            if updated_E is None:
                updated_E = worker.get()
            else:
                updated_E = updated_E.append(worker.get())
        pool.close()
        
        return updated_E


class NodeInfluence:
    #Initialization of the algorithm to compute the node influence scores.
    #E          is the table of updated edges, with the edge influence
    #stats      if True computes also the number of peaks and the standart
    #           deviation of the edge influence for each node.
    def __init__(self, E, stats = False):
        self.E = E.reset_index()
        self.stats = stats
    
    #The job for an individual worker computed on its slice of the data
    def job(self, nodes_list, edges):
        influence_scores = pd.DataFrame(nodes_list, columns = ['node'])
        influence_scores.loc[:,'influence'] = 0
        if self.stats:
            influence_scores.loc[:,'n_peaks'] = 0
            influence_scores.loc[:,'std'] = 0
        
        for i in range(len(influence_scores.node)):
            influence_sum = 0
            node = influence_scores.node[i]
            edges_slice = edges.loc[list((edges.p1 == node) | (edges.p2 == node)),:]
            inf_list = []
            for j in range(len(edges_slice)):
                e = edges_slice.iloc[j,:]
                influence = e['influence']
                influence = influence if e.p1 == node else -influence
                influence_sum += influence
                inf_list.append(influence)
            influence_scores.loc[i, 'influence'] = influence_sum/len(edges_slice)
            
            if self.stats:
                influence_scores.loc[i, 'n_peaks'] = number_of_peaks(inf_list)
                influence_scores.loc[i, 'std'] = np.std(inf_list)
            
        return influence_scores
    
    #When the object is called the node influence is computed. 
    #The algorithm supports multiprocessing, so the number of available workers can be specified.
    #The default is None.
    #It returns a table with the list of nodes and the influence score, as the stats if the param is True.
    def __call__(self, n_workers = None):
        nodes_list = list(set(self.E.p1.tolist() + 
                        self.E.p2.tolist()))
        size = len(nodes_list)
        load = int(size/n_workers)
    
        pool = mp.Pool(n_workers)

        pool = mp.Pool(n_workers)
        workers = []

        if n_workers is None or n_workers < 2:
            workers.append(pool.apply_async(self.job, (nodes_list, self.E)))
        else:
            #dividing the node list in n_workers - 1 slices
            nodes_list_slices = [nodes_list[start_index:start_index+load] \
                for start_index in range(0, (n_workers - 1)*load, load)]
            #dividing the edge list in n_workers - 1 slices according to the 
            #prior division of the nodes list
            edge_list_slices = [self.E.iloc[[ (a in nslice or b in nslice) \
                        for a,b in zip(self.E.p1,self.E.p2)],:] \
                            for nslice in nodes_list_slices]
            #building the list of the async workers
            workers = [pool.apply_async(self.job, (nslice, eslice)) \
                for eslice,nslice in zip(edge_list_slices,nodes_list_slices)]
      
            #last worker size may be bigger
            start_index = (n_workers - 1)*load
            nodes_list_slice = nodes_list[start_index:] 
            E_slice = self.E.iloc[[ (a in nodes_list_slice or b in nodes_list_slice) \
                                    for a,b in zip(self.E.p1,self.E.p2)],:]
            workers.append(pool.apply_async(self.job, (nodes_list_slice, E_slice)))            
        
        influence_scores = None
        for worker in workers:
            worker.wait()
            if influence_scores is None:
                influence_scores = worker.get()
            else:
                influence_scores = influence_scores.append(worker.get()) 
        pool.close()
        
        return influence_scores

    
