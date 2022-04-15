# RasterSamplingTools
A set of tools for analyzing glyphs.

## RasterSamplingTest
This tool analyzes a given glyph in a given font. It lays horizontal rasters across the glyph and attempts to identify a vertical stroke.
It then calculates the stroke width and the stroke angle.

See [RasterSamplingTest](RasterSamplingTest.md) for details.

## RasterSamplingTool
This tool recursively scans a give directory structure for TrueType fonts. And calls `RasterSamplingTest` consulting `FontDatabase.json` for the list
of glyphs to test. Results are recorded in `OutputDatabase.json`.

See [RasterSamplingTool](RasterSamplingTool.md) and [FontDatabase](FontDatabase.md) for details.

## Summarize
This tool reads the data in an `OutputDatabase.json` file and writes an Excel spreadsheet with a summary row for each font.

See [Summarize](Summarize.md) for details.

## Installation

The tools require Python 3.9 or later, and the [FontDocTools](https://bitbucket.org/LindenbergSW/FontDocTools), [UnicodeData](https://github.com/ermader/UnicodeData), [TestArguments](https://github.com/ermader/TestArguments) and [PathLib](https://github.com/ermader/PathLib) packages. The tools have been tested on macOS 11.5 but may also work on earlier versions of MacOS and other platforms.

* Check whether your system has Python 3.9 or later installed:

        python3 --version

    On macOS 10.15, this causes the OS to offer installation of command line tools, which include Python 3.9. Otherwise, if you don’t have at least Python 3.9, download and install a current version of [Python 3](https://www.python.org/downloads/mac-osx/).

 * If you haven’t yet, download the RasterSamplingTools package onto your system:

        cd /parent/directory/for/RasterSamplingTools/
        git clone https://github.com/ermader/RasterSamplingTools

* Run the `install.sh` script. This will download and install all required packages:

        zsh RasterSamplingTools/install.sh

This script will create a Python virtual environment in the parent directory in a folder named FontTools-env. Whenever you want to run the installed scripts you'll need to activate the virtual environment first:

        source FontTools-env/bin/activate

If you’d like to run the test cases in the Tests directories, you will also need to install the [pytest](https://docs.pytest.org/en/latest/index.html) package from the Python Package Index:

    pip install -U pytest

If you’d like to run the pylint source code checker on the packages, you will also need to install the [pylint](https://pylint.readthedocs.io/en/latest/index.html) package from the Python Package Index:

    pip install -U pylint

