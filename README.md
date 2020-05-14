## Detecting Semantic Influential Nodes in Time-Evolving Graphs
[![PyPI version](https://badge.fury.io/py/sinfpy.svg)](https://badge.fury.io/py/sinfpy)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Build Status](https://travis-ci.com/nickkunz/smogn.svg?branch=master)](https://travis-ci.com/enrlor/sinfpy)
<!-- [![Codacy Badge](https://api.codacy.com/project/badge/Grade/1bfe5a201f3b4a9787c6cf4b365736ed)](https://www.codacy.com/manual/enrlor/sinfpy?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=nickkunz/smogn&amp;utm_campaign=Badge_Grade)
![GitHub last commit](https://img.shields.io/github/last-commit/enrlor/sinfpy)-->

## Description
Semantic Influence Detection is a simple algorithm to compute how influential the nodes in the network are. The influence is computed as a value between -1 and 1. The lower the value the more susceptible the node is to influence, the higher the value the more the node exterts influence on their neighbors.
The algorithm is built upon the concept of influence as an increase of similarity over time. In other words, influence over an edge e(v,w) occurrs if v is more similar to w on time t, and they got connected on t-1. The influence, in this case, is positive for w and negative to v. The magnitude of the influence is determined by the similarity increases.
Moreover, we model influence reinforcement by monitoring the influence also in time > t. 

The algorithm is composed of two modules (implemented in two classes) the EdgeInfluence and NodeInfluence classes; both support multiprocessing and work with pandas dataframe.

EdgeInfluence computes the influence exerted on each edge. 
It takes as arguments the edge list (E) and the nodes' properties X; each entry is timed. It also takes as parameter the customized algorithm to compute the influence over an edge, the threshold (set to .8) and the parameter to control influence reinforcement.
The function to compute influence over an edge can either be user-defined or the default function included. The customized function must comply with the followign signature: (xi_t-1, xi_t, xj_t-1, xj_t, threshold, inf_t-1).
The first 4 arguments (xi_t-1, xi_t, xj_t-1, xj_t) are the properties of the two nodes i and j to compute the similarity on. Those values need to be pandas dataframe. The default algorithms assumes a size of 1. We will provide examples of why and how the function can be defined to handle bigger dataframes.
In particular, the default algorithm assumes that each row in X is a node with it's list of properties. However, by customizing the similarity function X can also be a list of <userid, property name, property value, timeframe ...> to allow having different properties for each node. In this case, the influence should be computed only on shared properties.
By default, the algorithm controls influence reinforcement over time, so we inclueded a penalizing factor. More specifically, the assumption is that, when influence occurrs, it should increase as the connection among the nodes persist. This parameter can be disabled.

NodeInfluence computes the influence for every node from the edge influence. Since every time influence occurs one end is the influencer and the other end is the susceptible node. Therefore, the influence score on the edge is positive from one oned and negative for the other. 
By convention, for each edge e=(u,v), with id(u) < id(v), and influence exerted edge_inf(e), edge_inf(e,u) = edge_inf(e) and edge_inf(e,v) = -edge_inf(e).

Note that this project is the outcome of a research study and, as such, in continuous update. Thus, many features are yet to be implemented.

For further details, please refer to the paper mentioned in the Reference(s) section.

## Requirements
1. Python 3
2. NumPy
3. Pandas
4. multiprocessing
5. scipy
6. math

## Installation pypi release
pip install sinfpy

## Usage
python3

## Load libraries
import sinfpy

## Reference(s)
1. Loria, E., Pirker, J., Drachen, A., & Marconi, A (2020, August). Do Influencers Influence? - Analyzing Players' Activity in an Online Multiplayer Game. In 2020 IEEE Conference on Games (CoG) (in press). IEEE.

