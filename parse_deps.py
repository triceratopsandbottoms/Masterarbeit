"""
Usage:
  parse_deps.py [INPUT]
  parse_deps.py (-h|--help)

Parse a text into a conll file

Arguments:
  INPUT input file. If not specified, will use stdin instead
  
Options:
  -h             display this help
"""

import os, sys, codecs
import fileinput
import os.path
from io import StringIO
import urllib.request
import urllib.parse
from docopt import docopt

if sys.version_info[0] >= 3:
    str = str
stdout_encoding = sys.stdout.encoding or sys.getfilesystemencoding()

def parse_dependencies_to_conll_file(text, path):
    if path:
        file = open(path,'w')
        file.write("")
    chunks = text.splitlines()
    errors = 0
    for chunk in chunks:
        if chunk != "":
            params = {
                "text": chunk,
                "format": "conll"
            }
            args = urllib.parse.urlencode(params).encode("utf-8")
            #TODO: Gibt es eine Möglichkeit, das sentencizing zu überspringen?
            req = "http://localhost:5004/parse/?"+args.decode("utf-8")
            try:
                f = urllib.request.urlopen(req)
                if path:
                    file = open(path,'a')
                    file.write(f.read().decode('utf-8'))
                else:
                    print(f.read().decode('utf-8'))
                #return 0
            except Exception as ex:
                print(ex, "\n", chunk)
                errors += 1
        else:
            f = urllib.request.urlopen(req)
            if path:
                file = open(path,'a')
                file.write("\n")
            else:
                print("\n")
    return errors

def main(arguments): 
    if arguments['INPUT']:
        inPath = arguments['INPUT']
        inPaths = []
        if os.path.isfile(inPath):
            inPaths = [inPath]
        else:
            inPaths = [os.path.join(dirpath,f) for (dirpath, dirnames, filenames) in os.walk(inPath) for f in filenames]
        for path_ in inPaths:
            outPath = os.path.splitext(path_)[0] + ".conll"
            f = open(path_,'r')
            text = f.read()
            err = parse_dependencies_to_conll_file(text, outPath)
            print("Error:", err)
    #else: 
    #    outPath = 'output' + ".conll"
    #print(open(conll).read())
    
    # while True:
        # text = input("Enter example text: ")
        # print("Parsing example text to conll file")
        # err = parse_dependencies_to_conll_file(text, conll)
        # print("Error:", err)
        # print(open(conll).read())
    
if __name__ == "__main__":
    arguments = docopt(__doc__)
    if arguments["INPUT"]:
        arguments["file"] = arguments["INPUT"]
    else:
        arguments["file"] = sys.stdin
    main(arguments)