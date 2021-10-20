"""\
Raster Sampling Tool

Created on February 5, 2021

@author Eric Mader
"""

import os
import pathlib
from sys import argv, exit, stderr
import pkg_resources
from TestArguments.CommandLineArguments import CommandLineOption, CommandLineArgs

from RasterSamplingTools import RasterSamplingTest
from RasterSamplingTools.FontDatabase import FontDatabase
from RasterSamplingTools.OutputDatabase import OutputDatabase

_usage = """
Usage:
rastersamplingtool --input inputPath --output outputPath
"""

class RasterSamplingToolArgs(CommandLineArgs):
    options = [
        CommandLineOption("input", None, lambda a: a.nextExtra("input directory"), "inputDir", None),
        CommandLineOption("output", None, lambda a: a.nextExtra("output directory"), "outputDir", None),
    ]

    def __init__(self):
        CommandLineArgs.__init__(self)
        self._options.extend(RasterSamplingToolArgs.options)

def checkGlyph(testArgs, testFont):
    if testArgs.glyphName: return testFont.hasGlyphName(testArgs.glyphName)
    if testArgs.glyphID: return testFont.hasGlyphIndex(testArgs.glyphID)
    if testArgs.charCode: return testFont.hasCharacterCode(testArgs.charCode)
    return False

def main():
    argumentList = argv
    args = None
    programName = os.path.basename(argumentList.pop(0))
    if len(argumentList) == 0:
        print(_usage, file=stderr)
        exit(1)

    try:
        toolArgs = RasterSamplingToolArgs()
        toolArgs.processArguments(argumentList)
    except ValueError as error:
        print(programName + ": " + str(error), file=stderr)
        exit(1)

    testCount = failedCount = 0
    db = FontDatabase(pkg_resources.resource_filename("RasterSamplingTools", "FontDatabase.json"))
    outdb = OutputDatabase(os.path.join(toolArgs.outputDir, "OutputDatabase.json"))

    for path in pathlib.Path(toolArgs.inputDir).rglob("*.[otOT][tT][cfCF]"):
        testArgs = RasterSamplingTest.RasterSamplingTestArgs()
        testArgs.fontFile = str(path)
        testArgs.fontName = None
        testArgs.fontNumber = 0
        testArgs.debug = False
        reldir = os.path.dirname(os.path.relpath(path, os.path.dirname(toolArgs.inputDir)))
        testArgs.outdir = os.path.join(toolArgs.outputDir, reldir)
        testArgs.outdb = outdb
        testArgs.silent = True
        os.makedirs(testArgs.outdir, exist_ok=True)

        print(f"{os.path.relpath(path, toolArgs.inputDir)}:")

        while True:
            try:
                testArgs.colon = True
                testArgs.showFullName = True
                rasterTest = RasterSamplingTest.RasterSamplingTest(testArgs)
                testFont = rasterTest.font
                info = db.getFontInfo(testFont)
                tests = db.getTests(testFont, info)
                for test in tests:
                    try:
                        glyph, range, widthMethod, mainContour, direction, loopDetect = db.getTest(test)

                        propsDict = {
                            "glyphSpec": glyph,
                            "range": range,
                            "widthMethod": widthMethod,
                            "mainContourType": mainContour,
                            "directionAdjust": direction,
                            "loopDetection": loopDetect
                        }

                        testArgs.setProps(propsDict)
                        rasterTest.run()
                    except:
                        failedCount += 1
                        print("Failed\n")
                    finally:
                        testArgs.colon = False
                        testArgs.showFullName = False

                    testCount += 1

            except StopIteration:
                break

            if not (testArgs.fontFile.endswith(".ttc") or testArgs.fontFile.endswith("otc")): break
            testArgs.fontNumber += 1

    print(f"{testCount} tests, {failedCount} failures.")
    outdb.close()

if __name__ == "__main__":
    main()
