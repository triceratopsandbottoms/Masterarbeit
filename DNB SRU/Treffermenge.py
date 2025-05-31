import requests
import re
from bs4 import BeautifulSoup as soup
import unicodedata
from lxml import etree
import pandas as pd
from collections import Counter
from string import Template
from tqdm import tqdm
import regexSearchterms as st

QUERY = Template(f'inh all {st.SEARCHSTRING} and jhr=$year and mat=books and spr=ger')
print(QUERY.substitute(year=1945))

def dnb_sru_numRecords(query):
    
    base_url = "https://services.dnb.de/sru/dnb"
    params = {'recordSchema' : 'MARC21-xml',
          'operation': 'searchRetrieve',
          'version': '1.1',
          'maximumRecords': 10,
          'query': query
         }
    r = requests.get(base_url, params=params)
    #print(r.content)
    xml = soup(r.content, features="xml")
    try:
        numRecords = xml.find('numberOfRecords').string
    except:
        numRecords = -1
    
    return numRecords

data = []
for year in range(1945, 2026):
#for searchterm in tqdm(st.SEARCHTERMS):
    #print(year)
    numRecords = dnb_sru_numRecords(QUERY.substitute(year=year))
    d = {'YEAR': year, 'NUM_RECORDS': numRecords}
    #print(numRecords)
    data.append(d.copy())
    print(year, numRecords)

df = pd.DataFrame(data)
df.to_csv("recordcountsPerYear.csv", index=False)

'''
i = 1
for year in range(1945, 2025):
    if len(results) = 50:
        i += change
        minResults = i+50-1
        if maxResults:
            change = (maxResults-minResults)/2
        else: 
            change = +1000
    elif len(results) = 0:
        i += change
        maxResults = i-1
    else: numResults = i + len(results) -1

'''
    


#print("file records.xml saved")
 
#saved_records = open("records.xml", "r")

#print(len(records), 'Ergebnisse')

#output = [parse_record(record) for record in records]
#df = pd.DataFrame(output)
#df.to_csv("patella.csv", index=False)
