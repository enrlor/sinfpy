#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np

import psutil
import ray

from sinfpy.utils import number_of_peaks, balance_influence, similarity_fun

#Default function to compute influence on a specific edge, which can be redefined.
#It assumes all the columns in x being numbers, and relevant to the computation 
#of the similarity
def properties_similarity(xi_old, xi_new, xj_old, xj_new, threshold, prev_inf, similarity_fun):
    influence = 0
    sim_i = similarity_fun(xi_old.iloc[0].tolist(),
                       xi_new.iloc[0].tolist())
    sim_j = similarity_fun(xj_old.iloc[0].tolist(),
                       xj_new.iloc[0].tolist())
    sim_ij = similarity_fun(xi_new.iloc[0].tolist(),
                        xj_new.iloc[0].tolist())
    
    if(prev_inf > threshold) or \
        (sim_i <= threshold and sim_j > threshold) or \
        (sim_i > threshold and sim_j <= threshold):
            influence = sim_ij if sim_i > sim_j else -sim_ij
    
    return influence

class EdgeInfluence:
    #Initialization of the algorithm to compute the influence at the edge level.
    #E                      is the table of edges in the form of <p1, p2, timeframe, weight>.
    #                       the table is indexed by (p1,p2)
    #X                      is the attributes table in the form of <characterId, attributes_list..., timeframe>
    #user_id                name of the column representing the ids of the users in the data DataFrame
    #edge_u                 name of the column representing the 1st node in the edge list Dataframe
    #edge_v                 name of the column representing the 2st node in the edge list Dataframe
    #timeframe              name of the column representing the timeframes in the data (and edge list if dynamic) DataFrame
    #computing_influence    is the function used to compute the edge influence from similarity.
    #                       if a custom function is defined, the signature must be the following 
    #                       (xi_old, xi_new, xj_old, xj_new, threshold, prev_inf, similarity_fun)
    #                       the similarity_fun is the function used to compute the similarity, according to the method chosen
    #similarity             the function used to compute the similarity among the nodes' properties,
    #                       which can either be the cosine simiarity, the euclidean distance,
    #                       or the manhattan distance.
    #dynamic                can either be True or False, and specifies whether the graph is dynamic.
    #                       The default value is True.
    #threshold              specifies the minimum similarity to be considered as influence.
    #                       The default value is 0.80.
    #balance_inf            can either be True of False, and specifies whether the influence needs
    #                       to be balanced according to the edge's weight. The default value is True
    #penality               used if balance_inf is True. It specifies the penality applied to the
    #                       edge influence score.
    def __init__(self, E, X, user_id = 'characterId', edge_u = 'p1', edge_v = 'p2', timeframe = 'timeframe',
                computing_influence = properties_similarity, similarity = 'cosine', dynamic = True,
                threshold = 0.80, balance_inf = True, penality = 0.1):
        self.E = E
        self.X = X
        self.userid = user_id
        self.edgeu = edge_u
        self.edgev = edge_v
        self.timeframe = timeframe

        self.similarity_method = similarity
        self.computing_influence = computing_influence
        self.threshold = threshold
        self.balance = balance_inf
        self.penality = penality

        if dynamic:
            self.job = self.dynamic_net_job
        else:
            self.job = self.static_net_job

        self.checkdata()

        self.X.loc[:,user_id] = self.X.loc[:,user_id].astype(str)

        self.E.loc[:,edge_u] = self.E.loc[:,edge_u].astype(str)
        self.E.loc[:,edge_v] = self.E.loc[:,edge_v].astype(str)
        self.E.set_index([edge_u,edge_v], inplace = True)
        self.E.sort_index(inplace = True)
    
    def checkdata(self):
        if not isinstance(self.threshold, float) :
            raise TypeError('threshold should be a float.')
        if not isinstance(self.balance, bool):
            raise TypeError('balance_inf should be a boolean.')
        if not isinstance(self.penality, float):
            raise TypeError('penality should be a float.')

        if not isinstance(self.X, pd.DataFrame):
            raise TypeError('X should be a pandas DataFrame.')
        else:
            if not self.userid in self.X.columns:
                raise ValueError('No ' + self.userid + ' in X columns.')
            if not self.timeframe in self.X.columns:
                raise ValueError('No ' + self.timeframe + ' in X columns.')
        
        if not isinstance(self.E, pd.DataFrame):
            raise TypeError('E should be a pandas DataFrame.')
        else: 
            if not self.edgeu in self.E.columns:
                raise ValueError('No ' + self.edgeu + ' in E columns.')
            if not self.edgev in self.E.columns:
                raise ValueError('No ' + self.edgev + ' in E columns.')
            if self.job == self.dynamic_net_job:
                if not self.timeframe in self.E.columns:
                    raise ValueError('No ' + self.timeframe + ' in E columns.')
        


    #The job for an individual worker computed on its slice of the data for a static network
    #where the edges do not vary in time.
    @ray.remote
    def static_net_job(self, E, X, edge_list, edges_slice_index):
        E_slice = pd.DataFrame({self.edgeu : [x[0] for x in edge_list[range(edges_slice_index[0],edges_slice_index[1]+1)]],
                                self.edgev : [x[1] for x in edge_list[range(edges_slice_index[0],edges_slice_index[1]+1)]],
                                'influence': [0]*(edges_slice_index[1]+1-edges_slice_index[0])})
        E_slice.set_index([self.edgeu,self.edgev], inplace = True)
        
        for e,_ in E_slice.iterrows():
            
            influence = 0

            i = str(min(int(e[0]), int(e[1])))
            j = str(max(int(e[0]), int(e[1])))

            Xi = X.loc[[i]].reset_index()
            Xj = X.loc[[j]].reset_index()

            timeframes =  list(set(X.loc[:,self.timeframe].unique().tolist() + Xj.loc[:,self.timeframe].unique().tolist()))
            timeframes.sort()
            prev_tf = timeframes[0]
            
            for tf in timeframes[1:]:
                xi_old = Xi[Xi.loc[:,self.timeframe] == prev_tf]
                xj_old = Xj[Xj.loc[:,self.timeframe] == prev_tf]
                xi_new = Xi[Xi.loc[:,self.timeframe] == tf]
                xj_new = Xj[Xj.loc[:,self.timeframe] == tf]
    		
                influence = self.computing_influence(xi_old, xi_new,
                                                 xj_old, xj_new,
                                                 self.threshold,
                                                 influence,
                                                 similarity_fun(self.similarity_method))
            
                if(self.balance):
                    influence = balance_influence(influence,len(timeframes))
                    
                E_slice.loc[e,'influence'] = influence
                
                prev_tf = tf 

        return E_slice.reset_index()
    
    #The job for an individual worker computed on its slice of the data for a dynamic network
    #where the edges may vary in time.
    @ray.remote
    def dynamic_net_job(self, E, X, edge_list, edges_slice_index):
        E_slice = pd.DataFrame({self.edgeu : [x[0] for x in edge_list[range(edges_slice_index[0],edges_slice_index[1]+1)]],
                                self.edgev : [x[1] for x in edge_list[range(edges_slice_index[0],edges_slice_index[1]+1)]],
                                'influence': [0]*(edges_slice_index[1]+1-edges_slice_index[0])})
        E_slice.set_index([self.edgeu,self.edgev], inplace = True)
        
        for e,_ in E_slice.iterrows():
            
            influence = 0
            timeframes =  E.loc[pd.IndexSlice[e],self.timeframe].values
            
            if (isinstance(timeframes,np.float64) or len(timeframes) == 0):
                continue
            else:
                timeframes = timeframes.tolist()
            timeframes.sort()
            i = str(min(int(e[0]), int(e[1])))
            j = str(max(int(e[0]), int(e[1])))

            prev_tf = timeframes[0]
            Xi = X.loc[[i]].reset_index()
            Xj = X.loc[[j]].reset_index()
            
            for tf in timeframes[1:]:
                xi_old = Xi[Xi.loc[:,self.timeframe] == prev_tf]
                xj_old = Xj[Xj.loc[:,self.timeframe] == prev_tf]
                xi_new = Xi[Xi.loc[:,self.timeframe] == tf]
                xj_new = Xj[Xj.loc[:,self.timeframe] == tf]
    		
                influence = self.computing_influence(xi_old, xi_new,
                                                 xj_old, xj_new,
                                                 self.threshold,
                                                 influence,
                                                 similarity_fun(self.similarity_method))
            
                if(self.balance):
                    w = E[[(e == i) and (t == tf) for i, t in \
                                 zip(E.index, E.loc[:,self.timeframe])]].weight
                    influence = balance_influence(influence, w)
                    
                E_slice.loc[e,'influence'] = influence
                
                prev_tf = tf
                
        return E_slice.reset_index()
            
    #When the object is called the edge influence is computed.
    #The algorithm supports multiprocessing, so the number of available workers can be specified.
    #The default is None.
    #It returns the updated table of edges E with the edge influence scores.
    #Important: the influence value refers to the node with the lowest id; for the other node the
    #edge influence score is -influence.
    def __call__(self, n_workers = None):
        
        n_workers = psutil.cpu_count(logical=False) if n_workers == None else n_workers
        available = psutil.virtual_memory()[1]
        
        edge_list = self.E.index.unique()
        size = len(edge_list)
        load = int(size/n_workers)
        
        ray.init(num_cpus=n_workers, 
                 memory=available*0.6, object_store_memory=available*0.4)
        
        self.X = self.X.set_index(self.userid)
        self.X.loc[:,self.timeframe] = self.X.loc[:,self.timeframe].astype(int)
        
        E_id = ray.put(self.E)
        X_id = ray.put(self.X)
        edge_list_id = ray.put(edge_list)
        
        eindexes = []
        
        if n_workers is None or n_workers < 2:
            eindexes.append([0, len(edge_list_id)])
        else:
            eindexes = [ [start_index,start_index+load] \
                for start_index in range(0, (n_workers - 1)*load, load) ]

            #last worker size may be bigger
            start_index = (n_workers - 1)*load
            eindexes.append([start_index, len(edge_list) - 1])

        updated_E = ray.get([self.job.remote(self,E_id,X_id,edge_list_id, i) \
                       for i in eindexes])

        ray.shutdown()
        
        updated_E = pd.concat([df for df in updated_E], ignore_index = True)
        
        return updated_E


class NodeInfluence:
    #Initialization of the algorithm to compute the node influence scores.
    #E          is the table of updated edges, with the edge influence
    #stats      if True computes also the number of peaks and the standart
    #           deviation of the edge influence for each node.
    def __init__(self, E, edge_u = 'p1', edge_v = 'p2', stats = False):
        self.E = E.reset_index()
        self.stats = stats
        self.edgeu = edge_u
        self.edgev = edge_v

        self.checkdata

    def checkdata(self):
        if not isinstance(self.E, pd.DataFrame):
            raise TypeError('E should be a pandas DataFrame.')
        else: 
            if not self.edgeu in self.E.columns:
                raise ValueError('No ' + self.edgeu + ' in E columns.')
            if not self.edgev in self.E.columns:
                raise ValueError('No ' + self.edgev + ' in E columns.')
        
    
    #The job for an individual worker computed on its slice of the data
    @ray.remote
    def job(self, nodes_list, edges, nodes_slice_index):
        influence_scores = pd.DataFrame({'node': nodes_list[range(nodes_slice_index[0],nodes_slice_index[1]+1)] })
        influence_scores.loc[:,'influence'] = 0
        if self.stats:
            influence_scores.loc[:,'n_peaks'] = 0
            influence_scores.loc[:,'std'] = 0
        
        for i in range(len(influence_scores.node)):
            influence_sum = 0
            node = influence_scores.node[i]
            edges_slice = edges.loc[list((edges.loc[:,self.edgeu] == node) | (edges.loc[:,self.edgev] == node)),:]
            inf_list = []
            for j in range(len(edges_slice)):
                e = edges_slice.iloc[[j],:]
                influence = e['influence'].values[0]
                influence = influence if e.loc[:,self.edgeu].values == node else -influence
                influence_sum += influence
                inf_list.append(influence)
            
            influence_scores.loc[[i], 'influence'] = influence_sum/len(edges_slice)
            
            if self.stats:
                influence_scores.loc[[i], 'n_peaks'] = number_of_peaks(inf_list)
                influence_scores.loc[[i], 'std'] = np.std(inf_list)
            
        return influence_scores
    
    #When the object is called the node influence is computed.
    #The algorithm supports multiprocessing, so the number of available workers can be specified.
    #The default is None.
    #It returns a table with the list of nodes and the influence score, as the stats if the param is True.
    def __call__(self, n_workers = None):
        n_workers = psutil.cpu_count(logical=False) if n_workers == None else n_workers
        available = psutil.virtual_memory()[1]
        
        nodes_list = np.array(list(set(self.E.loc[:,self.edgeu].tolist() +
                        self.E.loc[:,self.edgev].tolist())))
        size = len(nodes_list)
        load = int(size/n_workers)
    
        ray.init(num_cpus=n_workers, 
                 memory=available*0.6, object_store_memory=available*0.4)
        
        E_id = ray.put(self.E)
        nodes_list_id = ray.put(nodes_list)

        nindexes = []
        
        if n_workers is None or n_workers < 2:
            nindexes.append([0, len(nodes_list_id)])
        else:
            nindexes = [ [start_index,start_index+load] \
                for start_index in range(0, (n_workers - 1)*load, load) ]
            
            #last worker size may be bigger
            start_index = (n_workers - 1)*load
            nindexes.append([start_index, len(nodes_list) - 1])
        
        influence_scores = ray.get([self.job.remote(self,nodes_list_id,E_id,i) \
                       for i in nindexes])

        ray.shutdown()
        
        influence_scores = pd.concat([df for df in influence_scores], ignore_index = True)
        
        return influence_scores
    
    
    
    
    
    
    
    
    
    
    