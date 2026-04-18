import pandas as pd
from tqdm import tqdm, trange

df = pd.read_excel("./data/TextAnnotationen.xlsm", usecols="I:L")
#print(df.info())

df = df.loc[df['Anatomisch-physiologisch?'] == True]

#print(df.info())

for index, row in tqdm(df.iterrows()):
    filename = row["Dateiname"]
    excerpt = row["Anno_Text_mit Umbrüchen2"]
    
    with open("./data/anatomicExcerpts/secondRun/"+filename, "w") as f: 
        f.write(excerpt)
