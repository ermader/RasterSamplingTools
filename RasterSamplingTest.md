# RasterSamplingTest
A tool for analyzing a glyph in a font.

## Command Line Options
The tool is invoked on the command line as `rastersamplingtest` with the options described below. The *\-\-font* and *\-\-glyph* options are required, all others are optional.

* **\-\-font (*fontFile*.ttf | *fontFile*.otf | ( (*fontFile*.ttc | *fontFile*.otc) *fontName*)** – the font file to be used. If *fontFile*.ttc or *fontFile*.otc is specified then *fontName* must be specified.
* **\-\-glyph *glyphSpec*** - the glyph to be analyzed. *glyphSpec* is either a single character, "/" + *glyphName*, "uni" + 4 to 6 hex digits specifying a Unicode character code, or "gid" + a decimal glyph number.
* **\-\-debug** - enables debug output.
* **\-\-widthMethod *method*** - specifies how to identify the right edge of the stroke. *method* is *leftmost* to use the leftmost edge, *rightmost* to use the rightmost edge or *leastspread* to use the edge that results in a stroke with the least variable width.
* **\-\-mainContour *type*** - specifies how to identify the main contour in the glyph. *type* can be *largest*, *leftmost*, *rightmost* or *tallest*. The default is *tallest*.
* **\-\-range *rangeSpec*** - specifies the range over which to draw rasters. Specified as *start* + "-" + *end* as a percentage of the distance from the bottom to the top of the glyph. The default value is "30-70".
* **\-\-direction *dir*** - specifies if the glyph is left to right (*dir* is *ltr*) or right to left (*dir is *rtl*) The default is *ltr*. Used to determine the sign of the stroke angle.
* **\-\-loopDetection** - if present, the tool will try to detect an inner loop in the glyph and use that to set the raster range.
* **\-\-outdb *path*** - specifies the path to the output database file. If not present, the output database file is not updated.
