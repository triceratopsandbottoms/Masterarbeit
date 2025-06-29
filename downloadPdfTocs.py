import requests
import sys
import os
import pymupdf
import time
import logging
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
file_path = config['ZOTERO_FILEDUMP_PATH']
dropbox_folder = config['DROPBOX_PDFTOC_FOLDER']
dropbox_zot_home = config['DROPBOX_MAIN_ZOTERO_DIR']
local_file_path = config['LOCAL_PDFTOC_PATH']

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
                print(f'No corresponding attachment found for ${file.name}')
                continue
            #print(corr_att)    
            #print(file.path)
            
            new_path = file.path.replace('.pdf', '_marked.pdf')
            markPdfDoc(file.path, new_path)
            
            response = zot.attachment_simple([new_path], corr_att['parentItem'])
            logging.debug(f'Tried to upload attachment to zotero. Response: {response}')

        except Exception as e:
            raise Exception(f'An error occured while proccessing file "{file.name}": {e}')

def getTags():
    print (zot.tags())

fromZoteroUrlToZoteroPdf()

"""
try:
    #highlightSearchterms_upload2zotero()
except Exception as exc:
    print("Exception:", exc)
    print("Context:", exc.__context__)
"""