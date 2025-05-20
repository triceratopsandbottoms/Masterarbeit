from pycaprio import Pycaprio
from pycaprio.mappings import InceptionFormat
from zipfile import ZipFile
from io import BytesIO
from cassis import *
from bs4 import BeautifulSoup as soup
import json, itertools


INCEPTION_URL = "http://localhost:8080"
INCEPTION_USER = "remote-api"
INCEPTION_PW = "MDT2azx-qae0fbg*uhz"
PROJECT_ID = 2
INCEPTION_FORMAT = InceptionFormat.UIMA_CAS_XMI
USER = 'admin'

SENTENCE_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence"
TOKEN_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token"
DEPENDENCY_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.Dependency"
LEMMA_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Lemma"
POS_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS"
MORPH_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.morph.MorphologicalFeatures"
SPAN_TYPE = "custom.Span"
RELATION_TYPE = "webanno.custom.Relation"
COREFERENCE_TYPE = "webanno.custom.Coreferencesaslinks"
NAMED_ENTITY_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity"
CLITORIS_ENTITY_TYPE = "webanno.custom.ClitorisEntities"
SURFACE_FORM_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.SurfaceForm"
SEMARG_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.semantics.type.SemArg"
SEMPRED_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.semantics.type.SemPred"

def key_elemType(propElem):
    elemOrder = ["zus", "narg", "farg", "pspez", "gspez"]
    try:
        keyword = propElem.label.split()[0]
        rank = elemOrder.index(keyword)
    except:
        rank = 0
    return propElem[0] is rank

def check_for_sub_elems(cas, span):
    subElems = [r.Dependent for r in cas.select(RELATION_TYPE) if r.Governor.xmiID==span[0].xmiID]
    
    try:
        [rec_subElems] = [check_for_sub_elems(cas, [s]) for s in subElems]
        print("It worked")
    except:
        rec_subElems = subElems
    
    rec_subElems.sort(key=lambda s: s.begin)
    
    enumElems = []
    struct_subElems = []
    
    for subElem in rec_subElems:
        if subElem.label.lower().endswith("elem"):
            new_label = span[0].label
            new_label += " /"
            new_label += subElem.label
            subElem.set('label', new_label)
            enumElems.append(subElem)
        else:
            if enumElems != []:
                struct_subElems.append(enumElems)
                enumElems = []
            new_label = span[0].label
            new_label += " /"
            new_label += subElem.label
            subElem.set('label', new_label)
            struct_subElems.append([subElem])
    if enumElems != []:
        struct_subElems.append(enumElems)
    
    if struct_subElems == []:
        return span
    elif len(struct_subElems)==1:
        #TODO: Wenn ein Span ein subArg hat, das aber den Span ergänzen und nicht ersetzen soll, dann fällt hier der Span ungewollterweise weg, oder?
        [struct_subElems_] = struct_subElems
        return struct_subElems_
    else:
        struct_subElems = list(itertools.product(*struct_subElems))
        print("return:", struct_subElems)
        #TODO: Evtl dieses Konstrukt nochmal als Annotation speichern?
        return struct_subElems
        
#initializing the client
client = Pycaprio(INCEPTION_URL, authentication=(INCEPTION_USER, INCEPTION_PW))

#make a request at Inception and put the response doc into a ZipFile
annotation_zip = ZipFile(BytesIO(client.api.annotation(PROJECT_ID, 94, USER, annotation_format=INCEPTION_FORMAT))) # Downloads annotations on document 1

#recognise and deflate the zipfile contents
if annotation_zip.filelist[0].filename.endswith(".xmi"):
    annotation_xmi = annotation_zip.read(annotation_zip.filelist[0])
    typesystem_xml = annotation_zip.read(annotation_zip.filelist[1])
else:
    annotation_xmi = annotation_zip.read(annotation_zip.filelist[1])
    typesystem_xml = annotation_zip.read(annotation_zip.filelist[0])

#load/deserialise the received contents into a cas    
typesystem = load_typesystem(BytesIO(typesystem_xml))
cas = load_cas_from_xmi(BytesIO(annotation_xmi), typesystem=typesystem)

SemPred = typesystem.get_type(SEMPRED_TYPE)
Span = typesystem.get_type(SPAN_TYPE)

for rel in [r for r in cas.select(RELATION_TYPE) if r.RelationzumPrdikat not in [None, "", "elem"]]:
    dependent = rel.Dependent
    #print(old_dependent.label)
    new_label = rel.RelationzumPrdikat
    if rel.Relation:
        new_label += " | "
        new_label += rel.Relation
    dependent.set('label', new_label)
    #print("new",old_dependent.label)
 
for pred in filter(lambda s: s.label == "pred", cas.select(SPAN_TYPE)):
    propElems = []
    lemmaSubs = []
    propZuss = []
    for relation in filter(lambda rel: rel.Governor.xmiID == pred.xmiID, cas.select(RELATION_TYPE)):
        #print("relation:", relation)
        if relation.Dependent.label in ["predAVZ", "predSub"]:
            lemmaSubs.append([relation.Dependent])
        elif relation.Dependent.label.startswith("zus"):
            propZuss.append(relation.Dependent)
        else:
            propElems.append([relation.Dependent])
    
    #sort those 3 sublists and check for enumerations and other sub-Spans. "zusätze" mustn't have sub-elements, so the last step is skipped for them.
    lemmaSubs.sort(key=lambda s: s[0].begin)
    lemmaSubs = [check_for_sub_elems(cas, s) for s in lemmaSubs]
    propElems.sort(key=key_elemType)
    propElems = [check_for_sub_elems(cas, s) for s in propElems]
    propZuss.sort(key=lambda s: s[0].begin)
    
    #print("lemmaSubs:", lemmaSubs)
    print("LemmaProducts:", len(list(itertools.product(*lemmaSubs))))
    print("PropElemProducts:", len(list(itertools.product(*propElems))))
    

    """
    for [spans] in propElems:
        spanStrs = []
        for span in spans:
            elemStr = propElem.label.split()[0]
            elemStr += ": "
            spanStrs.append(span.get_covered_text())
        elemStr += " | ".join(spanStrs)
        propElemStrs.append(elemStr)
    """
    propZusStrs = []
    for zus in propZuss:
        try:
            zusStr = zus.label.split()[1]
            zusStr += ": "
        except:
            zusStr = ""
        zusStr += zus.get_covered_text()
        propZusStrs.append(zusStr)

    propArgsStrs = []
    for subPropArgs in itertools.product(*propElems):
        #subPropArgs.sort(key=key_elemType) -> doesn't work with tuples
        subPropArgsStrs = []
        for arg in subPropArgs:
            propArgStr = ""
            if type(arg)==tuple:
                propArgStr += arg[0].label.rsplit(" /")[0]
                propArgStr += ": "
                arg = " ".join(map(lambda span: span.get_covered_text(), arg))
                #print("arg:", arg)
                propArgStr += arg
            else:
                propArgStr += arg.label
                propArgStr += ": "
                propArgStr += arg.get_covered_text()
            subPropArgsStrs.append(propArgStr)
            #print("subPropArgsStrs:", subPropArgsStrs)
        propArgsStrs.append("\n\t".join(subPropArgsStrs))
        #print("propArgsStrs:", propArgsStrs) 
    
    lemmaStrs = []
    for raw_lemma in itertools.product(*lemmaSubs):
        lemmaStr = " ".join(map(lambda span: span.get_covered_text(), raw_lemma))
        if len(raw_lemma) > 0 and raw_lemma[-1].label != "predAVZ":
            lemmaStr += " "
        lemmaStr += cas.select_covered(TOKEN_TYPE, pred)[0].lemma.value
        lemmaStrs.append(lemmaStr)
    propLemmaStr = "lemma: "
    propLemmaStr += " | ".join(lemmaStrs)
    
    generalPropStr = ""
    if propZusStrs != []:
        generalPropStr += "ZUS:\n\t"
        generalPropStr += "\n\t".join(propZusStrs)
        generalPropStr += "\n"
    generalPropStr += "LEMMA:\n\t"
    generalPropStr += "\n\t".join(lemmaStrs)
    generalPropStr += "\n"
    generalPropStr += "ARGS:\n\t"
    generalPropStr += "\n\n\t".join(propArgsStrs)

    print(generalPropStr)




"""
ACHTUNG:
Ich brauche eigentlich keine itertools.product s von den Generalpropositionen, um die Teilpropositionen aufzuteilen. Stattdessen muss die Generalproposition erstmal in die verschiedenen Stellen (lemma, narg, farg, etc) aufgeteilt werden. Dann das Produkt von Lemmata (l) und nargs (n) bilden (+zusätze) -> das ergebnis sind die ersten l*n Teilpropos. 
An jede dieser Teilpropos jeweils das Argument auf der nächsten Stelle (s) anhängen, bei enums mit e Elementen ergeben sich zusätzlich l*n*e Teilpropos. Nach einer enum wird das Argument allerdings wieder zusammengefasst/"eingeklappt" und das Argument auf der nächsten Stelle erzeugt nur l*n weitere Teilpropos.

Die Anzahl der Teilpropos berechnet sich also so:

l*n* N_s_ohne_e + N_e 
bzw.:
l*n*N_e'    mit e' = Aufzählungselemente, wobei einfache Argumente als Aufzählungen mit nur einem Element angesehen werden.

Vorgehen
- Cas exportieren, Elemente extrahieren:
    - type3:DocumentMetaData
    - type5:Sentence
    - custom2:Coreferencesaslinks
    - custom2:ClitorisEntities
    - custom:Span
    - custom2:Relation
    - cas:Sofa
    - custom2:CoreferencesaslinksReferenzenLink
    - (type5:Lemma) -> nach dem nächsten Schritt löschen
- Cas vereinfachen
    - Relation.Dependents als zusätzliches Span-Feature aufnehmen, danach die Relation löschen (vorausgesetzt, "Relation zum Prädikat" wurde schon im Span-Label implementiert)
    - CoreferencesaslinksReferenzenLink genauso als zusätzliches Coreferencesaslinks-Feature integrieren und danach löschen
    - Bei pred-Spans ohne SurfaceForm: Lemma als SurfaceForm setzen
- Spans und Coreferencesaslinks: Feature ClitRef setzen
    - wenn ClitorisEntity im Span enthalten ist -> ClitRef = xmi:id der ClitorisEntity 
    - wenn eine referenz auf einen Coreferencesaslinks-span mit ClitRef-Feature im Span liegt -> den Wert übernehmen
- Für alle pred-Spans: rekursiv Dependent-Spans suchen und dieses Set von Spans als Generalproposition speichern
- Je Generalproposition die Teilpropositionen berechnen und speichern
"""