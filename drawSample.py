import random
import logging
from dotenv import dotenv_values

LOGLEVELS_DICT = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARN': logging.WARN, 'ERROR': logging.ERROR, 'CRITICAL': logging.CRITICAL}

config = dotenv_values(".env.config")

filename_log = config['FILENAME_LOG_DRAWSAMPLE']
if config['LOGGINGLEVEL_DRAWSAMPLE']:
    logging_level = LOGLEVELS_DICT[config['LOGGINGLEVEL_DRAWSAMPLE']]
else:
    logging_level = 0

first_year = int(config['FIRST_YEAR'])
last_year = int(config['LAST_YEAR'])
samplesize = int(config['SAMPLESIZE'])
seed = int(config['SEED_DRAWSAMPLE'])

logger = logging.getLogger('drawSample-logger')
logging.basicConfig(format='%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s', filename=filename_log, encoding='utf-8', level=logging_level)

random.seed(seed)
N_years = last_year - first_year +1

N_allYears = samplesize//N_years #division without decimals
N_rest = samplesize%N_years #modulo -> rest of division without decimals

assert samplesize == N_allYears*N_years+N_rest

sample_rest = random.sample(range(first_year, last_year+1), k=N_rest)

print(sample_rest)