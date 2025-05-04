import requests
from bs4 import BeautifulSoup as soup
import unicodedata
from lxml import etree
import pandas as pd
from collections import Counter

def dnb_sru(query):
    
    base_url = "https://services.dnb.de/sru/dnb"
    params = {'recordSchema' : 'MARC21-xml',
          'operation': 'searchRetrieve',
          'version': '1.1',
          'maximumRecords': '100',
          'query': query
         }
    r = requests.get(base_url, params=params)
    xml = soup(r.content)
    records = xml.find_all('record', {'type':'Bibliographic'})
    
    if len(records) < 100:
        
        return records
    
    else:
        
        num_results = 100
        i = 101
        while num_results == 100:
            
            params.update({'startRecord': i})
            r = requests.get(base_url, params=params)
            xml = soup(r.content)
            new_records = xml.find_all('record', {'type':'Bibliographic'})
            records+=new_records
            i+=100
            num_results = len(new_records)
            
        return records
        
def parse_record(record):
    
    ns = {"marc":"http://www.loc.gov/MARC21/slim"}
    xml = etree.fromstring(unicodedata.normalize("NFC", str(record)))
    
    #link
    link = xml.xpath("marc:datafield[@tag = '856']/marc:subfield[@code = 'u']", namespaces=ns)
    
    try:
        link = link[0].text
    except:
        link = "unkown"
        
    meta_dict = {"link":link + '/text'}
    
    return meta_dict
    
records = dnb_sru('inh=Sandwespe')
print(len(records), 'Ergebnisse')

output = [parse_record(record) for record in records]
df = pd.DataFrame(output)

print(df.to_string(index=False))