# Detecting Semantic Influential Nodes in Time-Evolving Graphs
[![PyPI version](https://badge.fury.io/py/sinfpy.svg)](https://badge.fury.io/py/sinfpy)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Build Status](https://travis-ci.com/nickkunz/smogn.svg?branch=master)](https://travis-ci.com/enrlor/sinfpy)

## Description
Semantic Influence Detection (sinfpy) is a simple algorithm to compute how influential the nodes in the network are. The influence scores are computed as values in [-1;1]. The lower the value the more *susceptible* the node is to influence, the higher the value the more the node *exterts influence* on their neighbors.
The algorithm is built upon the concept of influence as an increase of similarity over time. In other words, influence over an edge e(v,w) occurrs if v is more similar to w on time t, and they got connected on t-1. The influence, in this case, is positive for w and negative to v. The magnitude of the influence is determined by the similarity increases.
To compute the influence, timed information of players' properties are needed. The properties are user-defined, and thus, the concept of influence is tied to the properties of interest. The network can either be dynamic or static, in terms of the connection among the nodes. In case of dynamic connections the persistence of the disappeareance of a node is taken into consideration.

The algorithm is composed of two modules (implemented in two classes) the **EdgeInfluence** and **NodeInfluence** classes.

### Edges Influence
The class EdgeInfluence computes the influence exerted on each edge of the network as a result of the nodes' behaviors and interactions over the observatiob period. 
The class foresees a number of optional parameters which allow the computation to meet the context-specific requirements. 
While the class encloses a default function to compute the edge influence, it can be customized to better adapt to the use case. The default function assumes that (1) the values are already normalized, (2) all the properties in the data DataFrame X are relevant for the computation of the influence score, and (3) the similarity function is either the default function or the one specified in the class initialization.
The user-defined function must be passed as argument in the class initialization, and must comply with the followign signature: 
- ![formula](https://render.githubusercontent.com/render/math?math=x_{i}^{t-1}); properties values for node i prior the connection
- ![formula](https://render.githubusercontent.com/render/math?math=x_{i}^{t}); properties values for node i at the time of the connection
- ![formula](https://render.githubusercontent.com/render/math?math=x_{j}^{t-1}); properties values for node j prior the connection
- ![formula](https://render.githubusercontent.com/render/math?math=x_{j}^{t}); properties values for node j at the time of the connection
- threshold; as defined in the instantiation phase
- ![formula](https://render.githubusercontent.com/render/math?math=influence^{t-1}); the influence score, if any influence was exerted in the past
- similarity_fun; as defined in the instantiation phase, used to compute the magnitude of the influence

The edge influence computed refers to the magnitude of the influence exerted. Therefore, it has a positive value for one end of the edge (influencer) and a negative value for the other (influenced). 

### Nodes Influence
The class NodeInfluence computes the final value of the influence score for every node, as an aggregated of the influence of the edges they were involved in. 

## Disclaimer!
Note that this project is the outcome of a research study and, as such, in continuous update. Thus, many features are yet to be implemented. If you find any bugs or would like any additional features please contact me.

For further details, please refer to the paper mentioned in the Reference section.

## Requirements
1. Python 3
2. NumPy
3. Pandas
4. ray
5. psutil 
6. scipy

## Installation pypi release
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install sinfpy.
```bash
pip install sinfpy
```

## Load libraries
```python
import sinfpy.semantic_influence as sinf

E, X = filereader(fname)
ei = sinf.EdgeInfluence(E, X, participation_influence)
updated_E = ei()
ni = sinf.NodeInfluence(updated_E, stats = True)
influences = ni()
```

## Reference
1. Loria, E., Pirker, J., Drachen, A., & Marconi, A (2020, August). Do Influencers Influence? - Analyzing Players' Activity in an Online Multiplayer Game. In 2020 IEEE Conference on Games (CoG). IEEE. InPress.

