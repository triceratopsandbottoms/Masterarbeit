import os, sys, codecs
import fileinput
import os.path
from io import StringIO
import urllib.request
import urllib.parse

def parse_dependencies_to_conll_file(text, path):
    params = {
        "text": text,
        "format": "conll"
    }
    args = urllib.parse.urlencode(params).encode("utf-8")
    req = "http://localhost:5003/parse/?"+args.decode("utf-8")
    try:
        f = urllib.request.urlopen(req)
        if path:
            file = open(path,'w')
            file.write(f.read().decode('utf-8'))
        else:
            print(f.read().decode('utf-8'))
        return 0
    except Exception as ex:
        print(ex)
        return 1
        
conll = "corzu.conll"
while True:
    text = input("Enter example text: ")
    print("Parsing example text to conll file")
    err = parse_dependencies_to_conll_file(text, conll)
    print("Error:", err)
    print(open(conll).read())