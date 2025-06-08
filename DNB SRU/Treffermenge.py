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

def highlightedMatch(matchobj):
    global counter
    global matchList
    counter += 1
    replacement = Template(f'{matchobj[1]}<span $set_id style="background-color: #ffd40080">{matchobj[2]}</span>{matchobj[3]}')
    matchList.append(f'{replacement.substitute(set_id="")} <a href="#M{counter}">Zum Eintrag</a>')
    return '\n' + replacement.substitute(set_id=f'id="M{counter}"') + '\n'
    
def tocLine2tocRow(tocLine, hasChapterNums=False, mode='html'):
    if mode=='html':
        ret = '<tr>'
        ret += f'<td>{tocLine[3]}</td>'
        if hasChapterNums:
            ret += f'<td>{tocLine[0]}</td>'
        ret += f'<td>{tocLine[1]}</td>'
        ret += f'<td>{tocLine[2]}</td>'
        ret += '</tr>'
    elif mode=='md':
        ret = '| '
        if hasChapterNums:
            ret += f'{tocLine[0]} | '
        ret += f'{tocLine[1]} | '
        ret += f'{tocLine[2]} |'
    return ret
    
def getRangesFromList(inputList, function, useIndex=True):
    ranges = []
    rangeBegin = -1
    rangeEnd = -1
    
    for i in range(len(inputList)):
        if useIndex==False:
            i = inputList[i]
            
        if function(inputList, i): #we have a wanted item
            if rangeBegin==-1:
                rangeBegin = i
            rangeEnd = i
        else:
            if rangeEnd != -1:
                ranges.append((rangeBegin, rangeEnd))
                rangeBegin = -1
                rangeEnd = -1
    if rangeEnd != -1:
        ranges.append((rangeBegin, rangeEnd))
    return ranges
    
def combineCorrespondingRanges(xOnlyRanges, noXRanges, xColumn, dataList, xOnlyRangesFirst=False, mode='html'):
    if mode=='html':
        ital1 = '<i>'
        ital2 = '</i>'
    elif mode=='md':
        ital1 = '*'
        ital2 = '*'
    for range_ in xOnlyRanges:
        rangeLength = range_[1]-range_[0] + 1
        correspondingRanges = [r for r in noXRanges if r[1]==range_[0]-1 and r[1]-r[0]>=rangeLength-1]
        if len(correspondingRanges)==1:
            #print(f'{correspondingRanges=}')
            for i in range(range_[0], range_[1]+1):
                if xOnlyRangesFirst:
                    dataList[i+rangeLength][xColumn] = f'{ital1}{dataList[i][xColumn]}{ital2}'
                else:
                    dataList[i-rangeLength][xColumn] = f'{ital1}{dataList[i][xColumn]}{ital2}'
                dataList[i][xColumn] = ''
    oldLength = len(dataList)
    dataList = [d for d in dataList if len(d[0])+len(d[1])+len(d[2])>0 ]
    newLength = len(dataList)
    #print('difference:', oldLength-newLength)
    return dataList
    
df = getNumRecordsForYears(2022, 2023, QUERY)
print('got numrecords for years')
#df.to_csv("recordcountsPerYear.csv", index=False)

random.seed(29061998) #my birthday

global counter
global matchList

sample_df = getYearSamples(df, 10)
for index, row in tqdm(sample_df.iterrows()):
#for i in [0]:
    year = row['YEAR']
    order = row['ORDER']
    recordPos = row['RECORD_POS']
    
    #year = '1975'
    #order = '3'
    #recordPos = '1'
    
    #get marc xml record from the dnb catalog via sru and isolate record
    r_marc21 = dnb_sru(QUERY.substitute(year=year), startRecord=recordPos)
    xml_marc = soup(r_marc21.content, features="xml")
    record_marc = xml_marc.find('record', {'type':'Bibliographic'})
    str_marc_record = unicodedata.normalize("NFC", str(record_marc))
    xml_marc_record = etree.fromstring(str_marc_record)
    
    #convert record to zotEntry
    zotEntry = marcxml2zotEntry(xml_marc_record)
    zotEntry['date'] = str(year)
    zotEntry['extra'] = f'order: {order}\n' + zotEntry['extra']
    
    print(zotEntry)
    response = zot.create_items([zotEntry])
    base_url = zotEntry['url']
    entry_key = response['success']['0']
    
    #create attachments for zotEntry:
    # 1. link to the table of content as pdf
    zotAtt_toc_pdf = zot.item_template('attachment', 'linked_url')
    zotAtt_toc_pdf['parentItem'] = entry_key
    zotAtt_toc_pdf['title'] = f'Inhaltsverzeichnis_{year}_{order}.pdf'
    zotAtt_toc_pdf['contentType'] = 'application/pdf'
    zotAtt_toc_pdf['url'] = f'{base_url}/04'
    
    # 2. table of content (toc) text
    zotAtt_toc_text = zot.item_template('note')
    zotAtt_toc_text['parentItem'] = entry_key
    zotAtt_toc_text['note'] = f'<h1> Inhaltsverzeichnis-OCR-Text_{year}_{order}</h1>'
    
    r = requests.get(f'{base_url}/04/text')
    html = soup(r.content.decode(), features='lxml')
    tocText = html.get_text()
    
    
    tocLines = []
    numChapterMatch_regex = r'(?P<numChapter>^(((Kapitel)|(Kap\.?)|(Abschnitt)|(Teil))\s)?(([A-Z]{0,5})|((?P<numChap_chars>[^\s[a-zäüöß]{3,}]*)[\d\.:(\-\S)]+(?P=numChap_chars))))[\s|$]'
    pageMatch_regex = r'(?P<page>[^\.\s,]{0,2}\d+[^\.\s,]{0,2})$'
    #dotRow_pattern = r'(\b[\wÖÜÄ]?[a-z0-9öüäß]+\b[?!\'"\-]|[]{0})(\s?(?:[^a-np-zäöüß][a-np-zäöüß]{0,3}?)*)$'
    #dotRow_regex = re.compile(r'(\b[\wÖÜÄ]?[a-z0-9öüäß]+\b[?!\'"\-]|[]{0})(\s?[^\w](?:[^a-np-zäöüß][a-np-zäöüß]{0,3}?)*)$')
    line_count = 0
    for line in tocText.splitlines():
        numChapter = ''
        title = ''
        page = ''
        
        pageMatch = re.search(pageMatch_regex, line)
        if pageMatch:
            page = pageMatch['page']
            if len(line) > len(page):
                #print('page start:', pageMatch.start('page'))
                line = line[0:pageMatch.start('page')-1]
                #print('line after split page:', line)
            else:
                line = ''
        numChapterMatch = re.search(numChapterMatch_regex, line)
        if numChapterMatch:
            numChapter = numChapterMatch['numChapter']
            #print('numChapter:', numChapter)
            if len(line) > len(numChapter):
                title = line[numChapterMatch.end('numChapter')+1:-1]
                #print('title after split numChapter:', title)
            else:
                line = ''
        title = line
        #title = re.sub(dotRow_pattern, '\g<1> ', title)
        line_count +=1
        tocLines.append([numChapter, title, page, line_count])
    
    hasChapterNums = (len([l for l in tocLines if l[0] != ''])>0)
    
    pageOnlyFunc = lambda inputList, i: inputList[i][0]=='' and inputList[i][1]=='' and inputList[i][2]!=''
    pageOnlyRanges = getRangesFromList(tocLines, pageOnlyFunc)
    #print(pageOnlyRanges)
    
    if len(pageOnlyRanges)>0:
        noPageFunc = lambda inputList, i: inputList[i][1]!='' and inputList[i][2]==''
        noPageRanges = getRangesFromList(tocLines, noPageFunc)
        #print(noPageRanges)
        tocLines = combineCorrespondingRanges(pageOnlyRanges, noPageRanges, 2, tocLines)
    
    if hasChapterNums:
        numChapOnlyFunc = lambda inputList, i: inputList[i][1:2]==[''] and inputList[i][0]!=''
        numChapOnlyRanges = getRangesFromList(tocLines, numChapOnlyFunc)
        
        if len(numChapOnlyRanges)>0:
            noNumChapFunc = lambda inputList, i: inputList[i][1]!='' and inputList[i][0]==''
            noNumChapRanges = getRangesFromList(tocLines, noNumChapFunc)
    
            tocLines = combineCorrespondingRanges(numChapOnlyRanges, noNumChapRanges, 0, tocLines, xOnlyRangesFirst=True)
    
    tocTable = '<table style="width:100%">'
    
    if hasChapterNums:
        #f_md.write('| Kap.-Nr. | Kapitel | Seite |\n')
        #f_md.write('| -------- | ------- | ----- |\n')
        tocTable += '''
          <tr>
            <th style="width:20px">line_count</th>
            <th style="width:10%">Kap.-Nr.</th>
            <th style="width:80%">Kapitel</th>
            <th style="width:20px">Seite</th>
          </tr>
          '''
    else:
        #f_md.write('| Kapitel | Seite |\n')
        #f_md.write('| ------- | ----- |\n')
        tocTable += '''
          <tr>
            <th style="width:20px">line_count</th>
            <th style="width:90%">Kapitel</th>
            <th style="width:20px">Seite</th>
          </tr>
          '''
    
    tocRows = [tocLine2tocRow(l, hasChapterNums, mode='html') for l in tocLines]
    tocTable += '\n'.join(tocRows)
    tocTable += '</table>'
    
    #print(tocText)
    counter = 0
    matchList = []
    for term in search.SEARCHTERMS:
        #prepare term for regex-search 
        term = term.replace('*', '.*?') # right-truncation * -> 0 or more chars (lazy)
        term = term.replace(' ', r'\b \b') # add word boundaries around a space
        term = r'\n(.*?)(\b' + term + r'\b)(.*?)\n' # add word boundaries + begin/end of table row around it
        tocTable = re.sub(term, highlightedMatch, tocTable, flags=re.I)
    
    zotAtt_toc_text['note'] += f'<div><h2>Gefundene Stichwörter: {counter}</h2><p>{"".join(matchList)}</p></div><div><h2>Inhaltsverzeichnis</h2>{tocTable}</div>'
    
    response = zot.create_items([zotAtt_toc_pdf, zotAtt_toc_text])
    
    attachmentPaths = []
    with open(f'tmp/MARC21-xml_{year}_{order}.mrcx', 'w') as f:
        f.write(xml_marc.prettify())
    
    attachmentPaths.append(f'tmp/MARC21-xml_{year}_{order}.mrcx')
    
    zot.attachment_simple(attachmentPaths, entry_key)
    
    
'''
'''