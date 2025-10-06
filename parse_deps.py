"""
Usage:
  parse_deps.py [INPUT]
  parse_deps.py (-h|--help)

Parse text(s) into conll file(s) and upload to Inception

Arguments:
  INPUT input file or directory. If not specified, will use stdin instead
  
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
from pycaprio import Pycaprio
from pycaprio.mappings import InceptionFormat, DocumentState
from dotenv import dotenv_values

secrets = dotenv_values(".env")

inception_url = secrets['INCEPTION_URL']
inception_user = secrets['INCEPTION_USER']
inception_pw = secrets['INCEPTION_PW']
project_id = secrets['PROJECT_ID']
INCEPTION_FORMAT = InceptionFormat.CONLL2006

client = Pycaprio(inception_url, authentication=(inception_user, inception_pw))
    
if sys.version_info[0] >= 3:
    str = str
stdout_encoding = sys.stdout.encoding or sys.getfilesystemencoding()

# @deprecated
def old_parse_dependencies_to_conll_file(text, path):
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
            req = "http://localhost:5003/parse/?"+args.decode("utf-8")
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

def parse_dependencies_to_conll_file(text, path=None):
    if path:
        file = open(path,'w')
        file.write("")
    text = text.replace("\r\n"," ")
    conll = ""
    errors = 0
    counter = 0
    success = True
    while len(text) > len(conll) and counter < 3:
        params = {
            "text": text,
            "format": "conll"
        }
        args = urllib.parse.urlencode(params).encode("utf-8")
        req = "http://localhost:5003/parse/?"+args.decode("utf-8")
        try:
            f = urllib.request.urlopen(req)
            conll = f.read().decode('utf-8')
            if path:
                file = open(path,'a')
                file.write(conll)
            else:
                print(conll)
            #return 0
        except Exception as ex:
            print(ex)
            errors += 1
        counter += 1
        if counter == 3 and errors == 3: success = False
    return success, errors

def postDocumentToInception(title, filepath):
    doc_file = open(filepath,'rb')
    new_document = None
    try:
        new_document = client.api.create_document(project_id, title, doc_file, document_format=INCEPTION_FORMAT)
        return(new_document) # <Document #5: Test document name (Project: 1)>
    except Exception as ex:
        print(ex)
        return None

def main(arguments): 
    if arguments['INPUT']:
        inPath = arguments['INPUT']
        inPaths = []
        if os.path.isfile(inPath):
            inPaths = [inPath]
        else:
            inPaths = [os.path.join(dirpath,f) for (dirpath, dirnames, filenames) in os.walk(inPath) for f in filenames]
        for path_ in inPaths:
            f = os.path.splitext(path_)[0]
            filename = os.path.split(f)[1]
            outPath = "./tmp/" + filename + ".conll"
            f = open(path_,'r')
            text = f.read()
            parsed = parse_dependencies_to_conll_file(text, outPath)
            print(filename)
            if parsed[0]:                 
                print("    Parsing completed at",parsed[1]+1,". try.")
                new_document = postDocumentToInception(filename, outPath)
                if new_document:
                    os.remove(outPath)
                    print("    Posted to Inception.")
                else:
                    print("    ERROR: Posting to Inception failed.")
            else:
                print("    ERROR: Parsing to conll failed.")
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