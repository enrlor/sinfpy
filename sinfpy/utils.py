#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 10:25:59 2020

@author: fbk_user
"""
import numpy as np
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
