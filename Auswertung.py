import pandas as pd
import numpy as np
import scipy.stats as stats
from scipy.stats import pearsonr
import matplotlib.pyplot as plt

THEMEN = {"Anatomie": ["Ana: Äußere Strukturen",
            "Ana: Innere Strukturen",
            "Ana: Feinbau",
            "Ana: Variabilität"],
        "Embryo": ["Embryo: Geschlechtsvergleiche",
            "Embryo: Entwicklung"],
        "Lage": ["Lage: zu Muskeln",
            "Lage: zu sonstigem",
            "Lage: absolut"],
        "Funktion": ["Funktion: Stimulation und Empfindlichkeit",
            "Funktion: sexuelle Lust und Orgasmus",
            "Funktion: Anschwellen und Erektion",
            "Funktion: Sonstige Funktion"]}

CODES = ['kli', 'cac', 'spo', 'bul', 'cru', 'cor', 
        'gla', 'pra', 'fre', 'lig', 'ner', 'art', 
        'ven', 'rsp', 'int', 'kom', 'asz', 'des', 
        'tac', 'tas', 'sep', 'rcf']
        
CODES_DISPLAY = ['kli⁺', 'cac⁺', 'spo⁺', 'bul ', 'cru ', 'cor⁺', 
        'gla ', 'pra ', 'fre ', 'lig ', 'ner*', 'art*', 
        'ven*', 'rsp ', 'int ', 'kom ', 'asz ', 'des ', 
        'tac*', 'tas*', 'sep*', 'rcf*']
        
colors = ['tab:blue', 'tab:red', 'tab:cyan', 'tab:grey', 'tab:olive', 'tab:pink', 'tab:orange', 'tab:brown']
        
def calcMeanAndConfidenceInterval(series):
    m = series.mean() # Durchschnitt
    s = series.std(ddof=1) # Standardabweichung
    n = len(series) # Stichprobengröße
    t = stats.t.ppf(0.975, df=n-1)  # t-value für 95% confidence level
    e = t * (s / np.sqrt(n))  # Margin of error
    ci = (m - e, m + e)
    return(m, s, n, ci)
    
def idOutliersAndGetStats(df, series_name):
    print(f'Variable: {series_name}')
    #df[series_name].plot.hist()
    #plt.show()
    
    #Ausreißer erkennen
    df_series = df[(np.abs(stats.zscore(df[series_name])) < 3)]
    outlier = len(df)-len(df_series)
    print(f'  {outlier} Ausreißer erkannt, aber nicht entfernt.')
    
    mdn = df[series_name].median()
    q1 = df[series_name].quantile(0.25)
    q3 = df[series_name].quantile(0.75)
    print(f'  Mdn = {mdn}\n  IQR = [{q1}, {q3}]')
    
    m, s, n, ci = calcMeanAndConfidenceInterval(df[series_name])
    print(f'  M = {m}\n  SD = {s}\n  95 % CI [{ci[0]}, {ci[1]}]\n  n = {n}\n')
    
    return df_series
    
def getPearson(series1, series2, alternative=None):
    if alternative:
        corr = stats.pearsonr(series1, series2, alternative=alternative)
    else:
        corr = stats.pearsonr(series1, series2)
    print(f"Pearson-Korrelation: {series1.name} x {series2.name}{f', einseitig ({alternative})' if alternative else ''}\n  r = {corr.statistic}\n  p = {corr.pvalue}\n  n = {len(series1)}\n")
    #df.plot.scatter(series1.name, series2.name)

def getSpearman(series1, series2, alternative=None):
    if alternative:
        corr = stats.spearmanr(series1, series2, alternative=alternative)
    else:
        corr = stats.spearmanr(series1, series2)
    print(f"Spearman-Korrelation: {series1.name} x {series2.name}{f', einseitig ({alternative})' if alternative else ''}\n  r = {corr.statistic}\n  p = {corr.pvalue}\n  n = {len(series1)}\n")

### Ausschlussgründe analysieren ###

df_checkedRecords = pd.read_excel("/mnt/c/Users/annik/OneDrive/Documents/TextAnnotationen.xlsm", sheet_name="checkedRecords")

df_checkedRecords['keine Klitoris'] = ((df_checkedRecords["Ausschluss"]==True) & 
                                        (df_checkedRecords["falscher Einschluss"]==False) & 
                                        (df_checkedRecords["vergessen"]==False) & 
                                        (df_checkedRecords["vermisst"]==False) & 
                                        (df_checkedRecords["keine Vulven"]==False) & 
                                        (df_checkedRecords["nicht bestellbar"]==False) & 
                                        (df_checkedRecords["keine Genitalien"]==False) & 
                                        (df_checkedRecords["kein Treffer"]==False) & 
                                        (df_checkedRecords["andere Sprache"]==False) & 
                                        (df_checkedRecords["kein Sachbuch"]==False) & 
                                        (df_checkedRecords["keine Menschen"]==False))

df_Ausschlussgruende = pd.DataFrame()
for col in df_checkedRecords.columns:
    try:
        df_Ausschlussgruende[col] = [df_checkedRecords[col].value_counts()[True]]
        #print(df_checkedRecords[col].value_counts()[True])
    except:
        continue
    #
df_Ausschlussgruende = df_Ausschlussgruende.T
print(df_Ausschlussgruende)

df_checkedRecords["prinzipiell forschungsrelevant"] = ((df_checkedRecords["Einschluss"]==True) | (df_checkedRecords["vergessen"]==True))
#print(df_checkedRecords.info())

#Zusammenhang zwischen Anteil der prinzipiell forschungsrelevanten Büchern und Erscheinungsjahr?
(r,p) = pearsonr(df_checkedRecords[["Jahr"]], df_checkedRecords[["prinzipiell forschungsrelevant"]])
print("Jahr x prinzipiell forschungsrelevant", "r=", r, ", p=", p)


### Buchbezogene Daten analysieren ###
#Exceldatei einlesen
df = pd.read_excel("/mnt/c/Users/annik/OneDrive/Documents/TextAnnotationen.xlsm", sheet_name="allRecords", usecols="A:M,BE:CR", skiprows=1)

#Bücher der endgültigen Stichprobe filtern
df = df.loc[df['N Text+Bild'] != (0)].convert_dtypes()

#Berechne Validitätswerte
df['Validität R/Alle'] = (df['Validität Richtige'] / (df['Validität Richtige'] + df['Validität Falsche'] + df['Validität unklar']))

## Balkendiagramm für Verteilung der Validität ##
df_validität = pd.DataFrame({'richtig': [df['Validität Richtige'].mean() / df["N AnaPhy-Props"].mean()], 'falsch': [df['Validität Falsche'].mean() / df["N AnaPhy-Props"].mean()], 'unklar': [df['Validität unklar'].mean()] / df["N AnaPhy-Props"].mean()})
df_validität = df_validität.T
df_validität.plot.bar(legend=False)
plt.xticks(rotation='horizontal')
plt.yticks(ticks=[0, 0.2, 0.4, 0.6, 0.8, 1], labels=['0 %', '20 %', '40 %', '60 %', '80 %', '100 %'])
plt.xlabel('Ausprägung der Validität', fontweight='bold')
plt.ylabel('Anteil der Informationen', fontweight='bold')
plt.show()


## Deskriptive Statistiken und Konfidenzintervalle ##

# Umfang
df_umfang = idOutliersAndGetStats(df, 'Umfang')

# Vollständigkeit
df_vollst = idOutliersAndGetStats(df, 'Vollständigkeit')

# Validität R/Alle
df_val_ = df.loc[(df['Validität Richtige'] != 0) | (df['Validität Falsche'] != 0) | (df['Validität unklar'] != 0)]
print(f'{len(df_val_)} Bücher mit validen Validitätswerten.')
df_val = idOutliersAndGetStats(df_val_, 'Validität R/Alle')

## Korrelationen ##
getSpearman(df["Jahr"], df["Umfang"], "greater")
getSpearman(df["Jahr"], df["Vollständigkeit"], "greater")
getSpearman(df_val_["Jahr"], df_val_["Validität R/Alle"], 'greater')
getSpearman(df['Jahr'], df['N Bilder'])

### Themenanteile analysieren ###
#Oberkategorien zusammenfassen
dfs_themen = []
alle_themen_anteile = []

## Abbildung Unterthemen Boxplots ##
fig_themen, axes = plt.subplots(1,4, width_ratios=[4,2,3,4])
i = 0
for (kategorie,themen) in THEMEN.items():
    df[kategorie] = (0)
    for thema in themen:
        df[kategorie] = df[kategorie] + df[thema]
    df[kategorie + " %"] = (df[kategorie] / df["N AnaPhy-Props"])
    df[kategorie + " %"] = df[kategorie + " %"].astype('float')
    
    idOutliersAndGetStats(df, kategorie)
    idOutliersAndGetStats(df, kategorie + ' %')
    
    #Aus Thema-Häufigkeit Thema-Anteil berechnen
    columns = ["Jahr"]
    
    ## Scatterplots für Unterthemen erstellen ##
    fig, axs = plt.subplots(len(themen))
    for thema in themen:
        df[thema + " %"] = (df[thema] / df[kategorie])
        columns.append(thema + " %")
        columns.append(thema)
        axs[themen.index(thema)].scatter(df['Jahr'], df[thema + " %"])
        axs[themen.index(thema)].set_yticks(ticks=[0, 0.2, 0.4, 0.6, 0.8, 1], labels=['0 %', '20 %', '40 %', '60 %', '80 %', '100 %'])
        axs[themen.index(thema)].set_title(thema + ' %')
    
    fig.set_figheight(len(themen)*2.5)
    for ax in axs.flat:
        ax.label_outer()
    fig.show()
    
    df_thema = df[columns].loc[(df["N AnaPhy-Props"] != 0) & (df[kategorie] != 0)]
    
    ## Subplot: Boxplot für Themen-Anteile ##
    themen_anteile = [t + ' %' for t in themen]
    xlabels = []
    for t in themen:
        label = t.split(': ')[1]
        if len(label)>15:
            words = label.rsplit(' ', 1)
            label = '\n'.join(words)
            label = label.replace('und', '&')
            label = label.replace('Geschlechtsvergleiche', 'Geschlechts-\nvergleiche')
        xlabels.append(label)
    axes[i].boxplot(df_thema[themen_anteile], widths=0.5)
    axes[i].set_xticks(ticks=range(1,len(df_thema[themen_anteile].columns)+1), labels=xlabels, rotation=90)
    axes[i].set_yticks(ticks=[0, 0.2, 0.4, 0.6, 0.8, 1], labels=['0 %', '20 %', '40 %', '60 %', '80 %', '100 %'])
    axes[i].set_title(kategorie.replace('Embryo', 'Geschlechts-\nentwicklung'))
    #axes[i].set_aspect(aspect=3/len(themen), adjustable='box')
    i += 1
    
    alle_themen_anteile += themen_anteile
    
    for cols in [themen, [t + ' %' for t in themen]]:
        df_themen = pd.DataFrame({'M': df_thema[cols].mean(), 
                                'SD': df_thema[cols].std(ddof=1),
                                'n': len(df_thema[cols]),
                                'CI_low': df_thema[cols].mean() - stats.t.ppf(0.975, df=(len(df_thema[cols]))-1) * (df_thema[cols].std(ddof=1) / np.sqrt(len(df_thema[cols]))),
                                'CI_high': df_thema[cols].mean() + stats.t.ppf(0.975, df=(len(df_thema[cols]))-1) * (df_thema[cols].std(ddof=1) / np.sqrt(len(df_thema[cols]))),
                                'Mdn': df_thema[cols].median(),
                                'Q1': df_thema[cols].quantile(0.25),
                                'Q3': df_thema[cols].quantile(0.75),
                                'Spearman xJahr r': [stats.spearmanr(df_thema['Jahr'], df_thema[t]).statistic for t in df_thema[cols].columns],
                                'Spearman xJahr p': [stats.spearmanr(df_thema['Jahr'], df_thema[t]).pvalue for t in df_thema[cols].columns]
                                })
        dfs_themen.append(df_themen)
    
for ax in axes.flat:
    ax.label_outer()
fig_themen.supxlabel('Thema', fontweight='bold')
fig_themen.supylabel('Anteil am Themenbereich', fontweight='bold')
fig_themen.show()
df_themen = pd.concat(dfs_themen)
df_themen.to_csv('./data/df_themen.csv')
print(df_themen)


## Boxplot für Kategorien-Anteile ##
df[[k + " %" for k in THEMEN.keys()]].plot.box()
plt.xticks(ticks=[1,2,3,4], labels=[l.replace("Embryo", "Geschlechtsentwicklung") for l in THEMEN.keys()])
plt.yticks(ticks=[0, 0.2, 0.4, 0.6, 0.8, 1], labels=['0 %', '20 %', '40 %', '60 %', '80 %', '100 %'])
plt.xlabel('Themenbereich', fontweight='bold')
plt.ylabel('Anteil der Informationen', fontweight='bold')
plt.show()

### Abbildungen auswerten ###

def checkDescriptionList(row, code):
    descr_list = row['beschriftete Strukturen']
    presence = row[code]
    status = presence
    #print(type(descr_list))
    if type(descr_list) != list:
        return status
    for descr in descr_list:
        if descr.replace(' ', '').split('->')[0].count(code) > 0:
            status = 'falsch/unpräzise beschriftet'
            if descr.replace(' ', '').split('->')[0]==descr.replace(' ', '').split('->')[1]:
                status = 'korrekt & präzise beschriftet'
    return status

##Tabellen mit Abbildungen laden und vereinigen
df_Abb = pd.read_excel("/mnt/c/Users/annik/OneDrive/Documents/TextAnnotationen.xlsm", sheet_name="Abbildungen", usecols="A:E,R:AE")
df_TAbb = pd.read_excel("/mnt/c/Users/annik/OneDrive/Documents/TextAnnotationen.xlsm", sheet_name="Teil-Abbildungen", usecols="A:E,R:AE")
df_Abb = pd.concat([df_Abb, df_TAbb])
df_Abb = df_Abb.assign(row_number=range(len(df_Abb)))

#Ausschlüsse entfernen
df_Abb = df_Abb.loc[(df_Abb['Ausschluss'] == False)]

#print(df_Abb.info())
print(df_Abb.groupby('Medientyp')['Thema'].value_counts(), '\n')
df_Abb_thema = pd.DataFrame({'Schematische Abbildung': df_Abb.loc[df_Abb['Medientyp']=='Schematische Zeichnung']['Thema'].value_counts(), 
                                'Foto': df_Abb.loc[df_Abb['Medientyp']=='Foto']['Thema'].value_counts(), 
                                'Anderes': df_Abb.loc[df_Abb['Medientyp']=='Anderes']['Thema'].value_counts(), 
                                'Gesamt': df_Abb['Thema'].value_counts()})
df_Abb_thema = df_Abb_thema.sort_values('Gesamt', ascending=False)
df_Abb_thema[['Schematische Abbildung', 'Foto', 'Anderes']].plot.bar(stacked=True, color=['tab:blue','tab:red','tab:grey'])
print(df_Abb_thema)

## Balkendiagramm Themen von Abbildungen ##
plt.xticks(ticks=[0,1,2,3,4], labels=['Normal', 'Pathologie', 'Intervention', 'Schwangerschaft&\nGeburt', 'Embryologie'], rotation='horizontal')
plt.tight_layout()
plt.xlabel('Thema', fontweight='bold')
plt.ylabel('Anzahl Abbildungen', fontweight='bold')
plt.show()

print(df_Abb['Details?'].value_counts(), '\n')
df_Abb['Details?'].value_counts().plot.bar()
plt.xticks(rotation='horizontal')
plt.show()


print(df_Abb.groupby('Medientyp')['Blickwinkel'].value_counts(), '\n')
df_Abb_blick = pd.DataFrame({'Schematische Abbildung': df_Abb.loc[df_Abb['Medientyp']=='Schematische Zeichnung']['Blickwinkel'].value_counts(), 
                                'Foto': df_Abb.loc[df_Abb['Medientyp']=='Foto']['Blickwinkel'].value_counts(), 
                                'Anderes': df_Abb.loc[df_Abb['Medientyp']=='Anderes']['Blickwinkel'].value_counts(), 
                                'Gesamt': df_Abb['Blickwinkel'].value_counts()})
df_Abb_blick = df_Abb_blick.sort_values('Gesamt', ascending=False)

## Balkendiagramm Blickwinkel von Abbildungen ##
df_Abb_blick[['Schematische Abbildung', 'Foto', 'Anderes']].plot.bar(stacked=True, color=['tab:blue','tab:red','tab:grey'])
plt.xticks(rotation='horizontal')
plt.xlabel('Blickwinkel', fontweight='bold')
plt.ylabel('Anzahl Abbildungen', fontweight='bold')
plt.show()

#Spalten für einzelne Klitorisstrukturen erstellen mit Info, ob diese abgebildet, fehlend oder nicht im Bild waren
for code in CODES:
    df_Abb[code] = np.where(
        df_Abb['abgebildete Strukturen'].str.contains(code, na=False), 'abgebildet', np.where(
        df_Abb['fehlende Strukturen'].str.contains(code, na=False), 'fehlend', 'nicht im Bild')) 

df_Abb['beschriftete Strukturen'] = df_Abb['beschriftete Strukturen'].str.split('\n')
df_Abb['ikonografische Analyse'] = df_Abb['ikonografische Analyse'].str.split('\n')

for code in CODES:
    df_Abb[code + ' B'] = df_Abb.apply(checkDescriptionList, code=code, axis=1)

#print(df_Abb)

#DataFrame für Beschriftungen erstellen, indem Beschriftungs-Spalte aufgeteilt wird in einzelne Beschriftungen
df_Bes = df_Abb.explode('beschriftete Strukturen')
df_Bes['beschriftete Strukturen'] = df_Bes['beschriftete Strukturen'].str.replace(' ', '')


#Beschriftungen in beschriftete Strukturen und Beschriftung aufteilen; prüfen, ob die Beschriftung tatsächlich korrekt und eindeutig ist
df_Bes[['beschriftet', 'Beschriftung']] = df_Bes['beschriftete Strukturen'].str.split('->', expand=True)
df_Bes['korrekte, eindeutige Beschriftung'] = (df_Bes['beschriftet'] == df_Bes['Beschriftung'])

#Gründe von ikonografischer Analyse auswerten/Grafik erstellen
df_abg_str = df_Abb.explode('ikonografische Analyse')
df_abg_str[['abgebildet', 'Analyse']] = df_abg_str['ikonografische Analyse'].str.split(':', expand=True)
df_abg_str['Darstellung'] = df_abg_str['Analyse'].str.extract(r'(2.\d\d?)[, )]')
df_abg_str = df_abg_str.dropna(subset='abgebildet')
df_abg_str['Darstellung'] = df_abg_str['Darstellung'].fillna('X')

dict_ = {}
for code in CODES:
    dict_[code] = df_abg_str.loc[df_abg_str['abgebildet']==code]['Darstellung'].value_counts()
df_darst = pd.DataFrame(dict_)
df_darst = df_darst.T
df_darst['gesamt'] = 0
for col in df_darst.columns:
    if col != 'gesamt':
        df_darst[col] = df_darst[col].fillna(0)
        df_darst['gesamt'] = df_darst['gesamt'] + df_darst[col]
print(df_darst)
df_darst_pro = pd.DataFrame()

for col in ['2.'+str(x) for x in range(1, 31)]:
    df_darst_pro[col] = df_darst[col] / df_darst['gesamt']
df_darst_pro['X'] = df_darst['X'] / df_darst['gesamt']
df_darst_pro['gesamt'] = df_darst['gesamt']

df_darst_pro = df_darst_pro.loc[df_darst_pro['gesamt']>0]
df_darst_pro = df_darst_pro.sort_values('gesamt')
print(df_darst_pro)

colors_ikon = {'2.1': colors[0], '2.2': colors[1],
            '2.3': colors[0], '2.4': colors[1], '2.5': colors[2], '2.6': colors[4], '2.7': colors[5], '2.8': colors[6],
            '2.9': colors[0], '2.10': colors[1], '2.11': colors[2],
            '2.12': colors[0], '2.13': colors[1], '2.14': colors[1],
            '2.15': colors[0], '2.16': colors[1],
            '2.17': colors[0],
            '2.18': colors[0], '2.19': colors[1],
            '2.20': colors[0], '2.21': colors[1],
            '2.22': colors[0],
            '2.23': colors[0],
            '2.24': colors[0], '2.25': colors[1],
            '2.26': colors[0],
            '2.27': colors[0],
            '2.28': colors[0], '2.29': colors[1],
            '2.30': colors[0],
            'X': colors[3]}

## horizontales Balkendiagramm mit typischen Darstellungen ##
ax = df_darst_pro[[col for col in df_darst_pro.columns if col != 'gesamt']].plot(kind='barh', stacked=True, width=0.9, zorder=3, legend=False, color=colors_ikon)
plt.xticks(ticks=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1], labels=['0 %', '10 %', '20 %', '30 %', '40 %', '50 %', '60 %', '70 %', '80 %', '90 %', '100 %'])
ax.set_xlim(left=0, right=1)
plt.yticks(fontname='Monospace')
plt.xlabel('Anteil der Darstellungsart', fontweight='bold')
plt.ylabel('Klitorisstruktur', fontweight='bold')
plt.grid(True, axis='x', zorder=-1)

#Bar labels zum plot hinzufügen
labels = [col.replace('2.', '').replace('X', '*') for col in df_darst_pro.columns if col!='gesamt']
#print(labels)
num_yticks = len(ax.patches)/len(labels)
for i, rect in enumerate(ax.patches):
    # Find where everything is located
    height = rect.get_height()
    width = rect.get_width()
    x = rect.get_x()
    y = rect.get_y()
    
    j = int(i//num_yticks)
    # The width of the bar is also not pixels, it's the
    # number of animals. So we can use it as the label!
    label_text = labels[j] if width>0 else ''
    #print(label_text)
    # ax.text(x, y, text)
    label_x = x + width / 2
    label_y = y + height / 2
    ax.text(label_x, label_y, label_text, ha='center', va='center', color='w')

plt.show()

df_gla = df_abg_str.loc[df_abg_str['abgebildet']=='gla']

#Spalten für einzelne Klitorisstrukturen erstellen mit Info, ob diese beschriftet waren
for code in CODES:
    df_Bes[code + ' B'] = np.where(
        df_Bes['beschriftet'].str.contains(code, na=False) & (df_Bes['korrekte, eindeutige Beschriftung']==True), 'korrekt & präzise', np.where(
        df_Bes['beschriftet'].str.contains(code, na=False), 'falsch/unpräzise', np.where(
        (df_Bes[code]=='abgebildet') & (df_Bes['Beschriftung vorhanden']==True), 'fehlt', np.where(
        df_Bes[code]=='abgebildet', 'nicht vorhanden', 'nicht abgebildet'))))
    
#Spalten mit Anzahl der abgebildeten bzw. fehlenden Strukturen erstellen    
df_Abb['N abgebildet'] = 0
df_Abb['N fehlend'] = 0
df_Abb['N präzise beschriftet'] = 0
df_Abb['N unpräzise beschriftet'] = 0
for code in CODES:
    df_Abb['N abgebildet'] = df_Abb['N abgebildet'] + [1 if x == 'abgebildet' else 0 for x in df_Abb[code]]
    df_Abb['N fehlend'] = df_Abb['N fehlend'] + [1 if x == 'fehlend' else 0 for x in df_Abb[code]]
    df_Abb['N präzise beschriftet'] = df_Abb['N präzise beschriftet'] + [1 if x == 'korrekt & präzise beschriftet' else 0 for x in df_Abb[code + ' B']]
    df_Abb['N unpräzise beschriftet'] = df_Abb['N unpräzise beschriftet'] + [1 if x == 'falsch/unpräzise beschriftet' else 0 for x in df_Abb[code + ' B']]

#Spalte zur Vollständigkeit jeder Abbildung erstellen -> CAVE: Nicht verwechseln mit Vollständigkeit der Bücher!
df_Abb['Vollständigkeit'] = df_Abb['N abgebildet'] / (df_Abb['N abgebildet'] + df_Abb['N fehlend'])
df_Abb['Vollständigkeit Beschriftungen'] = (df_Abb['N präzise beschriftet'] + df_Abb['N unpräzise beschriftet']) / df_Abb['N abgebildet']

#print(df_Abb.loc[df_Abb['Beschriftung vorhanden']==True])

#DataFrames für Schematische Abbildungen bzw. Fotos erstellen
df_schema = df_Abb.loc[df_Abb['Medientyp']=='Schematische Zeichnung']
df_foto = df_Abb.loc[df_Abb['Medientyp']=='Foto']
df_andere = df_Abb.loc[df_Abb['Medientyp']=='Andere']

df_schema_bes = df_schema.loc[df_schema['Beschriftung vorhanden']==True]
df_foto_bes = df_foto.loc[df_foto['Beschriftung vorhanden']==True]

#Statistiken und Korrelation der Vollständigkeit von Schematischen Zeichnungen auf Bildebene berechnen
print('Statistiken und Korrelation der Vollständigkeit von Schematischen Zeichnungen auf Bildebene')
idOutliersAndGetStats(df_schema, 'Vollständigkeit')
getSpearman(df_schema['year'], df_schema['Vollständigkeit'])

print('Statistiken und Korrelation der Beschriftungs-Vollständigkeit von Schematischen Zeichnungen mit Beschriftung auf Bildebene')
idOutliersAndGetStats(df_schema_bes, 'Vollständigkeit Beschriftungen')
getSpearman(df_schema_bes['year'], df_schema_bes['Vollständigkeit Beschriftungen'])

print('Statistiken und Korrelation der Beschriftungs-Vollständigkeit von Fotos mit Beschriftung auf Bildebene')
idOutliersAndGetStats(df_foto_bes, 'Vollständigkeit Beschriftungen')
getSpearman(df_foto_bes['year'], df_foto_bes['Vollständigkeit Beschriftungen'])

#Daten zusammenfassen auf Buchebene
df_Abb_Buch = df_Abb.groupby('bookKey').agg(
                            Vollständigkeit= ('Vollständigkeit' , 'mean'), 
                            Jahr=('year', 'mean'),
                            N_Abb=('annoKey', 'count'))
df_Abb_Buch['N_ohne_Klitoris'] = df_Abb.groupby('bookKey')['Vollständigkeit'].apply(lambda x: x[x == 0].count())
df_Abb_Buch['%_ohne_Klitoris'] = df_Abb_Buch['N_ohne_Klitoris'] / df_Abb_Buch['N_Abb']
#print(df_Abb_Buch)
df_Abb_Bes = df_Abb.loc[df_Abb['Beschriftung vorhanden']==True]
df_Abb_Bes = df_Abb_Bes[df_Abb_Bes['N abgebildet']!=0]

df_Abb_Buch_Bes = df_Abb_Bes.groupby('bookKey').agg(
                            Vollständigkeit_Beschriftungen=('Vollständigkeit Beschriftungen' , 'mean'), 
                            Jahr=('year', 'mean'),
                            N_Abb=('annoKey', 'count'))

#Statistiken und Korrelation: mittlere Vollständigkeit pro Buch x Jahr
print('Statistiken und Korrelation: mittlere Vollständigkeit pro Buch x Jahr')
idOutliersAndGetStats(df_Abb_Buch, 'Vollständigkeit')
getSpearman(df_Abb_Buch['Vollständigkeit'], df_Abb_Buch['Jahr'])

print('Statistiken und Korrelation: mittlere Beschriftungs-Vollständigkeit pro Buch mit beschrifteten Bilder x Jahr')
#print(df_Abb_Buch_Bes)
idOutliersAndGetStats(df_Abb_Buch_Bes, 'Vollständigkeit_Beschriftungen')
getSpearman(df_Abb_Buch_Bes['Vollständigkeit_Beschriftungen'], df_Abb_Buch_Bes['Jahr'])

#Abbildungen ohne Klitorisstrukturen auf Abbildungsebene
df_oK = df_schema.loc[df_schema['N abgebildet'] == 0]
print(f'Schematische Abbildungen ohne Klitoris: {len(df_oK)} / {len(df_schema)} = {len(df_oK)/len(df_schema)}\n')

#Abbildungen ohne Klitorisstrukturen auf Buchebene
idOutliersAndGetStats(df_Abb_Buch, '%_ohne_Klitoris')
getSpearman(df_Abb_Buch['Jahr'], df_Abb_Buch['%_ohne_Klitoris'])

df_Abb_Buch_oK = df_Abb_Buch.loc[df_Abb_Buch['%_ohne_Klitoris'] > 0]
print(f'Bücher mit Abbildungen ohne Klitoris: {len(df_Abb_Buch_oK)} / {len(df_Abb_Buch)} = {len(df_Abb_Buch_oK)/len(df_Abb_Buch)}\n')

#Daten zum Vorhandensein in Schematischen Abbildungen zusammenfassen -> Klitorisstrukturen
print('Vorhandensein von Klitorisstrukturen in Schematischen Abbildungen')
df_Abg = df_schema[[c+' B' for c in CODES]].apply(pd.Series.value_counts)
df_Abg = df_Abg.T
df_Abg['codes'] = CODES_DISPLAY
df_Abg = df_Abg.set_index('codes')

df_Abg['falsch/unpräzise beschriftet %'] = df_Abg['falsch/unpräzise beschriftet'] / len(df_schema)
df_Abg['korrekt & präzise beschriftet %'] = df_Abg['korrekt & präzise beschriftet'] / len(df_schema)
df_Abg['unbeschriftet %'] = df_Abg['abgebildet'] / len(df_schema)
df_Abg['fehlend %'] = df_Abg['fehlend'] / len(df_schema)
df_Abg['nicht im Bild %'] = df_Abg['nicht im Bild'] / len(df_schema)
df_Abg['insgesamt abgebildet'] = df_Abg['abgebildet'].fillna(0) + df_Abg['korrekt & präzise beschriftet'].fillna(0) + df_Abg['falsch/unpräzise beschriftet'].fillna(0)
df_Abg['insgesamt abgebildet %'] = df_Abg['insgesamt abgebildet'] / len(df_schema)

df_Abg['gesamt'] = 1 - df_Abg['nicht im Bild %'].fillna(0)

df_Abg = df_Abg.sort_values('gesamt')
print(df_Abg[['insgesamt abgebildet', 'insgesamt abgebildet %', 'fehlend', 'fehlend %', 'falsch/unpräzise beschriftet %', 'korrekt & präzise beschriftet %']])

## horizontales Balkendiagramm abgebildeter/beschrifteter Klitorisstrukturen in Schematischen Abbildungen ##
ax = df_Abg[['korrekt & präzise beschriftet %', 'falsch/unpräzise beschriftet %', 'unbeschriftet %', 'fehlend %']].plot(kind='barh', stacked=True, color=colors, width=0.9, zorder=3)
plt.legend(['korrekt&präzise beschriftet', 'falsch/unpräzise beschriftet', 'unbeschriftet', 'fehlt'], loc='lower right')
plt.xticks(ticks=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1], labels=['0 %', '10 %', '20 %', '30 %', '40 %', '50 %', '60 %', '70 %', '80 %', '90 %', '100 %'])
ax.set_xlim(left=0, right=1)
plt.yticks(fontname='Monospace')
plt.xlabel('Anteil an schematischen Abbildungen', fontweight='bold')
plt.ylabel('Klitorisstruktur', fontweight='bold')
plt.grid(True, axis='x', zorder=-1)
plt.show()
#print(df_Abg)

#Daten zum Vorhandensein in Fotos zusammenfassen auf Klitorisstrukturen
print('Vorhandensein von Klitorisstrukturen in Fotos')
df_Abg = df_foto[[c+' B' for c in CODES]].apply(pd.Series.value_counts)
df_Abg = df_Abg.T
df_Abg['codes'] = CODES_DISPLAY
df_Abg = df_Abg.set_index('codes')

df_Abg['falsch/unpräzise beschriftet %'] = df_Abg['falsch/unpräzise beschriftet'] / len(df_foto)
df_Abg['korrekt & präzise beschriftet %'] = df_Abg['korrekt & präzise beschriftet'] / len(df_foto)
df_Abg['abgebildet %'] = df_Abg['abgebildet'] / len(df_foto)
df_Abg['nicht im Bild %'] = df_Abg['nicht im Bild'] / len(df_foto)
df_Abg['insgesamt abgebildet'] = df_Abg['abgebildet'].fillna(0) + df_Abg['korrekt & präzise beschriftet'].fillna(0) + df_Abg['falsch/unpräzise beschriftet'].fillna(0)
df_Abg['insgesamt abgebildet %'] = df_Abg['insgesamt abgebildet'] / len(df_foto)


df_Abg['gesamt'] = 1 - df_Abg['nicht im Bild %'].fillna(0)

df_Abg = df_Abg.sort_values('gesamt')
#print(df_Abg)
print(df_Abg[['insgesamt abgebildet', 'insgesamt abgebildet %']])

## horizontales Balkendiagramm abgebildeter/beschrifteter Klitorisstrukturen in Fotos ##
ax = df_Abg[['korrekt & präzise beschriftet %', 'falsch/unpräzise beschriftet %', 'abgebildet %']].plot(kind='barh', stacked=True, color=colors, width=0.9, zorder=3)
plt.legend(['korrekt&präzise beschriftet', 'falsch/unpräzise beschriftet', 'unbeschriftet'], loc='lower right')
ax.set_xlim(left=0, right=1)
plt.xticks(ticks=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1], labels=['0 %', '10 %', '20 %', '30 %', '40 %', '50 %', '60 %', '70 %', '80 %', '90 %', '100 %'])
plt.yticks(fontname='Monospace')
plt.xlabel('Anteil an Fotos', fontweight='bold')
plt.ylabel('Klitorisstruktur', fontweight='bold')
plt.grid(True, axis='x', zorder=-1)
plt.show()


#Daten zum Vorhandensein von Beschriftungen in Abbildungen zusammenfassen -> Klitorisstrukturen
print('Vorhandensein von Beschriftungen in Abbildungen mit Beschriftung')
df_Abg = df_Abb_Bes[[c+' B' for c in CODES]].apply(pd.Series.value_counts)
df_Abg = df_Abg.T
df_Abg['codes'] = CODES_DISPLAY
df_Abg = df_Abg.set_index('codes')

df_Abg['abgebildet'] = df_Abg['falsch/unpräzise beschriftet'].fillna(0) + df_Abg['korrekt & präzise beschriftet'].fillna(0) + df_Abg['abgebildet'].fillna(0)

df_Abg['falsch/unpräzise beschriftet %'] = df_Abg['falsch/unpräzise beschriftet'] / df_Abg['abgebildet']
df_Abg['korrekt & präzise beschriftet %'] = df_Abg['korrekt & präzise beschriftet'] / df_Abg['abgebildet']
df_Abg['gesamt'] = df_Abg['falsch/unpräzise beschriftet %'].fillna(0) + df_Abg['korrekt & präzise beschriftet %'].fillna(0)

df_Abg = df_Abg.sort_values('gesamt')

## horizontales Balkendiagramm zu Beschriftung ## 
ax = df_Abg[['korrekt & präzise beschriftet %', 'falsch/unpräzise beschriftet %']].plot(kind='barh', stacked=True, color=colors, width=0.9, zorder=3)
plt.legend(['korrekt&präzise beschriftet', 'falsch/unpräzise beschriftet'], loc='lower right')

#Bar label zum plot hinzufügen
labels = list(df_Abg['korrekt & präzise beschriftet'].fillna(0).astype('int64').astype('string')) + list(df_Abg['falsch/unpräzise beschriftet'].fillna(0).astype('int64').astype('string'))
for i, rect in enumerate(ax.patches):
    # Find where everything is located
    height = rect.get_height()
    width = rect.get_width()
    x = rect.get_x()
    y = rect.get_y()
    
    # The width of the bar is also not pixels, it's the
    # number of animals. So we can use it as the label!
    label_text = labels[i] if labels[i]!='0' else ''
    
    # ax.text(x, y, text)
    label_x = x + width / 2
    label_y = y + height / 2
    ax.text(label_x, label_y, label_text, ha='center', va='center', color='w')

plt.xticks(ticks=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1], labels=['0 %', '10 %', '20 %', '30 %', '40 %', '50 %', '60 %', '70 %', '80 %', '90 %', '100 %'])
ax.set_xlim(left=0, right=1)
plt.yticks(fontname='Monospace')
plt.grid(True, axis='x', zorder=-1)
plt.show()


print(df_Bes.dropna(subset=['beschriftet'])['korrekte, eindeutige Beschriftung'].value_counts(), '\n')

#df_bb enthält Daten zu Abbildungen, die prinzipiell beschriftet sind
df_bb = df_Abb.loc[(df_Abb['Beschriftung vorhanden'] == True)]

print(f'Anzahl Bilder mit Beschriftung: {len(df_bb)} aus {len(df_bb.groupby("bookKey"))} Büchern \n')
