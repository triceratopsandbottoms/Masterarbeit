    #klitoris-synonyme
CLITORIS_TERMS = ['bulboklitoralorgan*',
			'clit',
			'clitor*',
			'kitzel',
			'kitzler*',
			'klit',
			'klitor*',
			#'lustknospe*',                -> 0 Treffer
			'lustorgan*',
			#'lustperle*',                 -> 0 Treffer
			'penis muliebre']
					
    #vulva-synonyme
VULVA_TERMS = ['cunnus',
			'fotze*',
			'foz',
			'fud',
			'fut',
			'intimbereich*',
			#'intimgegend*',               -> 0 Treffer
			'intimzone*',
			'miss brown',
			'möse*',
			'pubes*',
			'pudendum muliebre',
			'punzel*',
			'pussi*',
			'pussy*',
			'schamgegend*',
			'scheidenvorhof*',
			'vestibulum',
			'vorhof d* scheide*',
			'vorhof d* vagina*',
			'votze*',
			'vulv*',
			'weiblich* scham*',
			'yoni*']

    #geschlechtsorgan-synonyme
GENITAL_TERMS = ['genital*',
			'begattungsorgan*',
			'fortpflanzungsapparat*',
			'fortpflanzungsorgan*',
			'fruchtbarkeitsorgan*',
			'gemächt*',
			'generationsorgan*',
			'geschlechtsapparat*',
			'geschlechtsorgan*',
			'geschlechtsteil*',
			'geschlechtswerkzeug*',
            #'intimorgan*',                 -> 0 Treffer
			'liebesorgan*',
			'primär* geschlechtsmerkmal*',
			'pudendum',
			'reproduktionsorgan*',
			'schamteil*',
			'sexualapparat*',
			'sexualorgan*',
			'wollustorgan*',
            #'wolllustorgan*',              -> 0 Treffer
			'zeugungsorgan*']
ONE_WORD_SUBSTITUTIONS = {'primär* geschlechtsmerkmal*': 'geschlechtsmerkmal*', 'weiblich* scham*': 'scham*', 'vorhof d* scheide*': 'vorhof', 'vorhof d* vagina*': 'vorhof', 'pudendum muliebre': 'muliebre', 'miss brown': 'brown', 'penis muliebre': 'muliebre'}

def oneWordVersion(termList):
    for term in termList:
        if term in ONE_WORD_SUBSTITUTIONS.keys():
            termList[termList.index(term)] = ONE_WORD_SUBSTITUTIONS[term]
    return termList
                
SEARCHTERMS = []
SEARCHTERMS.extend(CLITORIS_TERMS)
SEARCHTERMS.extend(VULVA_TERMS)
SEARCHTERMS.extend(GENITAL_TERMS)

SEARCHSTRING = '(' + ' or '.join([('"' + s + '"') for s in SEARCHTERMS]) + ')'
