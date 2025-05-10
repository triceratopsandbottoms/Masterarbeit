import requests
import re
from bs4 import BeautifulSoup as soup
import unicodedata
from lxml import etree
import pandas as pd
from collections import Counter

def dnb_sru(query, outputfile=None):
    
    base_url = "https://services.dnb.de/sru/dnb"
    params = {'recordSchema' : 'MARC21-xml',
          'operation': 'searchRetrieve',
          'version': '1.1',
          'maximumRecords': '100',
          'query': query
         }
    r = requests.get(base_url, params=params)
    xml = soup(r.content, features="xml")
    records = xml.find_all('record', {'type':'Bibliographic'})
    #xml_r = soup(records)
    #print(records[0].string)
    if outputfile:
        output = [parse_record(record) for record in records]
        df = pd.DataFrame(output)
        df.to_csv(outputfile, index=False)    
    
    if len(records) < 100:
        
        return records
    
    else:
        
        num_results = 100
        i = 101
        while num_results == 100:
            
            params.update({'startRecord': i})
            r = requests.get(base_url, params=params)
            xml = soup(r.content, features="xml")
            new_records = xml.find_all('record', {'type':'Bibliographic'})
            #records+=new_records
            if outputfile:
                output = [parse_record(record) for record in new_records]
                df = pd.DataFrame(output)
                df.to_csv(outputfile, index=False, mode='a', header=False)
            i+=100
            print("Current record count:", i-1)
            num_results = len(new_records)
            
        return num_results+i

#Function für Titeldaten in MARC21
def parse_record(item):

    ns = {"marc":"http://www.loc.gov/MARC21/slim"}
    xml = etree.fromstring(unicodedata.normalize("NFC", str(item)))
    
    
    #idn
    idn = xml.findall("marc:controlfield[@tag = '001']", namespaces=ns)
    try:
        idn = idn[0].text
    except:
        idn = 'N/A' 
        
    #jahr2
    year2 = xml.findall("marc:controlfield[@tag = '008']", namespaces=ns)
    try:
        year2 = year2[0].text[7: 11]
    except:
        year2 = 0
    
    #creator
    creator1 = xml.findall("marc:datafield[@tag = '100']/marc:subfield[@code = 'a']", namespaces=ns)
    creator2 = xml.findall("marc:datafield[@tag = '110']/marc:subfield[@code = 'a']", namespaces=ns)
    subfield = xml.findall("marc:datafield[@tag = '110']/marc:subfield[@code = 'e']", namespaces=ns)
    
    if creator1:
        creator = creator1[0].text
    elif creator2:
        creator = creator2[0].text
        if subfield:
            creator = creator + " [" + subfield[0].text + "]"
    else:
        creator = "N/A"
    
    #Titel $a
    title = xml.findall("marc:datafield[@tag = '245']/marc:subfield[@code = 'a']", namespaces=ns)
    title2 = xml.findall("marc:datafield[@tag = '245']/marc:subfield[@code = 'b']", namespaces=ns)
    
    if title and not title2:
        titletext = title[0].text
    elif title and title2:
        titletext = title[0].text + ": " + title2[0].text
    else:
        titletext = "N/A"
    
    
    #date
    dates = xml.findall("marc:datafield[@tag = '264']/marc:subfield[@code = 'c']", namespaces=ns)
    try:
        date = dates[0].text
    except:    
        date = 'N/A'

    #date-multifield
    multidate = [d.text for d in dates]
        
    #year
    year = None
    try:
        match = "^\d{4}$"
        year = [re.search(match, d).group() for d in multidate if re.search(match, d)][0]
    except:
        try:
            match = "\d{4}"
            year = [re.search(match, d).group() for d in multidate if re.search(match, d)][0]
        except:
            try:
                match = "(?:^|[^\d])(\d{2})(?:$|[^\d\.])"
                year = [re.search(match, d).group() for d in multidate if re.search(match, d)][0]
                if int(year) < 45:
                    year = str(2000+int(year))
                else:
                    year = str(1900+int(year))
            except:
                year = 'N/A'
                
    #publisher
    publ = xml.findall("marc:datafield[@tag = '264']/marc:subfield[@code = 'b']", namespaces=ns)
    try:
        publ = publ[0].text
    except:    
        publ = 'N/A'
        
        
    #URN
    testurn = xml.findall("marc:datafield[@tag = '856']/marc:subfield[@code = 'x']", namespaces=ns)
    urn = xml.findall("marc:datafield[@tag = '856']/marc:subfield[@code = 'u']", namespaces=ns)
    
    if testurn:
        urn = urn[0].text
    else:    
        urn = 'N/A'
        
        
    #ISBN
    isbn_new = xml.findall("marc:datafield[@tag = '020']/marc:subfield[@code = 'a']", namespaces=ns)
    isbn_old = xml.findall("marc:datafield[@tag = '024']/marc:subfield[@code = 'a']", namespaces=ns)
    if isbn_new:
        isbn = isbn_new[0].text
    elif isbn_old: 
        isbn = isbn_old[0].text
    else:    
        isbn = 'N/A'

    
    meta_dict = {"IDN":idn, "CREATOR":creator, "TITLE": titletext, "DATE":date, "YEAR":year, "YEAR2":year2, "PUBLISHER":publ, "URN":urn, "ISBN":isbn}
    
    return meta_dict


records = dnb_sru('inh all "pankre*" and jhr within "1945 *" and mat=books', "pankre.csv")

#print("file records.xml saved")
 
#saved_records = open("records.xml", "r")

#print(len(records), 'Ergebnisse')

#output = [parse_record(record) for record in records]
#df = pd.DataFrame(output)
#df.to_csv("patella.csv", index=False)
