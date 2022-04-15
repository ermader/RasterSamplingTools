# RasterSamplingTool
This tool will recursively scan a directory for all TrueType fonts (.ttf, .ttc, .otf, .otc).
For font collections (.ttc, .otc) it will process each font in the collection.
It will look each funt up in the file `FontDatabase.json` and get a list of glyphs and options to test. It will call `rastersamplingtest` to process each glyph with the given options.

See [RasterSamplingTest](RasterSamplingTest.md) and [FontDatabase](FontDatabase.md) for details.

## Command Line Options
* **\-\-input *path*** - the path to the directory containing the input fonts.
* **\-\-output *path*** - the path to the directory where the output graphs and output database will be written.
