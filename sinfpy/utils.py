#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 10:25:59 2020

@author: fbk_user
"""
import numpy as np
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
