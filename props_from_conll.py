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
- getPredicateSpan -> SemPred
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

    
def main(arguments):
    
    outputType = 'html'
    sep = "<br>"
    if arguments['-t']:
        outputType = 'pdf'
    sep = "\n"
        
    graphical = (outputType=='html')
    
    gs = parseConll(arguments["file"])
        
    i = 0

    for g,tree in gs: 
    
        if arguments['INPUT']:
            file_name = os.path.splitext(arguments['INPUT'])[0] + str(i)
        else: 
            file_name = 'output' + str(i)
                
        #print open ie like extractions
        if (arguments["--oie"]):
            for prop in g.getPropositions('pdf'):
                print(str(prop))
            for span in g.getArgumentSpans():
                print(str(span))
        i += 1
        

if __name__ == "__main__":
    arguments = docopt(__doc__)
    if arguments["INPUT"]:
        arguments["file"] = arguments["INPUT"]
    else:
        arguments["file"] = sys.stdin
    main(arguments)


