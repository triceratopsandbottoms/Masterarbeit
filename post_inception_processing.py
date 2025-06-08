from pycaprio import Pycaprio
from pycaprio.mappings import InceptionFormat
from pycaprio.core.exceptions import InceptionBadResponse
from zipfile import ZipFile
from io import BytesIO
from cassis import *
from inspect import currentframe, getframeinfo
from string import Template
from tqdm import tqdm
from dotenv import dotenv_values
import json, itertools, warnings, time
import pandas as pd

secrets = dotenv_values(".env")

INCEPTION_URL = secrets['INCEPTION_URL']
INCEPTION_USER = secrets['INCEPTION_USER']
INCEPTION_PW = secrets['INCEPTION_PW']
PROJECT_ID = secrets['INCEPTION_PROJECT_ID']
USER = secrets['INCEPTION_ANNOTATION_USER']

INCEPTION_FORMAT = InceptionFormat.UIMA_CAS_XMI

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

NAMED_TO_CLIT_ENT_DICT = {'A. bulbi vestibuli': 'art', 'A. bulbi vestibuli vaginae': 'art', 'A. clitoridis': 'art', 'A. profunda clitoridis': 'art', 'Bulbus/-i vestibularis': 'bul', 'Corpus cavernosum urethrae': 'cau', 'Corpusc': '!', 'Klitoris (Organ mit C. cavernosum)': 'kli', 'Lig. fundiforme clitoridis': 'lig', 'N. cavernosus clitoridis': 'ner', 'V. bulbi vestibuli': 'ven', 'V. dorsalis clitoridis': 'ven', 'V. dorsalis clitoridis subfascialis': 'ven', 'V. dorsalis superficialis clitoridis': 'ven', 'V. profunda clitoridis': 'ven', 'Klitoris (Organ mit C. cavernosum + spongiosum)': 'kli', 'Klitoris (Organ mit C. cavernosum + spongiosum + cav. urethrae)': 'kli', 'Klitoris (Organ mit unklarem Umfang)': 'kli', 'Klitoriskomplex (Organkomplex/-gruppe)': '?', 'Schwellkörper (C. cavernosum + spongiosum)': '?', 'Schwellkörper (C. cavernosum + spongiosum + cav. urethrae)': '?', 'Schwellgewebe': '?', 'Corpus cavernosum clitoridis': 'cac', 'Crus/Crura clitoridis': 'cru', 'Corpus clitoridis (gesamt)': 'cor', 'Corpus clitoridis ascendenz': 'asz', 'Corpus clitoridis descendenz': 'des', 'Septum media des Corpus clitoridis': 'sep', 'Septum media des RSP': '?', 'Tunica albuginea': 'tac/tas', 'Corpus spongiosum clitoridis': 'spo', 'Bulbus/-i vestibuli': 'bul', 'Bulbuskommissur': 'kom', 'Glans clitoridis': 'gla', 'Frenulum/-a': 'fre', 'Infra-corporeal Residual Spongy Part (RSP)': 'rsp', 'Pars intermedia, Kobeltscher Venenplexus': 'int', 'Ligamentum suspensorium clitoridis': 'lig', 'Präputium clitoridis': 'pra', 'Fascia retrocruralis': 'frc', 'N. dorsalis clitoridis': 'ner', 'A. dorsalis clitoridis': 'art', 'V. dorsalis profunda clitoridis': 'ven', 'Angulus clitoridis': '?', 'Smegma clitoridis': '?'}


def key_elemType(propElem):
    elemOrder = ["zus", "narg", "farg", "pspez", "gspez"]
    try:
        keyword = propElem[0].label.split()[0]
    except:
        keyword = propElem[0][0].label.split()[0]
    rank = elemOrder.index(keyword)
    #print(rank)
    return rank

def key_dictKey(item):
    key = item[0]
    keyOrder = ["id", "zus", "lemma", "narg", "farg", "pspez", "gspez"]
    keyword = list(filter(lambda k: key.startswith(k), keyOrder))[0]
    rank = keyOrder.index(keyword)
    return rank

def key_propDict(item):
    key = item[0]
    keyOrder = ["retrievalTime", "inceptionDocId", "bookId", "excerptId", "page", "infoId", "elements", 'coreferences', 'clitorisEntities', 'comments']
    rank = keyOrder.index(key)
    return rank


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
    enumerations = False
    
    for subElem in rec_subElems:
        if subElem.label.lower().endswith("elem"):
            enumerations = True
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
    elif struct_subElems != [] and enumerations==False:
        struct_subElems.append(span)
    
    if struct_subElems == []:
        return span
    elif len(struct_subElems)==1:
        #TODO: Wenn ein Span ein subArg hat, das aber den Span ergänzen und nicht ersetzen soll, dann fällt hier der Span ungewollterweise weg, oder? -> ergänzungen liegen nur und immer vor, wenn es keine enumelems gibt. -> mit elif Zeile 81-82 gelöst, oder?
        [struct_subElems_] = struct_subElems
        return struct_subElems_
    else:
        struct_subElems = list(itertools.product(*struct_subElems))
        #print("return:", struct_subElems)
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

def get_elem_text(elem):
    if type(elem)==tuple:
         ret = " ".join(map(lambda item: get_elem_text(item), elem))
    elif type(elem)==list:
        s = ' '
        ret = f'\n{s: <8}'.join(map(lambda item: get_elem_text(item), elem))
    else:
        ret = get_surface_text(elem)
    return ret
    
def get_elem_coref(elem, runType='default'):
    corefs = []
    begins = []
    ends = []
    #if type(elem)==tuple:
    #    for span in elem:
    #        if span.coreference: 
    #            corefs.append((span.coreference, span.coreference.begin, span.coreference.end))
    #            begins.append(span.begin)
    #            ends.append(span.end)
    if type(elem) in [list, tuple]:
        for item in elem:
            output = get_elem_coref(item, runType='raw')
            for coref in output[0]: corefs.append(coref)
            for begin in output[1]: begins.append(begin) 
            for end in output[2]: ends.append(end)
    else:
        if elem.coreference: 
            corefs.append((elem.coreference, elem.coreference.begin, elem.coreference.end))
            begins.append(elem.begin)
            ends.append(elem.end)
            
    if runType=='default':
        ret = []
        for coref in set(corefs):
            if coref[1] <= min(begins) and coref[2] >= max(ends):
                fullCoverage = True
            else:
                fullCoverage = False
            ret.append((coref[0], fullCoverage))
        return ret
    else:
        return corefs, begins, ends
        
def get_elem_clitents(elem, runType='default'):
    clitEnts = []
    begins = []
    ends = []
    # if type(elem)==tuple:
        # for span in elem:
            # if span.clitEnt:
                # clitEnts.append((span.clitEnt, span.clitEnt.begin, span.clitEnt.end))
                # begins.append(span.begin)
                # ends.append(span.end)
            # elif span.coreference:
                # if span.coreference.head.clitEnt:
                    # clitEnts.append((span.coreference.head.clitEnt, span.coreference.begin, span.coreference.end))
                    # begins.append(span.begin)
                    # ends.append(span.end)
    if type(elem) in [list, tuple]:
        for item in elem:
            output = get_elem_clitents(item, runType='raw')
            for clitEnt in output[0]: clitEnts.append(clitEnt)
            for begin in output[1]: begins.append(begin)
            for end in output[2]: ends.append(end)
    else:
        if elem.clitEnt: 
            clitEnts.append((elem.clitEnt, elem.clitEnt.begin, elem.clitEnt.end))
            begins.append(elem.begin)
            ends.append(elem.end)
        elif elem.coreference:
            if elem.coreference.head.clitEnt:
                clitEnts.append((elem.coreference.head.clitEnt, elem.coreference.begin, elem.coreference.end))
                begins.append(elem.begin)
                ends.append(elem.end)
            
    if runType=='default':
        ret = []
        for clitEnt in set(clitEnts):
            if clitEnt[1] <= min(begins) and clitEnt[2] >= max(ends):
                fullCoverage = True
            else:
                fullCoverage = False
            ret.append((clitEnt[0], fullCoverage))
        return ret
    else:
        return clitEnts, begins, ends

def get_elem_comments(elem, runType='default'):
    comments = []
    begins = []
    ends = []
    # if type(elem)==tuple:
        # for span in elem:
            # if span.Anmerkungen: 
                # commentStr = '; '.join(span.Anmerkungen.elements)
                # comments.append((commentStr, span.begin, span.end))
                # begins.append(span.begin)
                # ends.append(span.end)
    if type(elem) in [list, tuple]:
        for item in elem:
            output = get_elem_comments(item, runType='raw')
            for comment in output[0]: comments.append(comment)
            for begin in output[1]: begins.append(begin) 
            for end in output[2]: ends.append(end)
    else:
        if elem.Anmerkungen: 
            commentStr = '; '.join(elem.Anmerkungen.elements)
            comments.append((commentStr, elem.begin, elem.end))
            begins.append(elem.begin)
            ends.append(elem.end)
            
    if runType=='default':
        ret = []
        for comment in set(comments):
            if comment[1] <= min(begins) and comment[2] >= max(ends):
                fullCoverage = True
            else:
                fullCoverage = False
            ret.append((comment[0], fullCoverage))
        return ret
    else:
        return comments, begins, ends

def get_surface_text(span):
    if 'SurfaceForm' in span.type._features.keys():
        if span.SurfaceForm:
            return span.SurfaceForm
    if 'label' in span.type._features.keys():
        if span.label=='pred':
            return cas.select_covered(LEMMA_TYPE, span)[0].value
    if span.surfaceForm_ext and span.surfaceForm_ext.begin >= span.begin and span.surfaceForm_ext.end <= span.end:
        ret = ""
        if span.begin < span.surfaceForm_ext.begin:
            ret += cas.sofa_string[span.begin:span.surfaceForm_ext.begin]
        ret += span.surfaceForm_ext.value
        if span.end > span.surfaceForm_ext.end:
            ret += cas.sofa_string[span.surfaceForm_ext.end:span.end]
        return ret
    else:
        return span.get_covered_text()

def isEnumElem(elem):
    if type(elem) in [tuple, list]:
        try:
            return [s for s in elem if s.label.endswith('Elem')]!=[]
        except:
            for e in elem:
                print(get_surface_text(e))
            return [s for s in elem if s[0].label.endswith('Elem')]!=[]
    else:
        return elem.label.endswith('Elem')

def getElemType(elem):
    try:
        type_ = elem[0].label.split()[0]
    except:
        try:
            type_ = elem[0][0].label.split()[0]
        except:
            type_ = elem.label.split()[0]
    return type_

def getElemTypes(elemList):
    ret = []
    for elem in elemList: ret.append(getElemType(elem))
    return ret
    
def makePartProps(subLemmata, propZuss, propNargs, propElems):    
    partProps = []
    c_lemma=ord('A')
    for subLemma in subLemmata:
        prop = {}
        prop['elements'] = {}
        prop['elements']['lemmaHead'] = pred
        i=1
        zusElems = [e for e in propElems if getElemType(e)=='zus']
        for zus in zusElems:
                i_ = i if len(zusElems)>1 else ""
                prop['elements'][f"zus{i_}"] = zus
                i+=1
        c_ = chr(c_lemma) if len(subLemmata) > 1 else ""
        if len(subLemmata) > 0: prop['elements'][f"lemmaSubs{c_}"] = subLemma
        c_lemma+=1
        
        c_nargs=ord('A')
        for nargs in itertools.product(*propNargs):
            i=1
            for narg in nargs:
                i_ = i if len(nargs)>1 else ""
                c_ = chr(c_nargs) if isEnumElem(narg) else ""
                prop['elements'][f"narg{i_}{c_}"] = narg
                i+=1
            partProps.append({'elements': prop['elements'].copy()})
            c_nargs+=1
            
            for elem in [e for e in propElems if getElemType(e)!='zus']:
                #print(getElemTypes(propElems))
                try:
                    sameTypeElems = list(filter(lambda e: getElemType(e)==getElemType(elem), propElems))
                except:
                    sameTypeElems = []
                    print('sameTypeElems konnten nicht bestimmt werden!')
                    
                i_ = sameTypeElems.index(elem)+1 if len(sameTypeElems)>1 else ""
                if len(elem) > 1:
                    c_elems=ord('A')
                    for enum in elem:
                        type_ = getElemType(enum)
                        prop['elements'][f"{type_}{i_}{chr(c_elems)}"] = enum
                        partProps.append({'elements': prop['elements'].copy()})
                        prop['elements'].popitem()
                        c_elems+=1
                    prop['elements'][f"{type_}{i_}"] = elem
                else:
                    type_ = getElemType(elem)
                    prop['elements'][f"{type_}{i_}"] = elem[0]
                    #saveProp = {'elements': prop['elements'].copy()}
                    partProps.append({'elements': prop['elements'].copy()})
                    
    return partProps
    
def addInformationDict(prop, dictKey, func_get_elem_info):
    prop[dictKey] = {}
    for key, value in prop['elements'].items():
        i=1
        infos = func_get_elem_info(value)
        for info in infos:
            i_= i if len(infos)>1 else ''
            newKey = key + f"_{i_}"
            if info[1]==False: newKey+="*"
            prop[dictKey][newKey] = info[0]
            i+=1
        if infos==[]: prop[dictKey][key] = ''
    return
    
def addMetaInformation(dict_, cas):
    bookId = cas.get_document_annotation().documentTitle.split('_')[0]
    excerptId = cas.get_document_annotation().documentTitle.split('_')[1]
    page = cas.get_document_annotation().documentTitle.split('_')[2].split('.')[0]
    
    dict_['bookId'] = bookId
    dict_['excerptId'] = excerptId
    dict_['page'] = page
    return
    
def makeStrPartProp(prop, mergeLemma=True):
    newProp = prop.copy()
        
    #copy metainformation
    #newProp['inceptionDocId'] = prop['inceptionDocId']
    #newProp['bookId'] = prop['bookId']
    #newProp['excerptId'] = prop['excerptId']
    #newProp['page'] = prop['page']
    #newProp['infoId'] = prop['infoId']
    
    newProp['elements'] = {}
    newProp['coreferences'] = {}
    newProp['clitorisEntities'] = {}
    newProp['comments'] = prop['comments'].copy()
    
    #get strings for all prop entries, coreferences and clitEnts
    lemmaSubs = False
    for key, value in prop['elements'].items(): #for 'normal' entries
        valueStr = get_elem_text(value)
        if key.startswith("lemmaSubs"):
            lemmaSubs = key
            needSpace = False
            if len(value)>0:
                try:
                    needSpace = value[-1].label!="predAVZ"
                except:
                    needSpace = value[-1][-1].label!="predAVZ"
            if needSpace: valueStr+=" "
            #if len(value)>0 and value[-1].label!="predAVZ": valueStr+=" "
        newProp['elements'][key] = valueStr
            
    for key, value in prop['coreferences'].items(): #for coref entries
        if value != '':
            valueStr = get_surface_text(value.head)
            
            #check whether the reference has another reference which might have another reference....
            curValue = value.head
            while curValue.head:
                valueStr += " <- "
                valueStr += get_surface_text(curValue.head)
                curValue = curValue.head
            if key.find('*')>0: 
                valueStr += ' ("'
                valueStr += get_surface_text(value)
                valueStr += '")'
            newProp['coreferences'][key] = valueStr
        else:
            newProp['coreferences'][key] = ''
                
    for key, value in prop['clitorisEntities'].items(): #for clitEnt entries
        if value != '':
            try:
                valueStr = value.Struktur
                if value.Bezug:
                    valueStr += "; -> "
                    valueStr += str(value.Bezug)
            except:
                valueStr = value.value
            if key.find('*')>0: 
                valueStr += ' ("'
                valueStr += get_surface_text(value)
                valueStr += '")'
            newProp['clitorisEntities'][key] = valueStr
        else:
            newProp['clitorisEntities'][key] = ''
    
    if mergeLemma:
        #combine lemmaSubs and lemmaHead into lemma 
        if lemmaSubs:
            new_key = 'lemma' + lemmaSubs.split('lemmaSubs')[1]
            newProp['elements'][new_key] = newProp['elements'][lemmaSubs] + newProp['elements']['lemmaHead']
            newProp['elements'].pop(lemmaSubs)
        else:
            newProp['elements']['lemma'] = newProp['elements']['lemmaHead']
        newProp['elements'].pop('lemmaHead')
    
    #sort all elements according to their position in the proposition
    sortedPropElems = dict(sorted(list(newProp['elements'].items()), key=key_dictKey))
    sortedPropCorefs = dict(sorted(list(newProp['coreferences'].items()), key=key_dictKey))
    sortedPropClitEnts = dict(sorted(list(newProp['clitorisEntities'].items()), key=key_dictKey))
    sortedPropComments = dict(sorted(list(newProp['comments'].items()), key=key_dictKey))
    newProp['elements'] = sortedPropElems.copy()
    newProp['coreferences'] = sortedPropCorefs.copy()
    newProp['clitorisEntities'] = sortedPropClitEnts.copy()
    newProp['comments'] = sortedPropComments.copy()
    
    return newProp
    
def flattenStrProp(strProp):
    #conversion of dictionaries for elements, corefs and clitEnts into strings 
    strProp['elements'] = dict2string(strProp['elements'], keyWidth=6)
    strProp['coreferences'] = dict2string(strProp['coreferences'], False)
    strProp['clitorisEntities'] = dict2string(strProp['clitorisEntities'], False)
    strProp['comments'] = dict2string(strProp['comments'], False)    
    return
    
def dict2string(dict_, includeKey=True, keyWidth=1):
    strings = []
    if includeKey:
        for key, value in dict_.items(): 
            strings.append(f'{key: >{keyWidth}}: {value}')
    else:
        for key, value in dict_.items():
            strings.append(str(value))
            
    ret = None if set(strings)=={''} else '\n'.join(strings)
    return ret
    
def prepareDocument(typesystem_xml, annotation_xmi):
    #load/deserialise the typesystem and add a bunch of features, then load the cas
    typesystem = load_typesystem(BytesIO(typesystem_xml))
    ClitEnt = typesystem.create_feature(domainType=SPAN_TYPE, name="clitEnt", rangeType="uima.cas.AnnotationBase")
    ClitEnt1 = typesystem.create_feature(domainType=COREFERENCE_TYPE, name="clitEnt", rangeType="uima.cas.AnnotationBase")
    SurfaceForm_ext = typesystem.create_feature(domainType=SPAN_TYPE, name="surfaceForm_ext", rangeType="uima.cas.AnnotationBase")
    SurfaceForm_ext1 = typesystem.create_feature(domainType=COREFERENCE_TYPE, name="surfaceForm_ext", rangeType="uima.cas.AnnotationBase")
    SurfaceForm_ext2 = typesystem.create_feature(domainType=CLITORIS_ENTITY_TYPE, name="surfaceForm_ext", rangeType="uima.cas.AnnotationBase")
    SurfaceForm_ext2a = typesystem.create_feature(domainType=NAMED_ENTITY_TYPE, name="surfaceForm_ext", rangeType="uima.cas.AnnotationBase")
    Coreference = typesystem.create_feature(domainType=SPAN_TYPE, name="coreference", rangeType="uima.cas.AnnotationBase")
    Head = typesystem.create_feature(domainType=COREFERENCE_TYPE, name="head", rangeType="uima.cas.AnnotationBase")

    cas = load_cas_from_xmi(BytesIO(annotation_xmi), typesystem=typesystem)

    #add the relations values to the span labels, because we want to keep the info, but won't refer to relations later on anymore
    for rel in [r for r in cas.select(RELATION_TYPE) if r.RelationzumPrdikat not in [None, '', 'elem', 'none']]:
        dependent = rel.Dependent
        #print(old_dependent.label)
        new_label = rel.RelationzumPrdikat
        if rel.Relation:
            new_label += " | "
            new_label += rel.Relation
        dependent.set('label', new_label)
        #print("new",old_dependent.label)

    for ent in cas.select(CLITORIS_ENTITY_TYPE):
        for span in cas.select_covering(SPAN_TYPE, ent):
            span.set('clitEnt', ent)
        for coref in cas.select_covering(COREFERENCE_TYPE, ent):
            if coref.Referenzen==None:
                coref.set('clitEnt', ent)
            #print(span)
            
    for ent in cas.select(NAMED_ENTITY_TYPE):
        newValue = NAMED_TO_CLIT_ENT_DICT[ent.value]
        ent.set('value', newValue)
        for span in cas.select_covering(SPAN_TYPE, ent):
            span.set('clitEnt', ent)
            #print(span)

    for surfaceForm in cas.select(SURFACE_FORM_TYPE):
        for span in cas.select_covering(SPAN_TYPE, surfaceForm):
            if surfaceForm.begin >= span.begin and surfaceForm.end <= span.end:
                span.set('surfaceForm_ext', surfaceForm)
        for coref in cas.select_covering(COREFERENCE_TYPE, surfaceForm):
            if surfaceForm.begin >= coref.begin and surfaceForm.end <= coref.end:
                coref.set('surfaceForm_ext', surfaceForm)
            #print(span)

    for coref in cas.select(COREFERENCE_TYPE):
        if coref.Referenzen:
            coref.set('head', coref.Referenzen.elements[0].target)
            for span in cas.select_covering(SPAN_TYPE, coref):
                span.set('coreference', coref)
                #print(span)
                
    return typesystem, cas

################################### CODE STARTS HERE ###################################
    
#initializing the client
client = Pycaprio(INCEPTION_URL, authentication=(INCEPTION_USER, INCEPTION_PW))

for inceptionDocId in tqdm(range(1,120)):

    #make a request at Inception and put the response doc into a ZipFile
    try:
        annotation_zip = ZipFile(BytesIO(client.api.annotation(PROJECT_ID, inceptionDocId, USER, annotation_format=INCEPTION_FORMAT))) # Downloads annotations on document 1
    except InceptionBadResponse as error:
        print('An error occurred:', error.args[0])
        continue
    
    retrievalTime = time.strftime('%d.%m.%Y %H:%M:%S %Z')
    #print(retrievalTime)
    
    #recognise and deflate the zipfile contents
    if annotation_zip.filelist[0].filename.endswith(".xmi"):
        annotation_xmi = annotation_zip.read(annotation_zip.filelist[0])
        typesystem_xml = annotation_zip.read(annotation_zip.filelist[1])
    else:
        annotation_xmi = annotation_zip.read(annotation_zip.filelist[1])
        typesystem_xml = annotation_zip.read(annotation_zip.filelist[0])

    typesystem, cas = prepareDocument(typesystem_xml, annotation_xmi)

    #safe excerpt string on disc
    textStr = cas.sofa_string
    excerpt = {}
    excerpt['retrievalTime'] = retrievalTime
    excerpt['inceptionDocId'] = inceptionDocId
    addMetaInformation(excerpt, cas)
    excerpt['excerptString'] = textStr

    df = pd.DataFrame([excerpt])
    df.to_csv("excerpt_strings.csv", mode='a', header=False, index=False)

    #iterate through all predicate heads in the current document / excerpt
    i_pred = 0
    for pred in filter(lambda s: s.label == "pred", cas.select(SPAN_TYPE)):
        i_pred +=1
        propZuss = []
        lemmaSubs = []
        propNargs = []
        propElems = []
        
        #sort Dependents of the current predicate head into different lists
        for relation in filter(lambda rel: rel.Governor.xmiID == pred.xmiID, cas.select(RELATION_TYPE)):
            #print("relation:", relation)
            if relation.Dependent.label in ["predAVZ", "predSub"]:
                lemmaSubs.append([relation.Dependent])
            #elif relation.Dependent.label.startswith("zus"):
            #    propZuss.append(relation.Dependent)
            elif relation.Dependent.label.startswith("narg"):
                propNargs.append([relation.Dependent])
            else:
                propElems.append([relation.Dependent])
        
        #sort those 3 sublists and check for enumerations and other sub-Spans. "zusätze" mustn't have sub-elements, so the last step is skipped for them. -> untrue, they can't have enums, but they can have subArgs -> TODO!!! -> putting zusätze into 'propElems'
        #propZuss.sort(key=lambda s: s[0].begin)
        lemmaSubs.sort(key=lambda s: s[0].begin)
        lemmaSubs = [check_for_sub_elems(cas, s) for s in lemmaSubs]
        propNargs.sort(key=lambda s: s[0].begin)
        propNargs = [check_for_sub_elems(cas, s) for s in propNargs]
        propElems = [check_for_sub_elems(cas, s) for s in propElems]
        propElems.sort(key=key_elemType)
        
        subLemmata = list(itertools.product(*lemmaSubs))

        lemmaProducts = len(list(itertools.product(*lemmaSubs)))
        propNargsProducts = len(list(itertools.product(*propNargs)))
        numPropElems = len([e for e in propElems if getElemType(e)!='zus'])
        minNumInfos = lemmaProducts*propNargsProducts+numPropElems
        
        #print(f'{lemmaProducts=:<15}{propNargsProducts=:<15}{numPropElems=:<15}')
        #print(f'min number of infos:    {minNumInfos}')
        
        partProps = makePartProps(subLemmata, propZuss, propNargs, propElems)
        if len(partProps)<minNumInfos:
            warnings.warn_explicit(f'The calculated number of infos ({len(partProps)}) is below the expected amount (min. {minNumInfos})! ({inceptionDocId=}, predHead number {i_pred})', UserWarning, getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno-2)
        
        #print(f'actual number of infos: {len(partProps)}')
        
        #add additional information to each proposition
        partPropStrs = []
        c_prop=ord('A')
        for prop in partProps:
            #add corefs, clitEnts, comments from each element, add metainformation
            addInformationDict(prop, 'coreferences', get_elem_coref)
            addInformationDict(prop, 'clitorisEntities', get_elem_clitents)
            addInformationDict(prop, 'comments', get_elem_comments)

            prop['retrievalTime'] = retrievalTime
            prop['inceptionDocId'] = inceptionDocId
            addMetaInformation(prop, cas)
            prop['infoId'] = f"{ str(i_pred).zfill(2) }{ chr(c_prop) }"
            c_prop+=1
            
            #get a new dict with string representations for all elements
            strProp = makeStrPartProp(prop)
            partPropStrs.append(strProp)
                
            #flatten dicts in dict for 2D representation in a table
            flattenStrProp(strProp)
            
            strProp = dict(sorted(list(strProp.items()), key=key_propDict))

            #for key, value in strProp.items():
            #    print(f'{key:18} -> {value}')
            #print("\n")
        
        #save propositions on disc
        df = pd.DataFrame(partPropStrs)
        df.to_csv("partPropStrs.csv", mode='a', header=False, index=False)
        
        
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