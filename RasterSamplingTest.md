# RasterSamplingTest
A tool for analyzing a glyph in a font.

## Processing
* Select the main contour based on the **\-\-mainContour** command line argument.
* Fail if the main contour has an area less than 10% of the area of the whole glyph, or has less than 50% of the height of the whole glyph.
* Construct a list of curves containing all the curves in the main contour plus all the curves in any other contour whose bounding rectangle in contained in the bounding rectangle of the main contour and has an area that is at leat 5% of the area of the main contour. Call this *curveList*.
* Construct 50 horizontal raster lines from the bottom to the top of the glyph that span the width of the glyph.
* For each raster:
  * construct a list of curves in *curveList* that cross the y coordinate of the raster. Call this *curvesAtY*.
  * compute a list of the points where the curves in *curvesAtY* intersect the raster. Call this *intersections*.
  * the leftmost point in *intersections* is on the left edge of the stroke. Call it *p1*.
  * find the leftmost in *intersections* on curves that have the opposite direction from the curve on the left edge of the stroke. Call this *p2l*.
  * find the rightmost in *intersections* on curves that have the opposite direction from the curve on the left edge of the stroke. Call this *p2r*.
  * construct a raster line from *p1* to *p2l* and append it to the list called *rastersLeft*.
  * construct a raster line from *p1* to *p2r* and append it to the list called *rastersRight*.
* If the command line argument **\-\-loopDetecdtion** is present and *curveList* contains a single inner contour that extends at least 70% of the way to the top of the glyph, save its bounding rectangle as *innerBounds*.
* For *rastersLeft* and *rastersRight*:
  * compute a list of the lengths of the rasters. These lengths are the width of the stroke at the raster line.
  * compute the 2nd derivative of the lengths.
  * find the longest range of rasters where the 2nd derivatives are less than 5.
  * if the length of the longest range is greater than or equal to 5, use this range.
  * otherwise, use the range of *innerBounds* for the raster range, otherwise use the range from the **\-\-range** command line argument.
  * fit a line through the midpoints of the rasters in the range. the angle of this line is the stroke angle.
* If the **\-\-widthMethod** command line argument is *leftmost* use the results from *rastersLeft*,
if it is *rightmost* use the results from *rastersRight*. If it is *bestfit* use whichever results have the best fit.

## Command Line Options
The tool is invoked on the command line as `rastersamplingtest` with the options described below. The *\-\-font* and *\-\-glyph* options are required, all others are optional.

* **\-\-font (*fontFile*.ttf | *fontFile*.otf | *fontFile*.ttc  *fontName* | *fontFile*.otc *fontName*)** – the font file to be used. If *fontFile*.ttc or *fontFile*.otc is specified then *fontName* must be specified.
* **\-\-glyph *glyphSpec*** - the glyph to be analyzed. *glyphSpec* is either a single character, "/" + *glyphName*, "uni" + 4 to 6 hex digits specifying a Unicode character code, or "gid" + a decimal glyph number.
* **\-\-widthMethod *method*** - specifies how to identify the right edge of the stroke. *method* is *leftmost* to use the leftmost edge, *rightmost* to use the rightmost edge or *leastspread* to use the edge that results in a stroke with the least variable width.
* **\-\-mainContour *type*** - specifies how to identify the main contour in the glyph. *type* can be *largest*, *leftmost*, *rightmost* or *tallest*. The default is *tallest*.
* **\-\-range *rangeSpec*** - specifies the range over which to draw rasters. Specified as *start* + "-" + *end* as a percentage of the distance from the bottom to the top of the glyph. The default value is "30-70".
* **\-\-direction *dir*** - specifies if the glyph is left to right (*dir* is *ltr*) or right to left (*dir is *rtl*) The default is *ltr*. Used to determine the sign of the stroke angle.
* **\-\-outdb *path*** - specifies the path to the output database file. If not present, the output database file is not updated.
* **\-\-loopDetection** - if present, the tool will try to detect an inner loop in the glyph and use that to set the raster range.
* **\-\-autoRangeOff** - If present, disable automatic range detection
* **\-\-colon** - if present, calculate the italic angle based on the colon glyph in the font. (if that glyph is present)
* **\-\-debug** - enables debug output.
