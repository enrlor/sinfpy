## Detecting Semantic Influential Nodes in Time-Evolving Graphs
[![PyPI version](https://badge.fury.io/py/smogn.svg)](https://badge.fury.io/py/sinfpy)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Build Status](https://travis-ci.com/nickkunz/smogn.svg?branch=master)](https://travis-ci.com/enrlor/sinfpy)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/1bfe5a201f3b4a9787c6cf4b365736ed)](https://www.codacy.com/manual/enrlor/sinfpy?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=nickkunz/smogn&amp;utm_campaign=Badge_Grade)
![GitHub last commit](https://img.shields.io/github/last-commit/enrlor/sinfpy)

## Description
InfluenceDetection is a simple algorithm to compute, as the name suggests, how influential nodes in the network are. 
The influence is computed as a value between -1 and 1. The lower the value the more susceptible the node is to influence, the higher the value the more the node exterts influence on their neighbors.
This algorithm built upon the concept of influence as an increase of similarity over time. In other words, influence over an edge e(v,w) occurrs if v is more similar to w on time t, and they got connected on t-1. The influence, in this case, is positive for w and negative to v. The magnitude of the influence is determined by the similarity increases.
Moreover, we model influence reinforcement by monitoring the influence also in time > t. By default, the algorithm foresees that the influence needs to grow over time, so we inclueded a penalizing factor. The longer the nodes were connected the higher the influence is expected to be. This parameter can be disabled.

Important: the graph has to be dynamic. 

For further detail, please refer to the paper <paper link & refs>.

The algorithm is composed of two modules (implemented in two classes) the EdgeInfluence and NodeInfluence.

EdgeInfluence computes the influence exerted on each edge. 
It takes as arguments the edge list (E) and the nodes' properties X (each entry is timed). Optionally, it also takes as parameter the customized algorithm to compute the influence over an edge, the threshold (set to .8) and the parameter to control influence reinforcement.
The first optional parameter (function to compute influence over an edge) can be either personalized or the default function included. The customized function must take as input 
(xi_old, xi_new, xj_old, xj_new, self.threshold, prev_influence)
xi_old, xi_new, xj_old, xj_new are the properties of the two nodes (old and new) to compute the similarity on. Those values need to be pandas dataframe, and can be of lenght >=1. The default algorithms assumes a len == 1. The customized algorithm can handle it differently.
In particular, the default algorithm assumes that each row in X is a node with it's list of properties. However, by customizing the similarity function X can also be a list of <userid, property name, property value, timeframe ...> to allow having different properties for each node. In this case, the influence is computed only on shared properties.

NodeInfluence computes the influence for every node from the edge influence. Since every time influence occurs one end is the influencer and the other end is the susceptible node. Therefore, the influence score on the edge is positive from one oned and negative for the other. 
By convention, for each edge e=(u,v), with id(u) < id(v), and influence exerted edge_inf(e), edge_inf(e,u) = edge_inf(e) and edge_inf(e,v) = -edge_inf(e).
The NodeInfluence class has an additional parameter consider_susceptibility, which is false by default.
consider_susceptibility = False computes the influence score of the node according to the paper [1]. #Destiny
consider_susceptibility = True computes the influence score of the node according to the paper [2], in which the influence score also encloses the susceptibility of the neighbors. In this case, multiple iterations (at least 2) of the algorithm are needed. #Journal - further details TBD

#TODO: add influence adjusted

## Requirements
 1. Python 3
 2. NumPy
 3. Pandas
 4. multiprocessing
 5. math
 6. scipy

## Installation
python
## install pypi release
pip install sinfpy

## Usage
python
## load libraries
import sinfpy

## Examples - compute influence scores

## Reference(s)
 1. Loria, E., Pirker, J., Drachen, A., & Marconi, A (2020, August). Do Influencers Influence? -- Analyzing Players' Activity in an Online Multiplayer Game. In 2020 IEEE Conference on Games (CoG) (in press). IEEE.

