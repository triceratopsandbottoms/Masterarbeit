async function saveAnnotation(item, annotation, data){
    let bookID = item["parentItem"].getField("key");
    let bookTitle = item["parentItem"].getField("title");
    let year = item["parentItem"].getField("date");
    let attID = item.getField("key");
    let attFilename = item.attachmentFilename;
    var annoID = annotation.key;
    var annoPage = annotation.annotationPageLabel;
    var annoRect = annotation.annotationPosition;
    var title = `${bookID}_${annoID}_${annoPage}`;
    //var path = `C:\\Users\\annik\\ZoteroExports\\Images\\${bookID}\\${title}.jpg`;
    let pdfPath = `C:\\Users\\annik\\Zotero\\storage\\${attID}\\${attFilename}`;
    data.push([bookID, bookTitle, year, annoID, annoPage, pdfPath, annoRect, attFilename]);
    //await Zotero.File.putContentsAsync(path, annoImage);
}

var items = Zotero.getActiveZoteroPane().getSelectedItems();
let data = new Array();


for (let item of items) {
    let allAnnotations = await item.getAnnotations().filter((item) => item.annotationType === "image" && item.annotationColor === "#ffd400"); //yellow
    for (let annotation of allAnnotations) {
        saveAnnotation(item, annotation, data);
    }
}
const content = data.map(row => row.join('\t')).join('\n');
const tablePath = `C:\\Users\\annik\\ZoteroExports\\Table_imageAnnotations.csv`;
await Zotero.File.putContentsAsync(tablePath, content);