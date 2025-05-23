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
        keyword = propElem[0].label.split()[0]
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
        #TODO: Wenn ein Span ein subArg hat, das aber den Span ergänzen und nicht ersetzen soll, dann fällt hier der Span ungewollterweise weg, oder? -> ergänzungen liegen nur und immer vor, wenn es keine enumelems gibt. 
        [struct_subElems_] = struct_subElems
        return struct_subElems_
    else:
        struct_subElems = list(itertools.product(*struct_subElems))
        print("return:", struct_subElems)
        #TODO: Evtl dieses Konstrukt nochmal als Annotation speichern?
        return struct_subElems

def elementString(arg):
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
    return propArgStr

def get_surface_text(span):
    ret = ""
    if span.SurfaceForm:
        return span.SurfaceForm
    
    
    
    
#initializing the client
client = Pycaprio(INCEPTION_URL, authentication=(INCEPTION_USER, INCEPTION_PW))

#make a request at Inception and put the response doc into a ZipFile
annotation_zip = ZipFile(BytesIO(client.api.annotation(PROJECT_ID, 101, USER, annotation_format=INCEPTION_FORMAT))) # Downloads annotations on document 1

#recognise and deflate the zipfile contents
if annotation_zip.filelist[0].filename.endswith(".xmi"):
    annotation_xmi = annotation_zip.read(annotation_zip.filelist[0])
    typesystem_xml = annotation_zip.read(annotation_zip.filelist[1])
else:
    annotation_xmi = annotation_zip.read(annotation_zip.filelist[1])
    typesystem_xml = annotation_zip.read(annotation_zip.filelist[0])

#load/deserialise the received contents into a cas
typesystem = load_typesystem(BytesIO(typesystem_xml))
ClitEnt = typesystem.create_feature(domainType=SPAN_TYPE, name="clitEnt", rangeType="uima.cas.AnnotationBase")
SurfaceForm_ext = typesystem.create_feature(domainType=SPAN_TYPE, name="surfaceForm_ext", rangeType="uima.cas.AnnotationBase")
Coreference = typesystem.create_feature(domainType=SPAN_TYPE, name="coreference", rangeType="uima.cas.AnnotationBase")
Head = typesystem.create_feature(domainType=COREFERENCE_TYPE, name="head", rangeType="uima.cas.AnnotationBase")

cas = load_cas_from_xmi(BytesIO(annotation_xmi), typesystem=typesystem)


#add the relations values to the span labels, because we want to keep the info, but won't refer to relations later on anymore
for rel in [r for r in cas.select(RELATION_TYPE) if r.RelationzumPrdikat not in [None, "", "elem"]]:
    dependent = rel.Dependent
    #print(old_dependent.label)
    new_label = rel.RelationzumPrdikat
    if rel.Relation:
        new_label += " | "
        new_label += rel.Relation
    dependent.set('label', new_label)
    #print("new",old_dependent.label)

for ent in cas.select(CLITORIS_ENTITY_TYPE):
    for span in cas.select_covered(SPAN_TYPE, ent):
        span.set('clitEnt', ent)
        #print(span)
        
for ent in cas.select(NAMED_ENTITY_TYPE):
    for span in cas.select_covered(SPAN_TYPE, ent):
        span.set('clitEnt', ent)
        #print(span)

for surfaceForm in cas.select(SURFACE_FORM_TYPE):
    for span in cas.select_covered(SPAN_TYPE, surfaceForm):
        span.set('surfaceForm_ext', surfaceForm)
        #print(span)

for coref in cas.select(COREFERENCE_TYPE):
    if coref.Referenzen:
        coref.set("head", coref.Referenzen.elements[0].target)
        for span in cas.select_covered(SPAN_TYPE, coref):
            span.set('coreference', coref)
            #print(span)

i_pred = 0
for pred in filter(lambda s: s.label == "pred", cas.select(SPAN_TYPE)):
    i_pred +=1
    propZuss = []
    lemmaSubs = []
    propNargs = []
    propElems = []
    for relation in filter(lambda rel: rel.Governor.xmiID == pred.xmiID, cas.select(RELATION_TYPE)):
        #print("relation:", relation)
        if relation.Dependent.label in ["predAVZ", "predSub"]:
            lemmaSubs.append([relation.Dependent])
        elif relation.Dependent.label.startswith("zus"):
            propZuss.append(relation.Dependent)
        elif relation.Dependent.label.startswith("narg"):
            propNargs.append([relation.Dependent])
        else:
            propElems.append([relation.Dependent])
    
    #sort those 3 sublists and check for enumerations and other sub-Spans. "zusätze" mustn't have sub-elements, so the last step is skipped for them.
    propZuss.sort(key=lambda s: s[0].begin)
    lemmaSubs.sort(key=lambda s: s[0].begin)
    lemmaSubs = [check_for_sub_elems(cas, s) for s in lemmaSubs]
    propNargs.sort(key=lambda s: s[0].begin)
    propNargs = [check_for_sub_elems(cas, s) for s in propNargs]
    propElems.sort(key=key_elemType)
    propElems = [check_for_sub_elems(cas, s) for s in propElems]
    
    subLemmata = list(itertools.product(*lemmaSubs))
    #print("lemmaSubs:", lemmaSubs)
    print("LemmaProducts:", len(list(itertools.product(*lemmaSubs))))
    print("PropNargsProducts:", len(list(itertools.product(*propNargs))))
    print("PropElems:", len(propElems))
    
    partProps = []
    c_lemma=ord('A')
    for subLemma in subLemmata:
        prop = {"lemmaHead": pred}
        i=1
        for zus in propZuss:
                prop[f"zus{i}"] = zus
                i+=1
        c_ = chr(c_lemma) if len(subLemmata) > 1 else ""
        if len(subLemmata) > 0: prop[f"lemmaSubs{c_}"] = subLemma
        c_lemma+=1
        
        c_nargs=ord('A')
        for nargs in itertools.product(*propNargs):
            i=1
            for narg in nargs:
                c_ = chr(c) if narg.label.endswith("Elem") else ""
                prop[f"narg{i}{c_}"] = narg
                i+=1
            partProps.append(prop.copy())
            c_nargs+=1
            
            i=1
            for elem in propElems:
                if len(elem) > 1:
                    c_elems=ord('A')
                    for enum in elem:
                        type_ = enum.label.split()[0]
                        prop[f"{type_}{i}{chr(c_elems)}"] = enum
                        partProps.append(prop.copy())
                        prop.popitem()
                        c_elems+=1
                    prop[f"{type_}{i}"] = elem
                else:
                    type_ = elem[0].label.split()[0]
                    prop[f"{type_}{i}"] = elem[0]
                    partProps.append(prop.copy())
                i+=1
    
    #add IDs to the partial propositions
    c_prop=ord('A')
    for prop in partProps:
        prop["id"] = f"{ chr(i_pred).zfill(2) }{ chr(c_prop) }"
        c_prop+=1
    
"""    
    ########
    propZusStrs = []
    for zus in propZuss:
        try:
            zusStr = zus.label.split()[1]
            zusStr += ": "
        except:
            zusStr = ""
        zusStr += zus.get_covered_text()
        propZusStrs.append(zusStr)

    lemmaStrs = []
    for raw_lemma in itertools.product(*lemmaSubs):
        lemmaStr = " ".join(map(lambda span: span.get_covered_text(), raw_lemma))
        if len(raw_lemma) > 0 and raw_lemma[-1].label != "predAVZ":
            lemmaStr += " "
        lemmaStr += cas.select_covered(TOKEN_TYPE, pred)[0].lemma.value
        lemmaStrs.append(lemmaStr)
    propLemmaStr = "lemma: "
    propLemmaStr += " | ".join(lemmaStrs)

    nargsStrs = []
    for subPropArgs in itertools.product(*propNargs):
        subPropArgsStrs = []
        for arg in subPropArgs:
            propArgStr = elementString(arg)
            subPropArgsStrs.append(propArgStr)
            #print("subPropArgsStrs:", subPropArgsStrs)
        nargsStrs.append(subPropArgsStrs)
        #print("propArgsStrs:", propArgsStrs)
    
    #propElems
    propElemStrs = []
    for elem in propElems:
        if len(elem) == 1:
            [elem_] = elem
            elemStr = elementString(elem_)
            propElemStrs.append(elemStr)
        else:
            elemStrs = []
            for elem_ in elem:
                elemStr = elementString(elem_)
                elemStrs.append(elemStr)
            propElemStrs.append(elemStrs)
    
    print("zus:", propZusStrs)
    print("lemma:", lemmaStrs)
    print("nargs:", nargsStrs)
    print("elems:", propElemStrs)
    
    generalPropStr = ""
    if propZusStrs != []:
        generalPropStr += "ZUS:\n\t"
        generalPropStr += "\n\t".join(propZusStrs)
        generalPropStr += "\n"
    generalPropStr += "LEMMA:\n\t"
    generalPropStr += "\n\t".join(lemmaStrs)
    generalPropStr += "\n"
    generalPropStr += "ARGS:\n\t"
    #generalPropStr += "\n\n\t".join(nargsStrs)
    generalPropStr += "\n"
    generalPropStr += "ELEMS:\n\t"
    #generalPropStr += "\n\n\t".join(propElemStrs)

    #print(generalPropStr)

"""
"""
Was definiert werden muss:
span ->
    ein Stück text, kann alleine oder mit anderen ein gültiges PropElement sein
    Eigenschaften:  - evtl. koreferenz-span: xmiID
                    - enthält direkt/indirekt Klitorisverweis: Boolean
                    - evtl. KlitorisEntity-Span: xmiID
                    - Position innerhalb des PropElements: Integer
                    - Ist enumElem?: Boolean
                    - evtl. Art der Aufzählung z.B. "und", "bzw."...
                    - evtl. Position in der Aufzählung, z.B. 1/3
PropElement -> 
    ein aus einem oder mehreren Spans gebildetes Objekt; mehrere PropElemente, die aus einer Aufzählung gebildet wurden, besetzen dieselbe Stelle.
    Eigenschaften:  - evtl. Position in der Aufzählung, z.B. 1/3
                    - zugehörige Spans: xmiID
                    - zugehörige Stelle
                    - ? evtl. koreferenz-span: xmiID
                    - ? enthält direkt/indirekt Klitorisverweis: Boolean
                    - ? evtl. KlitorisEntity-Span: xmiID
    Einfaches PropElement -> besteht aus nur 1 Span
    PropElement mit Enum-Teil -> besteht aus 2-3 Spans, von denen der enumSpan hervorgehoben dargestellt werden kann 
    Zusammengesetztes PropElement -> besteht aus min. 2 Spans 
Stelle -> könnte doch auch einfach eine Eigenschaft der PropElemente sein?
    die Position, an der ein oder mehrere Argumente in der Propo stehen, z.B. Zusatz; Lemma; Narg1; Narg2; etc.
    Eigenschaften:  - zugehörige PropElemente: xmiID
                    - Typ: Zus, Lemma, Narg, Farg, Pspez oder GSpez
                    - Position in Bezug auf alle Stellen des gleichen Typs: int
Generalproposition ->
    Eigenschaften:  - ID der Textstelle: str
                    - n-te Generalproposition der Textstelle: n=int
                    - xmiIDs von allen PropElementen
                    - xmiID vom pred-Head
                    - evtl. Liste von Stellen?
Teilpropositionen ->
    Eigenschaften:  - xmiID der Generalproposition
                    - Liste der PropElemente: List of PropElemente/xmiIDs
                    - Nummer der Teilpropo: int

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