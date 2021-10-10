"""\
Summarize OutputDatabase

Created on September 15, 2021

@author Eric Mader
"""

import os
from sys import argv, stderr, stdout
import statistics
from openpyxl import Workbook
from openpyxl.styles import Alignment
from openpyxl.utils import get_column_letter
from TestArguments.CommandLineArguments import CommandLineOption, CommandLineArgs
from RasterSamplingTools.OutputDatabase import OutputDatabase

# from TextUtilities import ctFont, stringWidth

_usage = """
Usage:
summarize --input inputPath [--output outputPath] [--widthFields mean | median | all]
"""

class SummarizeArgs(CommandLineArgs):
    widthFieldDict = {
        "mean": ["mean"],
        "median": ["median"],
        "most": ["min", "median", "mean", "max"],
        "all": ["min", "q1", "median", "mean", "q3", "max"],
    }

    options = [
        CommandLineOption("input", None, lambda a: a.nextExtra("input file"), "inputFile", None),
        CommandLineOption("output", None, lambda a: a.nextExtra("output file"), "outputFile", None, required=False),
        # CommandLineOption("widthFields", lambda s, a: CommandLineOption.valueFromDict(s.widthFieldDict, a, "width fields spec"), lambda a: a.nextExtra("width fields"), "widthFields", "median", required=False),
        # CommandLineOption("excel", None, True, "excel", False, required=False),
    ]

    def __init__(self):
        CommandLineArgs.__init__(self)
        self._options.extend(SummarizeArgs.options)

def cellName(row, column):
    return f"{get_column_letter(column)}{row}"

def rangeFormula(row, minColumn, maxColumn):
    minCell = cellName(row, minColumn)
    maxCell = cellName(row, maxColumn)

    return f"={maxCell}-{minCell}"

def percentFormula(row, medianColumn, rangeColumn):
    medianCell = cellName(row, medianColumn)
    rangeCell = cellName(row, rangeColumn)

    # return f"=IF({medianCell}<>0,{rangeCell}/{medianCell},#N/A)"
    return f"=IF({medianCell}<>0,{rangeCell}/{medianCell},{-9999.9 / 100.0})"


def main():
    argumentList = argv
    args = None
    programName = os.path.basename(argumentList.pop(0))

    if len(argumentList) == 0:
        print(_usage, file=stderr)
        exit(1)

    try:
        args = SummarizeArgs()
        args.processArguments(argumentList)
        args.widthFields = SummarizeArgs.widthFieldDict["most"]  # need a better way to do this...
    except ValueError as error:
        print(programName + ": " + str(error), file=stderr)
        exit(1)

    # font = ctFont("Calibri", 11)

    outdb = OutputDatabase(args.inputFile)
    widthFields = args.widthFields
    fitResultFields = ["stroke_angle", "r_squared"]

    wb = Workbook()
    ws = wb.active
    fieldNames = ["ps_name", "tested glyphs", "ignored glyphs"]
    fieldNames.extend(widthFields)
    fieldNames.extend(["range", "range as % of median", "min angle", "median angle", "mean angle", "max angle", "angle range", "range as % of median", "min R\u00B2", "median R\u00B2", "mean R\u00B2", "max R\u00B2", "R\u00B2 range", "range as % of median"])

    for column, label in enumerate(fieldNames):
        ws.cell(row=1, column=column+1, value=label).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    rowNumber = 2
    # maxWidth = 0
    for entry in outdb._db:
        psName = entry["ps_name"]
        testResults = entry["test_results"]
        widths = {wf: [] for wf in widthFields}
        fits = {frf: [] for frf in fitResultFields}
        goodGlyphCount = 0
        haveWidths = False

        # maxWidth = max(maxWidth, stringWidth(psName, font))

        row = [psName]

        for result in testResults.values():
            widthResults = result.get("widths", None)
            fitResults = result.get("fit_results", None)

            if widthResults:
                haveWidths = True
                goodGlyphCount += 1
                for widthField in widthFields:
                    widths[widthField].append(widthResults[widthField])

                for fitResultField in fitResultFields:
                    fits[fitResultField].append(fitResults[fitResultField])

        if haveWidths:
            means = [round(statistics.mean(widths[wf]), 1) for wf in widthFields]

            fitMeans = {frf: statistics.mean(fits[frf]) for frf in fitResultFields}
            fitMedians = {frf: statistics.median(fits[frf]) for frf in fitResultFields}
            fitMins = {frf: min(fits[frf]) for frf in fitResultFields}
            fitMaxs = {frf: max(fits[frf]) for frf in fitResultFields}

            widthColumn = 4
            row.extend([goodGlyphCount, len(testResults) - goodGlyphCount])
            row.extend(means)
            ws.append(row)
            ws.cell(row=rowNumber, column=widthColumn+4, value=rangeFormula(rowNumber, widthColumn, widthColumn+3))
            ws.cell(row=rowNumber, column=widthColumn+5, value=percentFormula(rowNumber, widthColumn+1, widthColumn+4)).number_format = "0.0%"

            angleColumn = widthColumn+6
            ws.cell(row=rowNumber, column=angleColumn, value=fitMins["stroke_angle"]).number_format = "0.0"
            ws.cell(row=rowNumber, column=angleColumn+1, value=fitMedians["stroke_angle"]).number_format = "0.0"
            ws.cell(row=rowNumber, column=angleColumn+2, value=fitMeans["stroke_angle"]).number_format = "0.0"
            ws.cell(row=rowNumber, column=angleColumn+3, value=fitMaxs["stroke_angle"]).number_format = "0.0"
            ws.cell(row=rowNumber, column=angleColumn+4, value=rangeFormula(rowNumber, angleColumn, angleColumn+3)).number_format = "0.0"
            ws.cell(row=rowNumber, column=angleColumn+5, value=percentFormula(rowNumber, angleColumn+1, angleColumn+4)).number_format = "0.0%"

            r2Column = angleColumn + 6
            ws.cell(row=rowNumber, column=r2Column, value=fitMins["r_squared"]).number_format = "0.0000"
            ws.cell(row=rowNumber, column=r2Column+1, value=fitMedians["r_squared"]).number_format = "0.0000"
            ws.cell(row=rowNumber, column=r2Column+2, value=fitMeans["r_squared"]).number_format = "0.0000"
            ws.cell(row=rowNumber, column=r2Column+3, value=fitMaxs["r_squared"]).number_format = "0.0000"
            ws.cell(row=rowNumber, column=r2Column+4, value=rangeFormula(rowNumber, r2Column, r2Column+3)).number_format = "0.0000"
            ws.cell(row=rowNumber, column=r2Column+5, value=percentFormula(rowNumber, r2Column+1, r2Column+4)).number_format = "0.0%"
        else:
            # ws.cell(row=rowNumber, column=1, value=psName)
            # ws.cell(row=rowNumber, column=2, value=-999.9)
            # ws.append([psName, goodGlyphCount, len(testResults) - goodGlyphCount, -9999.9])
            ws.append([psName, goodGlyphCount, len(testResults) - goodGlyphCount])

        rowNumber += 1

    # ws.column_dimensions["A"].bestFit = True
    # ws.column_dimensions["A"].auto_size = True
    ws.column_dimensions["A"].width = 30  # maxWidth * .15?

    wb.save(args.outputFile)

if __name__ == "__main__":
    main()



