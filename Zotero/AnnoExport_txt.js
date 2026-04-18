async function saveAnnotation(item, annotation, data){
    let bookID = item["parentItem"].getField("key");
    let bookTitle = item["parentItem"].getField("title");
    let year = item["parentItem"].getField("date");
    let attID = item.getField("key");
    var annoID = annotation.key;
    var annoPage = annotation.annotationPageLabel;
	var annoText = annotation.annotationText.replaceAll('\n', 'ABSATZ');
    var title = `${bookID}_${annoID}_${annoPage}`;
    data.push([bookID, bookTitle, year, annoID, annoPage, annoText]);
}

var items = Zotero.getActiveZoteroPane().getSelectedItems();
let data = new Array();


for (let item of items) {
    let allAnnotations = await item.getAnnotations().filter((item) => item.annotationType === "highlight" && item.annotationColor === "#ffd400"); //yellow
    for (let annotation of allAnnotations) {
        saveAnnotation(item, annotation, data);
    }
}
const content = data.map(row => row.join('\t')).join('\n');
const tablePath = `C:\\Users\\annik\\ZoteroExports\\textAnnotations.csv`;
await Zotero.File.putContentsAsync(tablePath, content);