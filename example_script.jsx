// Example JSX script for Photoshop API Server
// This script will invert the colors of the input image and save as PNG

// Configuration (will be replaced by Python)
var inputPath = "{{INPUT_PATH}}";
var outputPath = "{{OUTPUT_PATH}}";

try {
    // Open the input file
    var inputFile = new File(inputPath);
    if (!inputFile.exists) {
        throw new Error("Input file not found: " + inputPath);
    }
    
    var docRef = app.open(inputFile);
    
    // Invert colors
    docRef.activeLayer.invert();
    
    // Save as PNG
    var pngSaveOptions = new PNGSaveOptions();
    var outputFile = new File(outputPath);
    docRef.saveAs(outputFile, pngSaveOptions, true, Extension.LOWERCASE);
    
    // Close the document without saving changes (we already saved as PNG)
    docRef.close(SaveOptions.DONOTSAVECHANGES);
    
    // Notify success (optional, but helpful for debugging)
    $.writeln("Successfully processed image: " + outputPath);
    
} catch (e) {
    $.writeln("Error: " + e.toString());
    if (typeof e.stack !== "undefined") {
        $.writeln("Stack: " + e.stack);
    }
    // Clean up if document is open
    if (typeof docRef !== "undefined" && docRef !== null) {
        try {
            docRef.close(SaveOptions.DONOTSAVECHANGES);
        } catch (closeError) {
            $.writeln("Error closing document: " + closeError.toString());
        }
    }
    // Exit with error code 1 (but don't throw uncaught exception)
    $.exit(1);
}

