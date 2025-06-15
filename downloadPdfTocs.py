import requests
import sys
import pymupdf
import time
import logging
sys.path.append('./DNB SRU')
import dnb_search as search
sys.path.append('./python-dropbox-file-uploader')
from main import DropboxHandler
from dotenv import dotenv_values
from pyzotero import zotero
from tqdm import tqdm

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


def changePublicUrlsToDropbox():
    zot = zotero.Zotero(LIBRARY_ID, 'group', API_KEY)

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

def searchTermAndHighlightOccurences(page, textpage, term, color):
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
            annot.set_info(title='AutomaticSearchTermHighlighter', content=f"Search term: {term}", creationDate=pdftime)
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
    
try:
    #print(pymupdf.pdfcolor.keys())
    highlightSearchtermsInPdfs()
except Exception as exc:
    print("Exception:", exc)
    print("Context:", exc.__context__)
