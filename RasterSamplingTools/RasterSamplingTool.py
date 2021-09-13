"""\
Raster Sampling Tool

Created on February 5, 2021

@author Eric Mader
"""

import os
import pathlib
from sys import argv, exit, stderr
import pkg_resources
from TestArguments.TestArgumentIterator import TestArgs

from RasterSamplingTools import RasterSamplingTest
from RasterSamplingTools.FontDatabase import FontDatabase
from RasterSamplingTools.OutputDatabase import OutputDatabase

_usage = """
Usage:
rastersamplingtool --input inputPath --output outputPath
"""

class RasterSamplingToolArgs(TestArgs):
    __slots__ = "inputDir", "outputDir"

    def __init__(self):
        self.inputDir = ""
        self.outputDir = ""
        TestArgs.__init__(self, needGlyph=False)

    @classmethod
    def forArguments(cls, argumentList):
        args = RasterSamplingToolArgs()
        args.fontFile = "(dummy)"  # so TestArgumentIterator doesn't complain about missing "--font"...
        args.processArguments(argumentList)
        return args

    def processArgument(self, argument, arguments):
        if argument == "--input":
            self.inputDir = arguments.nextExtra("input directory")
        elif argument == "--output":
            self.outputDir = arguments.nextExtra("output directory")
        else:
            TestArgs.processArgument(self, argument, arguments)


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
        toolArgs = RasterSamplingToolArgs.forArguments(argumentList)
    except ValueError as error:
        print(programName + ": " + str(error), file=stderr)
        exit(1)

    testCount = failedCount = 0
    db = FontDatabase(pkg_resources.resource_filename("RasterSamplingTools", "FontDatabase.json"))
    outdb = OutputDatabase(os.path.join(toolArgs.outputDir, "OutputDatabase.json"))

    for path in pathlib.Path(toolArgs.inputDir).rglob("*.[otOT][tT][cfCF]"):
        testArgs = RasterSamplingTest.RasterSamplingTestArgs()
        testArgs.fontFile = str(path)
        testArgs.fontNumber = 0
        # testArgs.glyphName = toolArgs.glyphName
        # testArgs.glyphID = toolArgs.glyphID
        # testArgs.charCode = toolArgs.charCode
        reldir = os.path.dirname(os.path.relpath(path, os.path.dirname(toolArgs.inputDir)))
        testArgs.outdir = os.path.join(toolArgs.outputDir, reldir)
        # testArgs.widthMethod = RasterSamplingTest.RasterSamplingTestArgs.widthMethodLeastspread
        testArgs.outdb = outdb
        testArgs.silent = True
        os.makedirs(testArgs.outdir, exist_ok=True)

        print(f"{os.path.relpath(path, toolArgs.inputDir)}:")

        while True:
            try:
                testArgs.colon = True
                rasterTest = RasterSamplingTest.RasterSamplingTest(testArgs)
                testFont = rasterTest.font
                print(f"    {testFont.fullName}:")
                info = db.getFontInfo(testFont)
                tests = db.getTests(testFont, info)
                for test in tests:
                    try:
                        glyph, range, widthMethod, mainContour, direction, loopDetect = db.getTest(test)
                        testArgs.processGlyph(glyph)
                        testArgs.processRange(range)
                        testArgs.processWidthMethod(widthMethod)
                        testArgs.processMainContourType(mainContour)
                        testArgs.processDirection(direction)
                        testArgs.loopDetection = loopDetect
                        rasterTest.run()
                    except:
                        failedCount += 1
                        print("Failed\n")
                    finally:
                        testArgs.colon = False

                    testCount += 1

            except StopIteration:
                break

            if not (testArgs.fontFile.endswith(".ttc") or testArgs.fontFile.endswith("otc")): break
            testArgs.fontNumber += 1

    print(f"{testCount} tests, {failedCount} failures.")
    outdb.close()

if __name__ == "__main__":
    main()
