import requests
import sys
import os
import re
import pymupdf
import time
import logging
import pprint
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
sys.path.append('./DNB SRU')
import dnb_search as search
sys.path.append('./python-dropbox-file-uploader')
from main import DropboxHandler
from dotenv import dotenv_values
from pyzotero import zotero
from tqdm import tqdm, trange

LOGLEVELS_DICT = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARN': logging.WARN, 'ERROR': logging.ERROR, 'CRITICAL': logging.CRITICAL}

# load env vars from files
secrets = dotenv_values(".env")
config = dotenv_values(".env.config")

LIBRARY_ID = secrets['ZOTERO_LIBRARY_ID']
API_KEY = secrets['ZOTERO_API_KEY']
collectionId = secrets['ZOTERO_COLLECTION_ZU_BESTELLEN']
collectionId_inclusion = secrets['ZOTERO_COLLECTION_EINSCHLUSS']

file_path = config['ZOTERO_FILEDUMP_PATH']
dropbox_folder = config['DROPBOX_PDFTOC_FOLDER']
dropbox_zot_home = config['DROPBOX_MAIN_ZOTERO_DIR']
local_file_path = config['LOCAL_PDFTOC_PATH']
local_books_path = config['LOCAL_PDFBOOKS_PATH']

# get logging config values from env
filename_log = config['FILENAME_LOG_PDFTOCHANDLING']
if config['LOGGINGLEVEL_PDFTOCHANDLING']:
    logging_level = LOGLEVELS_DICT[config['LOGGINGLEVEL_PDFTOCHANDLING']]
else:
    logging_level = 0

# initialize logger
logger = logging.getLogger("pdf_toc_handling")
logging.basicConfig(format='%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s', filename=filename_log, encoding='utf-8', level=logging_level)

# get one-word search terms
clitoris_terms = search.oneWordVersion(search.CLITORIS_TERMS)
vulva_terms = search.oneWordVersion(search.VULVA_TERMS)
genital_terms = search.oneWordVersion(search.GENITAL_TERMS)

zot = zotero.Zotero(LIBRARY_ID, 'group', API_KEY)
    
def pretty_print_dict(d, fcol_width):
    ret = ''
    for k, v in d.items():
        if type(v)==str:
            string = v
        else:
            string = pprint.pformat(v, sort_dicts=False)
        v_lines = string.splitlines()
        v_output = f'\n{" ":<{fcol_width}}'.join(v_lines)
        ret += f'{k:<{fcol_width}}{v_output}' + '\n'
    return ret
    
def changePublicUrlsToDropbox():

    items = zot.everything(zot.collection_items(collectionId, itemType='attachment'))

    attachments = []
    for item in tqdm(items):
        attachment = item['data']
        try:
        #print(attachment)
            if attachment['contentType']=='application/pdf':
                #r = requests.get(attachment['url'])
                #with open(file_path+'/'+attachment['title'], 'wb') as f:
                #    f.write(r.content)
                #file = r.content
                #saveAs = f"{dropbox_folder}/{attachment['title']}"
                #DropboxHandler().upload_files(file, saveAs)
                attachment['url'] = f"{dropbox_zot_home}{dropbox_folder}?preview={attachment['title']}"
                zot.update_items([attachment])
        except:
            raise Exception(f"Zotero item {attachment['key']} with title {attachment['title']} could not be updated.")

def searchTermAndHighlightOccurences(page, textpage, term, color, mode='comments'):
    pdftime = time.strftime('D:%Y%m%d')
    #prepare term for regex-search 
    term = term.replace('*', '') # remove right-truncation '*'
    
    # search for term, results in a list of rectangles
    quads = page.search_for(term, quads=True, textpage=textpage)
    
    if quads!=[]:
        logging.info(f'{len(quads)} occurences of "{term}" were found')
        color = pymupdf.pdfcolor[color]
        for quad in quads:
            annot = page.add_highlight_annot(quad)
            annot.set_colors(stroke=color)
            annot.set_info(title='AutomaticSearchTermHighlighter', creationDate=pdftime)
            if mode=='comments':
                annot.set_info(content=f"Search term: {term}", )
            annot.update()
        logging.debug(f'Created annotation for all quads(=places of occurences)')
    
    
def highlightSearchtermsInPdfs():
    
    filenames = DropboxHandler().list_all_folder_files(dropbox_folder)
    for filename in filenames:
        try:
            DropboxHandler().download_files(f"{dropbox_folder}/{filename}", 'tmp/input.pdf')
            logging.info(f'Downloaded document {filename} from Dropbox')
            # open input PDF 
            doc=pymupdf.open('tmp/input.pdf')

            num_pages = doc.page_count
            logging.info(f'the document has {num_pages} pages')
            
            for page in doc.pages():
                textpage = page.get_textpage()
                
                for term in clitoris_terms:
                    searchTermAndHighlightOccurences(page, textpage, term, 'hotpink')
                for term in vulva_terms:
                    searchTermAndHighlightOccurences(page, textpage, term, 'plum')
                for term in genital_terms:
                    searchTermAndHighlightOccurences(page, textpage, term, 'skyblue')
                    
            # save the document with these changes
            #pdf_file = doc.convert_to_pdf()
            
            doc.save('tmp/output.pdf')
            with open('tmp/output.pdf', 'rb') as f:
                DropboxHandler().upload_files(f.read(), f"{dropbox_folder}/{filename}")
                
            logging.info('Document was saved on disc as "tmp/output.pdf"')
            
            
            #DropboxHandler().upload_files('tmp/output.pdf', f"{dropbox_folder}/{filename}", mode='file_path')
            #logging.info(f'Uploaded document (with highlighted searchterms) to Dropbox at "{dropbox_folder}/{filename}"')
        except Exception as e:
            raise Exception(f'An error occured while proccessing file "{filename}": {e}')

def markPdfDoc(inputPath, outputPath=None):
    doc=pymupdf.open(inputPath)
    num_pages = doc.page_count
    logging.info(f'the document has {num_pages} pages')
    
    for page in doc.pages():
        textpage = page.get_textpage()
        
        for term in clitoris_terms:
            searchTermAndHighlightOccurences(page, textpage, term, 'hotpink', mode='no_comment')
        for term in vulva_terms:
            searchTermAndHighlightOccurences(page, textpage, term, 'plum', mode='no_comment')
        for term in genital_terms:
            searchTermAndHighlightOccurences(page, textpage, term, 'skyblue', mode='no_comment')
    if outputPath==None:
        outputPath = inputPath
    doc.save(outputPath)
    return doc

def fromZoteroUrlToZoteroPdf():
    #items = zot.everything(zot.collection_items('NXUKXR6N', itemType='book'))
    items = zot.everything(zot.top(tag='🛒 bestellt'))
    counter = 0
    for item in tqdm(items):
        try:
            attachments = zot.children(item['data']['key'], itemType='attachment')
            pdf_files = [a['data'] for a in attachments if a['data']['linkMode']=='imported_file']
            if pdf_files==[]: #if no pdf-toc is already present:
                counter += 1
                print(counter, item['data']['date'], item['data']['title'])
                #toc_link_att_list = [a['data'] for a in attachments if a['data']['contentType']=='application/pdf']
                #if toc_link_att_list != []:
                    #toc_link_att = toc_link_att_list[0]
                url = item['data']['url'] + '/04'
                r = requests.get(url)
                with open('tmp/input.pdf', 'wb') as f:
                    f.write(r.content)
                markPdfDoc('tmp/input.pdf', 'tmp/Inhaltsverzeichnis_marked.pdf')
                #new_title = toc_link_att['title'].replace('.pdf', '_marked.pdf')
                zotResponse = zot.attachment_simple([ 'tmp/Inhaltsverzeichnis_marked.pdf'], item['data']['key'])
        except Exception as e:
            print (f'\nAn error occured while proccessing the following item: {item}\nError: {e}')
    print(f'items without imported pdfs before this operation: {counter}')
    
def highlightSearchterms_upload2zotero():
    items = zot.everything(zot.collection_items(collectionId, itemType='attachment'))
    
    dir_entries = os.scandir(local_file_path)
    local_files = [e for e in dir_entries if e.is_file()]
        
    zotero_attachments = [i['data'] for i in items if i['data']['contentType']=='application/pdf']
    for x in trange(119, 203):
        file = local_files[x]
    #for file in tqdm(local_files):
        try:
            try:
                corr_att = [a for a in zotero_attachments if a['title']==file.name][0]
            except IndexError:
                print(f'No corresponding attachment found for {file.name}')
                continue
            #print(corr_att)    
            #print(file.path)
            
            new_path = file.path.replace('.pdf', '_marked.pdf')
            markPdfDoc(file.path, new_path)
            
            response = zot.attachment_simple([new_path], corr_att['parentItem'])
            logging.debug(f'Tried to upload attachment to zotero. Response: {response}')

        except Exception as e:
            raise Exception(f'An error occured while proccessing file "{file.name}": {e}')

def isNameInCreators(name, creators):
    if len(creators)==0:
        return 'creators is empty'
    for creator in creators:
        if creator.get('name')==None:
            nameToCompare = f"{creator.get('lastName')}{creator.get('firstName')}"
        else:
            nameToCompare = creator.get('name')
        if nameToCompare.find(name)>=0:
            return 'yes'
    return 'no'

def analyzeItemCards():
    
    #items = zot.everything(zot.items(tag='✅ Einschluss'))
    items = zot.everything(zot.collection_items_top(collectionId_inclusion))
    
    sign_item_dict = {}
    
    for item in items:
        sign = item['data']['callNumber']
        sign_std = sign.replace(' ', '').upper()
        for k, v in item['data'].copy().items():
            if not v:
                item['data'].pop(k)
        sign_item_dict[sign_std] = item['data']
    
    dir_entries = os.scandir(local_books_path)
    file_paths = [e.path for e in dir_entries if e.is_file()]
    
    document_overview = []
    paths = ['./tmp/Neuer Ordner (8)_20250629.pdf']
    
    #for inputPath in paths:
    for inputPath in tqdm(file_paths):
        document_dict = {}
        document_dict['path'] = inputPath
        document_dict['status'] = ''
        
        try:
            doc=pymupdf.open(inputPath)
            pages = list(doc.pages())
            itemCard = pages[0]
            
            rect_sign = pymupdf.Rect(470, 420, 720, 455)
            raw_signature = itemCard.get_textbox(rect_sign).strip()
            signature = raw_signature[2:].replace(' ', '').upper()
            document_dict['raw_signature'] = raw_signature
            document_dict['corr_key'] = ''
            
            rect_info = pymupdf.Rect(125, 60, 400, 250)
            raw_info = itemCard.get_textbox(rect_info).strip()
            document_dict['raw_info'] = raw_info
            
            if not raw_signature.startswith('L:'):
                logging.error(f"raw_signature '{raw_signature}' retrieved from the ItemCard in '{inputPath}' doesn't start with 'L:', e.g. has an invalid format, and therefore cannot be matched with a zotero item.")
                #print(f"raw_signature '{raw_signature}' retrieved from the ItemCard in '{inputPath}' doesn't start with 'L:', e.g. has an invalid format, and therefore cannot be matched with a zotero item.")
                document_dict['status'] = "ERROR: Signature doesn't start with 'L:'"
            elif re.fullmatch('[A-Z0-9\-\.,]*', signature) is None:
                logging.error(f"The signature '{signature}' retrieved from the ItemCard in '{inputPath}' contains invalid characters, e.g. chars other than [A-Z0-9\-\.,], and therefore cannot be matched with a zotero item.")
                #print(f"The signature '{signature}' retrieved from the ItemCard in '{inputPath}' contains invalid characters, e.g. chars other than [A-Z0-9\-\.,], and therefore cannot be matched with a zotero item.")
                document_dict['status'] = "ERROR: Signature contains invalid chars"
            elif signature not in sign_item_dict.keys():
                logging.error(f"The signature '{signature}' retrieved from the ItemCard in '{inputPath}' was not found in the considered zotero items and therefore was not matched with an item.")
                #print(f"The signature '{signature}' retrieved from the ItemCard in '{inputPath}' was not found in the considered zotero items and therefore was not matched with an item.")
                document_dict['status'] = "ERROR: Signature not found in zotero"
                
            corr_item = sign_item_dict[signature]
            pretty_item = pretty_print_dict(corr_item, 20)
            corr_key = corr_item['key']
            document_dict['corr_key'] = corr_key
            document_dict['pretty_item'] = str(pretty_item)
        except Exception as e:
            document_dict['status'] = f"ERROR: {e}"
        
        document_overview.append(document_dict)
    
    df = pd.DataFrame(document_overview)
    df.to_csv('matching_overview.csv')

    #item = zot.item(corr_key)
    
    
#remove outliers in y-coordinate-cols; code from https://stackoverflow.com/a/59366409
def remove_outliers(df, cols, min_dev=15, max_dev=30):
    k = 1.5 # how many interquartile ranges around the quartiles are still included
    Q1 = df[cols].quantile(0.25)
    Q3 = df[cols].quantile(0.75)
    med = df[cols].quantile(0.5)
    IQR = Q3 - Q1
    
    dev = [min(max([k*x, min_dev]), max_dev) for x in IQR] # how much deviation from the quartiles do we include
    #print(df)

    #print(f'{df[cols].median()=}, {low_b=}, {upp_b=}')
    
    low_b = pd.Series([max(Q1.iloc[x], med.iloc[x]-min_dev)-dev[x] for x in range(Q1.size)], index=cols)
    upp_b = pd.Series([min(Q3.iloc[x], med.iloc[x]+min_dev)+dev[x] for x in range(Q3.size)], index=cols)
    #print(f'{df[cols].size=}, {low_b=}')
    
    df = df[~((df[cols] < low_b) |(df[cols] > upp_b)).any(axis=1)]
    
    #print(f'Outliers with [{", ".join(cols)}]-values beneath {[round(x, 1) for x in (Q1 - dev)]} or above {[round(x, 1) for x in Q3 + dev]} were excluded.')
    #print(df)
    return df
    
def lin_reg_residual_column(df, col_x, col_y):
    x = df[[col_x]]
    y = df[col_y]
    model = LinearRegression()
    model.fit(x, y)
    
    residuals = abs(df[col_y] - model.predict(df[[col_x]]))
    
    df = df.assign(residuals=residuals)
    
    return residuals
    
def get_differing_rows(df1, df2):
    return df1[~df1.isin(df2).all(axis=1)]

def get_range_begins(nums, sortInput=True):
    if sortInput: 
        nums = sorted(set(nums))
    gaps = [[e] for s, e in zip(nums, nums[1:]) if s+1 < e]
    edges = iter(nums[:1] + sum(gaps, [])) # + nums[-1:])
    return list(edges) #list(zip(edges, edges))
    
def improve_bookscans():
    #Seitenzahlen: eine Zahl in einer der Ecken oder nicht existent. Wenn keine Zahl erkannt wird, aber die Seite davor und danach Seitenzahl haben: Seitenzahl dazwischen. Wenn unklar: markieren? Seitenzahlen mit doc.set_page_labels(//list_of_dicts//) setzen
    #Wenn keine unklaren Seitenzahlen nach den Seiten zu Beginn: Seiten sortieren
    
    df_zotMatches = pd.read_csv('matchedZot_2colmns.csv')
    #inputPath = './tmp/Neuer Ordner (8)_20250629.pdf'
    
    for row in list(df_zotMatches.itertuples())[77:]:
        print('Current row:', row)
        index = row[0]
        path = row[1]
        zotKey = row[2]
        
        children = zot.children(zotKey, itemType='attachment')
        attachment_titles = [x['data']['title'] for x in children]
        bookscans = [x for x in attachment_titles if x.startswith('Buchscan')]
        #print(bookscans)
        if bookscans != []:
            continue

        doc=pymupdf.open(path)
        
        '''EXTRACT POSSIBLE PAGE LABELS'''
        corner_nums = []
        for page in doc.pages():
            textpage = page.get_textpage()
            height = page.cropbox[3]
            words = textpage.extractWORDS()
            num_words = [w for w in words if w[4].isdigit() and w[6]==0]
            num_words_header = [w for w in num_words if w[3] < height*0.1]
            num_words_footer = [w for w in num_words if w[1] > height-height*0.1]
            
            if num_words_header:
                interimList = list(sorted(num_words_header, key=lambda w: (w[1], w[0]))[0])
                interimList.insert(0, page.number)
                corner_nums.append(interimList)
                interimList = list(sorted(num_words_header, key=lambda w: (w[1], w[2]))[0])
                interimList.insert(0, page.number)
                corner_nums.append(interimList)
            if num_words_footer:
                interimList = list(sorted(num_words_footer, key=lambda w: (w[3], w[0]))[0])
                interimList.insert(0, page.number)
                corner_nums.append(interimList)
                interimList = list(sorted(num_words_footer, key=lambda w: (w[3], w[2]))[0])
                interimList.insert(0, page.number)
                corner_nums.append(interimList)

        raw_df = pd.DataFrame(corner_nums, columns=['page_num','x0','y0','x1','y1','num_word','block_no','line_no','word_no'])
        #print('step 1:\n', raw_df)
        
        '''GET BEST EXTRACTED PAGE LABELS'''
        df = raw_df.apply(pd.to_numeric).drop_duplicates()
        
        #print('step 2 (duplicate removal):\n', raw_df)
        #df = raw_df
        
        if df['num_word'].size>0 and df['num_word'].max()== df.at[0, 'num_word']:
            df.drop(0, inplace=True)
        
        df.insert(5, 'x_center', (df['x0']+df['x1'])/2)
        df.insert(6, 'y_center', (df['y0']+df['y1'])/2)
        
        df = remove_outliers(df, cols=['y_center'])
        
        #print('step 3 (y-outlier removal):\n', df)
        #print(raw_df)
        #print('Differing rows:\n', get_differing_rows(raw_df, df), '\n')
        
        if df['page_num'].size > 4:
            try:
                '''categorize data into 2 position clusters (there are 2 page number locations, for left/right pages)'''
                kmeans = KMeans(n_clusters=2)
                y = kmeans.fit_predict(df[['x_center']])
                df = df.assign(cluster=y)
                
                #print('step 4 (assign cluster):\n', df)    
                
                '''Axiom: all left resp. right pages (-> clusters) have  e i t h e r  odd  o r  even page numbers
                Goal: Remove page numbers that doesn't fit 
                1. check whether the extracted page number (num_word) is odd or even, 2. get the modal value for even-ness within the cluster, 3. filter those pages where the even-ness matches it's clusters modal'''
                df['even'] = df['num_word'] % 2 == 0 
                cluster_even = df.groupby('cluster')['even'].agg(lambda x: x.mode())    
                df = df[ df['even'] == list(cluster_even[df['cluster']]) ]
                
                residuals = []
                for name, group in df.groupby('cluster'):
                    x = df[['num_word']]
                    y = df['x_center']
                    model = LinearRegression()
                    model.fit(group[['num_word']], group['x_center'])
                    residuals.extend(abs(group['x_center'] - model.predict(group[['num_word']])))
                
                df['residuals'] = residuals
                #print('step 5 (added column with residuals of linear regression per cluster):\n', df)
                    
                #print('Dropped x0,x1-outliers of clusters:\n', get_differing_rows(df, new_df), '\n')
                
                # before duplicates are deleted, we sort the df so that better fitting page numbers (those closer to the median position) are kept    
                df.sort_values(['page_num', 'residuals'])
                #print('step 6 (sort by page_num and residuals):\n', df)
                df.drop_duplicates('page_num', inplace=True)
                #print('step 7 (remove num_words with less fitting position in case of more than 1 number per page):\n', df)
            except Exception as e:
                print('Clustering did not work for this item. Error:', e)


        first_labeled_page = df['page_num'].min()
        last_page = doc.page_count-1
        #print(first_labeled_page, last_page)
            
        if df['page_num'].size > 1:
            df.set_index('page_num', inplace=True)
            
            '''FILL IN MISSING PAGE LABELS'''
            original_pnos = range(first_labeled_page, doc.page_count)
            page_labels = []
            ambiguous_guess = False
            guessed = False
            for i in original_pnos:
                if i in df.index:
                    label = int(df.at[i, 'num_word'])
                    if guessed and page_labels[-1] != label-1:
                        ambiguous_guess = True
                    page_labels.append(label)
                    guessed = False
                else:
                    label = page_labels[-1]+1
                    page_labels.append(label)
                    guessed = True
            if guessed and page_labels[-1] < df['num_word'].max():
                ambiguous_guess = True
            
            '''SET PAGE LABELS'''
            range_begins = get_range_begins(page_labels, sortInput=False)
            
            dicts = [{'startpage': 0, 'prefix': '', 'style': 'r', 'firstpagenum': 1}]
            for rb in range_begins:
                #startpage = [t[0] for t in page_label_tuples if t[1]==rb][0]
                startpage = original_pnos[page_labels.index(rb)]
                d = {'startpage': startpage, 'prefix': '', 'style': 'D', 'firstpagenum': rb}
                dicts.append(d)

            doc.set_page_labels(dicts)
            
            '''EVENTUALLY SORT PAGES BY PAGE LABELS'''
            if not ambiguous_guess:
                meta_pages = range(first_labeled_page)
                #main_pages = [t[0] for t in sorted(page_label_tuples, key=lambda t: t[1])]
                main_pages = [p for p in sorted(original_pnos, key=lambda p: page_labels[original_pnos.index(p)])]
                all_pages = [p for p in [*meta_pages, *main_pages]]
                sorted_pages = sorted(all_pages)
                if sorted_pages!=all_pages:
                    doc.select(sorted_pages)
                
        '''MARK CLITORIS MENTIONS'''
        if type(first_labeled_page)==int:
            pages = list(doc.pages())[first_labeled_page:]
        else:
            pages = list(doc.pages())
            
        for page in pages:
            textpage = page.get_textpage()
            
            clit_terms = ['clit', 'klit', 'kitzler', 'schwellkörper', 'cavern', 'kavern', 'spongi', 'bulb']
            for term in clit_terms:
                searchTermAndHighlightOccurences(page, textpage, term, 'hotpink')
        
        '''SAVE PDF'''
        doc.save(f'tmp/Buchscan_{zotKey}.pdf')
        
        #resp = zot.attachment_both([[f'Buchscan_{zotKey}.pdf', f'tmp/Buchscan_{zotKey}.pdf']], zotKey)
        #if resp['failure'] != []:
        #    print('WARNING: A failure occured while uploading a pdf to zotero:', resp['failure'])
        
def assign_parentItem_2_bookscan():
    parentless_items = zot.everything(zot.top(q='Buchscan'))
    template = zot.item_template('attachment', 'imported_file')
    
    for item in [[i['data'] for i in parentless_items if i['data']['title'].startswith('Buchscan')][0]]:
        print(item)
        parentItem_key = item['title'].split('_')[1]
        item['parentItem'] = parentItem_key
        #zot.update_item(item)
        #print(parentItem_key) 
            
def getTags():
    print (zot.tags())

#analyzeItemCards()
assign_parentItem_2_bookscan()

"""
try:
    #highlightSearchterms_upload2zotero()
except Exception as exc:
    print("Exception:", exc)
    print("Context:", exc.__context__)
"""