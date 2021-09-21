# Summarize
This tool reads a `FontDatabase.json` file written by `RasterSamplingTool` and prints a simmary line for each font.
The summary line shows the font's postscript name, its full name and the median values of the selected stroke widths.

### Example summary line
    ps_name: AcademyEngraved, full_name: Academy Engraved, median: 106.5

See [RasterSamplingTool](RasterSamplingTool.md) and [OutputDatabase](OutputDatabase.md) for details.

## Command Line Options
* **\-\-input *path*** - the path to the `OutputDatabase.json` file.
* **\-\-output *path*** - the path to the summary file. If this option isn't given, the summary is written to `stdout`.
* **\-\-widthFields *fields*** - *fields* can be *mean*, *median* or *all*. The default is *median*.
