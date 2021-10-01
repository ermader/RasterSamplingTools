"""\
Summarize OutputDatabase

Created on September 15, 2021

@author Eric Mader
"""

import os
from sys import argv, stderr, stdout
import statistics
from TestArguments.CommandLineArguments import CommandLineOption, CommandLineArgs
from RasterSamplingTools.OutputDatabase import OutputDatabase

_usage = """
Usage:
summarize --input inputPath [--output outputPath] [--widthFields mean | median | all]
"""

class SummarizeArgs(CommandLineArgs):
    widthFieldDict = {
        "mean": ["mean"],
        "median": ["median"],
        "all": ["min", "q1", "median", "mean", "q3", "max"],
    }

    options = [
        CommandLineOption("input", None, lambda a: a.nextExtra("input file"), "inputFile", None),
        CommandLineOption("output", None, lambda a: a.nextExtra("output file"), "outputFile", None, required=False),
        CommandLineOption("widthFields", lambda s, a: CommandLineOption.valueFromDict(s.widthFieldDict, a, "width fields spec"), lambda a: a.nextExtra("width fields"), "widthFields", "median", required=False),
    ]

    def __init__(self):
        CommandLineArgs.__init__(self)
        self._options.extend(SummarizeArgs.options)

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
    except ValueError as error:
        print(programName + ": " + str(error), file=stderr)
        exit(1)

    outdb = OutputDatabase(args.inputFile)
    outFile = open(args.outputFile, "w") if args.outputFile else stdout
    widthFields = args.widthFields

    for entry in outdb._db:
        psName = entry["ps_name"]
        testResults = entry["test_results"]
        widths = {wf: [] for wf in widthFields}
        haveWidths = False

        outFile.write(f"{psName}\t")

        for result in testResults.values():
            widthResults = result.get("widths", None)

            if widthResults:
                haveWidths = True
                for widthField in widthFields:
                    widths[widthField].append(widthResults[widthField])

        if haveWidths:
            means = [f"{round(statistics.mean(widths[wf]), 1)}" for wf in widthFields]
            outFile.write(f"{', '.join(means)}\n")
        else:
            outFile.write("-999\n")

    if args.outputFile:
        outFile.close()

if __name__ == "__main__":
    main()



