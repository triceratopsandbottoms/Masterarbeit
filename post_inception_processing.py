from pycaprio import Pycaprio
from pycaprio.mappings import InceptionFormat
from zipfile import ZipFile
from io import BytesIO
from cassis import Cas

INCEPTION_URL = "http://localhost:8080"
INCEPTION_USER = "remote-api"
INCEPTION_PW = "MDT2azx-qae0fbg*uhz"
PROJECT_ID = 2
INCEPTION_FORMAT = InceptionFormat.UIMA_CAS_XMI_XML_1_1
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


client = Pycaprio(INCEPTION_URL, authentication=(INCEPTION_USER, INCEPTION_PW))

annotation_zip = ZipFile(BytesIO(client.api.annotation(PROJECT_ID, 1, USER, annotation_format=INCEPTION_FORMAT))) # Downloads annotations on document 1

for item in [i for i in annotation_zip.filelist if i.filename.endswith(".xmi")]:
    annotation_xmi = annotation_zip.read(item)
    print(len(annotation_xmi))

with open("tmp/test.xmi", 'wb') as f:
    f.write(annotation_xmi)

print("annotations downloaded")
    

"""
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
    - Relation.Dependents als zusätzliches Span-Feature aufnehmen, danach die Relation löschen (vorausgesetzt, "Relation zum Prädikat" wurde schon als Span-Feature implementiert)
    - CoreferencesaslinksReferenzenLink genauso als zusätzliches Coreferencesaslinks-Feature integrieren und danach löschen
    - Bei pred-Spans ohne SurfaceForm: Lemma als SurfaceForm setzen
- Spans und Coreferencesaslinks: Feature ClitRef setzen
    - wenn ClitorisEntity im Span enthalten ist -> ClitRef = xmi:id der ClitorisEntity 
    - wenn eine referenz auf einen Coreferencesaslinks-span mit ClitRef-Feature im Span liegt -> den Wert übernehmen
- Für alle pred-Spans: rekursiv Dependent-Spans suchen und dieses Set von Spans als Generalproposition speichern
- Je Generalproposition die Teilpropositionen berechnen und speichern
"""