import random
import pandas as pd

random.seed(312487687)

df_v1 = pd.read_csv('recordcountsPerYear.csv')

samples = []
rawSample = []
for index, row in df_v1.iterrows():
    samplesize = row['NUM_RECORDS'] if row['NUM_RECORDS']<10 else 10
    sample = random.sample(range(1, row['NUM_RECORDS']+1), k=samplesize)
    samples.append(sample)
    for num in sample:
        rawSample.append({'YEAR': row['YEAR'], 'ORDER': sample.index(num), 'RECORD_POS': num})
        
df_v2 = df_v1.assign(SAMPLE = samples)
#print(df_v2.to_string())

sample_df = pd.DataFrame(rawSample)
print(sample_df)
#df_v2.to_csv("recordcountsPerYear_withSamples.csv", index=False)