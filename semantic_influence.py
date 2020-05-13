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

from scipy.signal import find_peaks


class EdgeInfluenceDetection:
    
    def __init__(self, E, X, computing_influence, dynamic = True,
                 threshold = 0.80, balance_inf = True):
        self.E = E
        self.X = X
        self.computing_influence = computing_influence
        self.threshold = threshold
        self.balance = balance_inf
        
        if dynamic:
            self.job = self.dynamic_net_job
        else:
            self.jon = self.static_net_job
        
        
    def balance_influence(self, influence, w):
        inf_perc_20 = influence * 10 /100
        # math.log(w + 1, 2)/w for w->inf = 0
        # 1 - math.log(w + 1, 2)/w) for w->inf = 1
        #so, the higher the w, the higher the penality
        #for w = 1 (inf_perc_20 * (1 - math.log(w + 1, 2)/w)) = 0
        #so, no penality
        return float(influence - (inf_perc_20 * (1 - math.log(w + 1, 2)/w)))
    
    
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
    
    
    def dynamic_net_job(self, E_slice, X):
       
        E_slice.loc[:,'influence'] = 0
        for e in E_slice.index.unique():
            
            influence = 0
            timeframes =  E_slice.loc[pd.IndexSlice[e],'timeframe']
            if (type(timeframes) == np.float64 or len(timeframes) == 0):
                #print(e)
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
            
    
    def __call__(self, filename, n_workers):
        edge_list = self.E.index.unique()
        size = len(edge_list)
        load = int(size/n_workers)
        
        pool = mp.Pool(n_workers)
        
        workers = []
        for i in range(n_workers - 1):
            start_index = i*load
            edge_list_slice = edge_list[start_index:start_index+load]
            E_slice = self.E.loc[edge_list_slice,:]
            workers.append(pool.apply_async(self.job, (E_slice, self.X)))
        
        start_index = (n_workers - 1)*load
        edge_list_slice = edge_list[start_index:] #last worker size may be bigger
        E_slice = self.E.loc[edge_list_slice,:] 
        workers.append(pool.apply_async(self.job, (E_slice, self.X)))

        updated_E = None
        for worker in workers:
            worker.wait()
            
            if updated_E is None:
                updated_E = worker.get()
            else:
                updated_E = updated_E.append(worker.get()) 
            print('A WORKER FINISHED...')
        pool.close()
        
        return updated_E


class NodeInfluence:
    
    def __init__(self, E, stats = False):
        self.E = E.reset_index()
        self.stats = stats
    
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
                influence_scores.loc[i, 'n_peaks'] = self.number_of_peaks(inf_list)
                influence_scores.loc[i, 'std'] = np.std(inf_list)
            
        return influence_scores
    
    
    def __call__(self, n_workers):
        
        nodes_list = list(set(self.E.p1.tolist() + 
                        self.E.p2.tolist()))
        size = len(nodes_list)
        load = int(size/n_workers)
        
        pool = mp.Pool(n_workers)
        
        workers = []
        for i in range(n_workers - 1):
            start_index = i*load
            nodes_list_slice = nodes_list[start_index:start_index+load]
            
            E_slice = self.E.iloc[[ (a in nodes_list_slice or b in nodes_list_slice) \
                                   for a,b in zip(self.E.p1,self.E.p2)],:]
            workers.append(pool.apply_async(self.job, (nodes_list_slice, E_slice)))
        
        start_index = (n_workers - 1)*load
        nodes_list_slice = nodes_list[start_index:] #last worker size may be bigger
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
            print('A WORKER FINISHED...')
        pool.close()
        
        return influence_scores
    
    
    def number_of_peaks(self,x):
        return len(find_peaks(x)[0])

    
