#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 10:25:59 2020

@author: fbk_user
"""
import numpy as np 
import math

def similarity(a,b):
    dot = np.dot(a, b)
    norma = np.linalg.norm(a)
    normb = np.linalg.norm(b)
    cos = dot / (norma * normb)
    return cos


def fun(w):
    return (1 - math.log(w + 1, 2)/w)

