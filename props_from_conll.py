"""
Usage:
  parse_props.py [INPUT] (-g|-t) [--original] [--props] [--oie] [--dep] 
  parse_props.py (-h|--help)

Parse sentences into the PropS representation scheme

Arguments:
  INPUT   input file composed of one sentence per line. if not specified, will use stdin instead
  
Options:
  -h             display this help
  -t             print textual PropS representation
  -g             print graphical representation (in svg format)
  --original     print original sentence
  --props        print the PropS representation of the input
  --oie          print open-ie like extractions
  --dep          print the intermediate dependency representation 
"""

#!/usr/bin/env python
#coding:utf8

import os, sys, codecs, time, datetime
import fileinput
import os.path
from io import StringIO
from subprocess import call

import pydot
from docopt import docopt
from propsde.applications.viz_tree import DepTreeVisualizer
from propsde.dependency_tree.tree_readers import *
from propsde.dependency_tree.german_parser import ParserDE
from propsde.graph_representation.graph_wrapper import GraphWrapper
from propsde.graph_representation.convert import convert
from propsde.graph_representation.proposition import Proposition

import sys
if sys.version_info[0] >= 3:
    str = str
    
    
stdout_encoding = sys.stdout.encoding or sys.getfilesystemencoding()

"""
Wir brauchen folgende Recommender bzw. Funktionen:

- getArgumentSpans -> Layer SemArg
-  -> SemPred
- linkArguments (to Predicate) -> SemPred
- linkSubPredicates (to Predicate) -> SemPred?
- linkSubArguments (to their head Argument) -> SemArg?
- getFullPredicateStatement (with verb lemma) -> SemPred?
- getFinalProposition with rating options -> ??? SemPred?
- getAttributes
 
"""

#import propsde.applications.run as run
def parseConll(conll):
    
    # read and process output
    graphs = read_dep_graphs(None, conll)
    
    ret = []
    i = 0
    for graph in graphs:  
        g = convert(graph)
        ret.append((g,g.tree_str))
        i += 1

    if not graphs:#Berkley bug?
        ret.append((GraphWrapper("",""),""))
    #print(ret)
    return ret

'''
def runPropsde(conll, mode):
    """
    @type   conll: file in dependency conll format
    @param  conll: the annotated text you want to analyse
    
    @type   mode:   'predicates' or 'arguments'
    @param  mode:   what kind of spans you want to get
    """

    gs = parseConll(conll)
    
    # Iterate over each graph (sentence?) and append ret with a list of spans per predicate
    ret = []
    for g,tree in gs: 
    
        if mode == 'arguments':
            ret.append(g.getArguments4Predicate(startIndex, endIndex))
        elif mode == 'predicates':
            ret.append(g.getPredicates())
        #print(ret)
    return ret
'''
def runPropsDEArguments(conll, sentIdx, tokenIdx):
    gs = parseConll(conll)
    #ret = []
    #for g,tree in gs: 
    ret = gs[sentIdx][0].getArguments4Predicate(tokenIdx)
    return ret
    
def runPropsDEEnumerations(conll, sentIdx, tokenIdx):
    gs = parseConll(conll)
    #ret = []
    #for g,tree in gs: 
    ret = gs[sentIdx][0].getEnumerations4Subtree(tokenIdx)
    return ret
    
def runPropsDEPredicates(conll):
    #print("runPropsDEPredicates(conll); conll:",conll)
    gs = parseConll(conll)
    ret = []
    strProps = []
    for g,tree in gs: 
        ret.append(g.getPredicates())
        props = g.getPropositions('pdf')
        for prop in props:
            print((str(prop)))
    return ret

#print(runPropsDEArguments("examples.conll", 10, 10))
"""
if __name__ == "__main__":
    arguments = docopt(__doc__)
    if arguments["INPUT"]:
        arguments["file"] = arguments["INPUT"]
    else:
        arguments["file"] = sys.stdin
    main(arguments)
"""

