#RasterSamplingTools
A set of tools for analyzing glyphs.

##RasterSamplingTest
This tool analyzes a given glyph in a given font. It lays horizontal rasters across the glyph and attempts to identify a vertical stroke.
It then calculates the stroke width and the stroke angle.

See [RasterSamplingTest](RasterSamplingTest.md) for details.

##RasterSamplingTool
This tool recursively scans a give directory structure for TrueType fonts. And calls `RasterSamplingTest` consulting `FontDatabase.json` for the list
of glyphs to test. Results are recorded in `OutputDatabase.json`.

See [RasterSamplingTool](RasterSamplingTool.md) for details.
