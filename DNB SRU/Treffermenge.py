import requests
import re
import unicodedata
import random
import time
import pandas as pd
import dnb_search as search
from bs4 import BeautifulSoup as soup
from pyzotero import zotero
from lxml import etree
from string import Template
from tqdm import tqdm

QUERY = Template(f'inh all {search.SEARCHSTRING} and jhr=$year and mat=books and spr=ger and location=leipzig')
CREATOR_DICT = {'abr': 'contributor', 'aft': 'contributor', 'aui': 'contributor', 'aut': 'author', 'clb': 'contributor', 'cov': 'contributor', 'cre': 'contributor', 'ctb': 'contributor', 'edc': 'series editor', 'edd': 'editor', 'edt': 'editor', 'ill': 'contributor', 'oth': 'contributor', 'trl': 'translator', 'wfw': 'contributor', 'win': 'contributor'}
LIBRARY_ID = 6014926
API_KEY = 'wyvQS9dKWZVY7yoEuJLPCEXW'

#print(QUERY.substitute(year=1945))
zot = zotero.Zotero(LIBRARY_ID, 'group', API_KEY)

def getNumRecordsForYears(firstyear, lastyear, querytemplate):
    '''
    firstyear:      first year the number of search records is wanted
        Type:       int
        
    lastyear:       last year the number of search records is wanted
        Type:       int
        
    querytemplate:  DNB SRU query for the with a fillable year
        Type:       string.Template
        QueryLang:  QCL (http://www.loc.gov/standards/sru/cql/index.html)
        Tags:       https://www.dnb.de/DE/Service/Hilfe/Katalog/kataloghilfeExpertensuche_node.html
    
    OUTPUT:
        a list of the years with their corresponding number of search records
        Type:       pandas.DataFrame
    '''
    
    data = []
    for year in tqdm(range(firstyear, lastyear+1)):
        numRecords = dnb_sru_numRecords(querytemplate.substitute(year=year))
        d = {'YEAR': year, 'NUM_RECORDS': numRecords}
        data.append(d.copy())
        #print(year, numRecords)

    df = pd.DataFrame(data)
    
    return df

def dnb_sru(query, maxRecords=None, startRecord=None, recordSchema='MARC21plus-1-xml'):
    base_url = "https://services.dnb.de/sru/dnb"
    params = {'recordSchema' : recordSchema,
            'operation': 'searchRetrieve',
            'version': '1.1',
            'query': query}
    if maxRecords:
        params.update({'maximumRecords': maxRecords})
    if startRecord:
        params.update({'startRecord': startRecord})
    
    r = requests.get(base_url, params=params)
    
    return r
    
def dnb_sru_numRecords(query):
    r = dnb_sru(query, 1)
    xml = soup(r.content, features="xml")
    numRecordsField = xml.find('numberOfRecords')
    numRecords = int(numRecordsField.string) if  numRecordsField else 2 #-1
    
    return numRecords

def getYearSamples(df, samplesize, colName='NUM_RECORDS'):
    samples = []
    rawSample = []
    for index, row in df.iterrows():
        samplesize_ = row['NUM_RECORDS'] if row['NUM_RECORDS']<samplesize else samplesize
        sample = random.sample(range(1, row['NUM_RECORDS']+1), k=samplesize_)
        #df['SAMPLES'] = sample
        samples.append(sample)
        for num in sample:
            rawSample.append({'YEAR': row['YEAR'], 'ORDER': sample.index(num), 'RECORD_POS': num})
    #print(df)
    numColumns = len(df.columns)
    df.insert(numColumns, 'SAMPLE', samples)
    sample_df = pd.DataFrame(rawSample)
    
    return sample_df

def getMarcSubfield(xml, datafield, subfield, mode='text'):
    ns = {"marc":"http://www.loc.gov/MARC21/slim"}

    fields = xml.findall(f"marc:datafield[@tag = {repr(datafield)}]/marc:subfield[@code = {repr(subfield)}]", namespaces=ns)
    if mode=='text':
        if fields != []:
            text = fields[0].text
        else:
            text = ''
        return text
    elif mode=='fields':
        return fields
    elif mode=='field':
        return fields[0]
    else:
        raise ValueError(f"Mode '{mode}' does not exist. Available modes are: 'text'(default) and 'field'.")

def getMarcFields(xml, datafield):
    ns = {"marc":"http://www.loc.gov/MARC21/slim"}

    fields = xml.findall(f"marc:datafield[@tag = {repr(datafield)}]", namespaces=ns)
    return fields
    
def getMarcSubfieldOf(xml_datafield, subfield, mode='text'):
    ns = {"marc":"http://www.loc.gov/MARC21/slim"}

    fields = xml_datafield.findall(f"marc:subfield[@code = {repr(subfield)}]", namespaces=ns)
    if mode=='text':
        if fields != []:
            text = fields[0].text
        else:
            text = ''
        return text
    elif mode=='texts':
        if fields != []:
            texts = ', '.join([f.text for f in fields])
        else:
            text = ''
        return text
    elif mode=='fields':
        return fields
    elif mode=='field':
        if fields != []:
            return fields[0]
    else:
        raise ValueError(f"Mode '{mode}' does not exist. Available modes are: 'text'(default) and 'field'.")
        
def getControlfieldText(xml, controlfield):
    ns = {"marc":"http://www.loc.gov/MARC21/slim"}

    field = xml.findall(f"marc:controlfield[@tag = {repr(controlfield)}]", namespaces=ns)
    if field != []:
        text = field[0].text
    else:
        text = ''
    return text

def marcxml2zotEntry(xml_marc):
    
    zotEntry = zot.item_template('book')
    
    #idn -> key
    idn = getControlfieldText(xml_marc, '001')
    zotEntry.update({'extra': 'IDN: ' + idn + '\n'})
    zotEntry['url'] = f'https://d-nb.info/{idn}'
    
    #Titel $a -> title
    zotEntry['title'] = getMarcSubfield(xml_marc, '245', 'a')
    title2 = getMarcSubfield(xml_marc, '245', 'b') #additional title
    
    if zotEntry['title'] and title2:
        zotEntry['title'] += ': ' + title2
    
    #creator(s) - main entry
    creatorfields = []
    person = getMarcFields(xml_marc, '100')
    if person:
        creatorfields.append(*person)
    else:
        corporation = getMarcFields(xml_marc, '110')
        if corporation:
            creatorfields.append(*corporation)
        else:
            meeting = getMarcFields(xml_marc, '111')
            if meeting:
                creatorfields.append(*meeting)
    # creators - additional entries
    people = getMarcFields(xml_marc, '700')
    corporations = getMarcFields(xml_marc, '710')
    meetings = getMarcFields(xml_marc, '711')
    for p in people:
        creatorfields.append(p)
    for c in corporations:
        creatorfields.append(c)
    for m in meetings:
        creatorfields.append(m)
    #print(creatorfields)
    creators = []
    for f in creatorfields:
        if f.get('tag') in ['100', '700']:
            name = getMarcSubfieldOf(f, 'a')
            rel = getMarcSubfieldOf(f, '4')
            creator = {'creatorType': rel}
            ind1 = f.get('ind1')
            #print('person', name)
            if ind1=='0': #name is just a first name
                num = getMarcSubfieldOf(f, 'b') #Numeration 
                tit = getMarcSubfieldOf(f, 'c') #Titles and words associated with a name
                if num != '':
                    name += ' ' + num
                if tit != '':
                    name += ', ' + tit
                creator['name'] = name
                creators.append(creator.copy())
            elif ind1=='1': #name has format 'surname, forename(s)'
                name_spl = name.split(', ', 1)
                creator['lastName'] = name_spl[0]
                creator['firstName'] = name_spl[1]
                creators.append(creator.copy())
            elif ind1=='3': #name is a family/clan/dynasty name
                creator['name'] = name
                creators.append(creator.copy())
        if f.get('tag') in ['110', '710']:
            corpName = getMarcSubfieldOf(f, 'a')
            subdivision = getMarcSubfieldOf(f, 'b', mode='texts')
            #print('corp', corpName)
            if subdivision != '':
                corpName += ', ' + subdivision
            rel = getMarcSubfieldOf(f, '4')
            creator = {'creatorType': rel,'name': corpName}
            creators.append(creator.copy())
        if f.get('tag') in ['111', '711']:
            meetingName = getMarcSubfieldOf(f, 'a')
            numeration = getMarcSubfieldOf(f, 'n')
            #print('meeting', meetingName)
            if numeration != '':
                meetingName += ', ' + numeration
            rel = getMarcSubfieldOf(f, '4')
            creator = {'creatorType': rel, 'name': meetingName}
            creators.append(creator.copy())
    #print(creators)
            
    zotEntry['creators'] = []
    for creator in creators:
        type_=creator['creatorType']
        if type_=='pbl':
            continue
        if type_ in CREATOR_DICT.keys():
            creator['creatorType'] = CREATOR_DICT[type_]
            zotEntry['creators'].append(creator.copy())
        else:
            zotEntry['extra'] += f'Creator ({type_}): '
            if creator['name'] != []:
                zotEntry['extra'] += creator['name']
            else:
                zotEntry['extra'] += creator['lastName'] + ' || ' + creator['firstName']

    #ISBN
    zotEntry['ISBN'] = getMarcSubfield(xml_marc, '020', 'a') #new isbn
    if not zotEntry['ISBN']:
        zotEntry['ISBN'] = getMarcSubfield(xml_marc, '024', 'a') #old isbn

    #abstractNote / Inhaltstext
    urlTypes = getMarcSubfield(xml_marc, '856', '3', mode='field')
    urlTypes = list(map(lambda t: t.text, urlTypes))
    try:
        indAbstract = urlTypes.index('Inhaltstext')
    except:
        abstractNote = ''
    else:
        links = getMarcSubfield(xml_marc, '856', 'u', mode='field')
        abstractLink = links[indAbstract].text
        r = requests.get(abstractLink)
        html = soup(r.content.decode(), features='lxml')
        abstractNote = html.get_text()
    zotEntry['abstractNote'] = abstractNote
    
    zotEntry['language'] = getMarcSubfield(xml_marc, '041', 'a')
    zotEntry['edition'] = getMarcSubfield(xml_marc, '250', 'a')
    zotEntry['shortTitle'] = getMarcSubfield(xml_marc, '246', 'a')
    zotEntry['publisher'] = getMarcSubfield(xml_marc, '264', 'b')
    zotEntry['place'] = getMarcSubfield(xml_marc, '264', 'a')
    zotEntry['numPages'] = getMarcSubfield(xml_marc, '300', 'a')
    zotEntry['series'] = getMarcSubfield(xml_marc, '490', 'a')
    zotEntry['seriesNumber'] = getMarcSubfield(xml_marc, '490', 'v')
    zotEntry['volume'] = getMarcSubfield(xml_marc, '830', 'v')
    zotEntry['libraryCatalog'] = 'Katalog der Deutschen Nationalbibliothek'
    zotEntry['archive'] = 'Deutsche Nationalbibliothek Leipzig'
    zotEntry['accessDate'] = 'CURRENT_TIMESTAMP'
    
    
    #callNumber / Signatures
    r_pica = dnb_sru(idn, recordSchema='PicaPlus-xml')
    xml_pica = soup(r_pica.content, features="xml")
    record_pica = xml_pica.find('ppxml:record')
    owners_pica = record_pica.find_all('ppxml:owner')
    signatures = []
    for owner in owners_pica:
        lib_id = owner.local.find('tag', {'id': '101@'}).find('subf', {'id': 'a'})
        if lib_id:
            lib_id = lib_id.text
        if lib_id=='1': # 1 = Leipzig, 2 = Frankfurt, 3 = Deutsches Musikarchiv
            signature_tags = owner.find_all('tag', {'id': '209A'})
            if signature_tags:
                for tag in signature_tags:
                    tag = tag.find('subf', {'id': 'a'})
                    if tag:
                        signatures.append(tag.text)
    zotEntry['callNumber'] = '; '.join(signatures)
    
    #print(zotEntry)
    return zotEntry
    
#df = getNumRecordsForYears(2022, 2023, QUERY)
#print(df)
#df.to_csv("recordcountsPerYear.csv", index=False)

#random.seed(312487687)
#sample_df = getYearSamples(df, 10)
#query = '1331715741'
#for index, row in sample_df.iterrows():
tocText = 'Hormone und Genitalorgane .................................................................. 606'

for term in search.SEARCHTERMS:
    #prepare term for regex-search 
    term = term.replace('*', '') # right-truncation * -> 0 or more chars (lazy)
    #term = '\\\\b' + term.replace(' ', '\\\\b \\\\b') + '\\\\b'  # add word boundaries around a space
    #term = term + '\\b' # add word boundaries at beginning and end
    print(term)
    #print(repr(term)[1:-1])
    #tocText = re.sub(term, r'<span style="background-color: #f1983780">$&<\/span>', tocText, re.I)
    text = tocText.replace(term, f'<span style="background-color: #f1983780">{term}<\/span>')
        
print(text)

'''
for i in [0]:
    #year = row['YEAR']
    #order = row['ORDER']
    #recordPos = row['RECORD_POS']
    
    year = '1975'
    order = '3'
    recordPos = '1'
    
    #get marc xml record from the dnb catalog via sru and isolate record
    r_marc21 = dnb_sru(QUERY.substitute(year=year), startRecord=recordPos)
    xml_marc = soup(r_marc21.content, features="xml")
    record_marc = xml_marc.find('record', {'type':'Bibliographic'})
    str_marc_record = unicodedata.normalize("NFC", str(record_marc))
    xml_marc_record = etree.fromstring(str_marc_record)

    #convert record to zotEntry
    zotEntry = marcxml2zotEntry(xml_marc_record)
    zotEntry['date'] = year
    zotEntry['extra'] = f'order: {order}\n' + zotEntry['extra']
    zotEntry.update({'key': f'{year}P{order}'})
    
    base_url = zotEntry['url']
    
    #create attachments for zotEntry:
    # 1. link to the table of content as pdf
    zotAtt_toc_pdf = zot.item_template('attachment', 'linked_url')
    zotAtt_toc_pdf['parentItem'] = zotEntry['key']
    zotAtt_toc_pdf['title'] = f'Inhaltsverzeichnis_{year}_{order}.pdf'
    zotAtt_toc_pdf['contentType'] = 'application/pdf'
    zotAtt_toc_pdf['url'] = f'{base_url}/04'
    
    # 2. table of content (toc) text
    zotAtt_toc_text = zot.item_template('note')
    zotAtt_toc_text['parentItem'] = zotEntry['key']
    zotAtt_toc_text['title'] = f'Inhaltsverzeichnis-Text_{year}_{order}.pdf'
    r = requests.get(f'{base_url}/04/text')
    html = soup(r.content.decode(), features='lxml')
    tocText = html.get_text()
    
    for term in search.SEARCHTERMS:
        #prepare term for regex-search 
        term = term.replace('*', '.*?') # right-truncation * -> 0 or more chars (lazy)
        #term = '\\b' + term.replace(' ', '\\b \\b') + '\\b'  # add word boundaries around a space
        #term = term + '\\b' # add word boundaries at beginning and end
        #print(term)
        #print(repr(term)[1:-1])
        #tocText = re.sub(term, r'<span style="background-color: #f1983780">$&<\/span>', tocText, re.I)
        text = re.sub('\\b' + term.replace(' ', '\\b \\b') + '\\b', 'FOUND', tocText, 1, re.I)
        
    print(text)
    zotAtt_toc_text['note'] = f'<div data-schema-version="9"><p>{tocText}</p>\n</div>'
    #zot.create_items([zotEntry, zotAtt_toc_pdf, zotAtt_toc_text])
    
    attachmentPaths = []
    with open(f'tmp/MARC21-xml_{year}_{order}.mrcx', 'w') as f:
        f.write(str_marc_record)
    
    attachmentPaths.append(f'tmp/MARC21-xml_{year}_{order}.mrcx')
    
    #zot.attachment_simple(attachmentPaths, zotEntry['key'])
    
    
'''