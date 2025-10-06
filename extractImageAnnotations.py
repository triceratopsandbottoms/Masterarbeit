import pymupdf
import pandas as pd
from pyzotero import zotero
from tqdm import tqdm, trange
from dotenv import dotenv_values

secrets = dotenv_values(".env")

LIBRARY_ID = secrets['ZOTERO_LIBRARY_ID']
API_KEY = secrets['ZOTERO_API_KEY']

TABLEPATH = "./data/imageAnnotations.csv"
OUTPUTPATH = "./data/images/"

zot = zotero.Zotero(LIBRARY_ID, 'group', API_KEY)

df = pd.read_csv(TABLEPATH, sep=";")

#print(df)

# Iterating over rows
for index, row in tqdm(df.iterrows()):
    path = row["path"].replace("\\", "/").replace("C:", "/mnt/c")
    pageIndex = row["pageIndex"]
    outpath = OUTPUTPATH + row["bookKey"] + "_" + row["annoKey"] + "_" + row["pageLabel"] + ".jpg"
    
    doc = pymupdf.open(path)
    page=doc[pageIndex]
    
    height = page.cropbox[3]
    
    x0 = row["r0"]
    y0 = height - row["r3"]
    x1 = row["r2"]
    y1 = height - row["r1"]
    
    rect = pymupdf.Rect([x0, y0, x1, y1])

    image = page.get_pixmap(clip=rect)
    image.save(outpath, jpg_quality=98)
        
    