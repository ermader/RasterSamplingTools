# Font Database
`FontDatabase.json` is a file in JSON format used to determine a font which glyphs to test and how to test them.

The file is an array of objects. The first object contains default settings, and the rest are per-font objects.

## Test Objects
Test objects describe a particular glyph and how to test it. Their fields are:
* **glyph** : a *glyph spec* for the glyph to be tested - values can be a single character, "/" + *glyphName*, "uni" + 4 to 6 hex digits specifying a Unicode character code, or "gid" + a decimal glyph number.
* **range** : the range over which to draw rasters. Specified as *start* + "-" + *end* as a percentage of the distance from the bottom to the top of the glyph.
* **widthMethod** : specifies how to determine the right edge of a stroke. Values are *leftmost*, *rightmost* and *leastspread*.
* **mainContour** : specifies how to select the main contour of the glyph. Values are *largest*, *leftmost*, *rightmost* or *tallest*.
* **direction** : specifies the direction of the glyph. Values are *ltr* and *rtl*. This is used to determine the sign of the stroke angle.
* **loopDetect** : the value can be *true* or *false*. If it is *true* try to detect an inner loop in the glyph and use that to set the raster range.

### Example test objects
    {"glyph": "l", "loop_detect": true}
    {"glyph": "/l.ss01"}
    {"glyph": "gid300", "loop_detect": true}
    {"glyph": "j", "range": "40-62", "main_contour": "largest"}
    {"glyph": "m"}
    {"glyph": "l", "width_method": "rightmost"}
    {"glyph": "uni0627", "direction": "rtl"}

## The Default Settings Object
The default settings object has two fields:
* **default_tests** : an array of test objects listing the tests to be done for every font.
* **test_defaults** : a single test object without a *glyph* field, giving the default values for the fields.

### The test_defaults object
    "test_defaults": {"range": "30-70", "width_method": "leastspread", "main_contour": "tallest", "direction": "ltr", "loop_detect": false}

## The per-font Object
Per-font objects have the following fields:
* **ps_name** : the postscript name of the the font
* **family_name** : the family name of the font
* **full_name** : the full name of the font
* **tests** : an array of test objects
* **test_defaults** : a single test object, without a *glyph* field, that gives the default field values for every test
* **ignore_glyphs** : an array of *glyph specs* for glyphs (from the *default_tests*) that should be skipped for this font

**Notes:**
* Only one of *ps_name*, *family_name* or *full_name* should be given.
* The per-font objects will be searched in the order in which they are given in the file, so they should be listed from most-specific to lest-specific.
### Example per-font objects:
    {
    "ps_name": "AyresRoyal",
    "test_defaults": {"main_contour": "largest"},
    "tests": [
      {"glyph": "f", "range": "30-60"},
      {"glyph": "i", "range": "25-50"},
      {"glyph": "j", "range": "40-62"},
      {"glyph": "l", "range": "20-50"},
      {"glyph": "m"}
    ],
    "ignore_glyphs": ["I", "L"]
    },
    {
    "ps_name": "HelveticaNeue",
    "tests": [
      {"glyph": "uni006C"}
    ]
    },
    {
    "family_name": "Helvetica Neue",
    "tests": [
      {"glyph": "l"},
      {"glyph": "j"}
    ]
    },
    {
    "full_name": "Goudy Old Style Bold",
    "ignore_glyphs": ["uni0413", "uni0422", "uni04C0"]
    },


