var items = Zotero.getActiveZoteroPane().getSelectedItems();

for (let item of items) {
        let allAnnotations = await item.getAnnotations().filter((item) => item.annotationType === "highlight");
    for (let annotation of allAnnotations) {
        var bookID = item.key;
        var annoID = annotation.key;
        var annoPage = annotation.annotationPageLabel;
        var annoText = annotation.annotationText;
        var title = `${bookID}_${annoID}_${annoPage}`;
        var path = `C:\\Users\\annik\\ZoteroExports\\${bookID}\\${title}.txt`;
        await Zotero.File.putContentsAsync(path, annoText);
    }
}