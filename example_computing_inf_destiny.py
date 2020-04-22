#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 10:20:10 2020

@author: fbk_user
"""

import influence_detection as inf
from utils import similarity

import multiprocessing as mp
import pandas as pd
import sys

def filereader(filename):
    with pd.HDFStore(filename, mode = 'r') as hdf:
        #print(hdf.keys())
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
    
    
    #ONLY USED IF TIMEFRAME != DAYS   
    if (tf_len_type != 'D'):
        E = E.reset_index().groupby(['p1','p2','timeframe']).agg({'weight':'sum'}).reset_index().set_index(['p1','p2'])
        X = X.groupby(['characterId','timeframe']).agg({
                'assists':'sum',
                'deaths':'sum',
                'kills':'sum',
                'score':'sum',
                'activityDurationSeconds':'sum',
                'averageLifespanSeconds':'mean',
                'completed':'mean',
                'numMatches':'sum',
                'avgTimeBetweenMatches':'mean',
                }).reset_index()   
    
    
    E = E.sort_index()
    return E,X


def participation_influence(xi_old, xi_new, xj_old, xj_new, prev_inf, threshold):
    cols = ['numMatches', 'avgTimeBetweenMatches', 
            'activityDurationSeconds', 'completed']
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
    
    if len(sys.argv) >= 2:
        tf_len_type = sys.argv[2]
        if(tf_len_type == 'D'):
            filename = '../Data/Destiny/SN/SNA_Destiny_Daily.h5'
            fout = '../Data/Destiny/MeasuresPerPlayer/Destiny_SN_Influence_Daily.h5'
        elif(tf_len_type == 'W'):
            filename = '../Data/Destiny/SN/SNA_Destiny_Weekly.h5'
            fout = '../Data/Destiny/MeasuresPerPlayer/Destiny_SN_Influence_Weekly.h5'
        elif(tf_len_type == 'M'):
            filename = '../Data/Destiny/SN/SNA_Destiny_Monthly.h5'
            fout = '../Data/Destiny/MeasuresPerPlayer/Destiny_SN_Influence_Monthly.h5'
        else:
            print('The arg must specify if the influence is daily weekly or monthly [D,W,M].')
            sys.exit()
    else:
        print('You need to specify the lenght of the timeframes.')
        sys.exit()
    
    tf_len_type = 'W'
    
    workers = mp.cpu_count()
    
    print('READY')
    
    
    E, X = filereader(filename)
    ei = inf.EdgeInfluenceDetection(E, X, participation_influence) 
                            
    updated_E = ei(workers)
    
    print('EDGE INFLUENCES COMPUTED')
    
    with pd.HDFStore(fout, mode = 'w') as hdf:
        hdf.put('edges', updated_E, format = 'table', data_columns = True)
        
    '''
    with pd.HDFStore(fout, mode = 'r') as hdf:
        updated_E = hdf['/edges']
    '''
    
    ni = inf.NodeInfluence(updated_E, stats = True)
    influences = ni(workers)
    
    print('NODE INFLUENCE COMPUTED')

    with pd.HDFStore(fout) as hdf:
        hdf.put('nodes', influences, format = 'table', data_columns = True)


