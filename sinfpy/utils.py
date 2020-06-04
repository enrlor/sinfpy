#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import math
from scipy.signal import find_peaks
from scipy.spatial import distance

#Computing the cosine similarity between two property vectors.
#The elements' order is the same in both arguments.
#It also assumes that the values are normalized.
#The method can either be cosine (for cosine similarity), 
#euclidean (for euclidean distance), or manhattan (for manhattan distance).
def similarity(a,b, method = 'cosine'):
    if method == 'euclidean':
        return distance.euclidean(a,b)
    if method == 'manhattan':
        return distance.euclidean(a,b)
    if method == 'cosine':
        dot = np.dot(a, b)
        norma = np.linalg.norm(a)
        normb = np.linalg.norm(b)
        cos = dot / (norma * normb)
        return cos
    else:
        raise ValueError("Illegal value for method, no definition for " + method)

#Computing the number of peaks of the attribute's values over time.
#The argument is the vector of the attribute's values over time, cronologically ordered.
def number_of_peaks(x):
    return len(find_peaks(x)[0])

#In case the parameter balance_inf is true, the influence value is adjusted according
# to the edge's weight, using a logarithmic function
def balance_influence(influence, weight, penality = 0.1):
    penalized_inf = influence * penality
    return float(influence - (penalized_inf * (1 - math.log(weight + 1, 2)/weight)))