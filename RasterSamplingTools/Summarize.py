"""\
Summarize OutputDatabase

Created on September 15, 2021

@author Eric Mader
"""

from sys import argv, stderr
import statistics
from RasterSamplingTools.OutputDatabase import OutputDatabase

_usage = """
Usage:
summarize inputPath [mean | median | all]
"""

def main():
    widthFieldDict = {
        "mean": ["mean"],
        "median": ["median"],
        "all": ["min", "q1", "median", "mean", "q3", "max"],
    }

    if len(argv) == 1:
        print(_usage, file=stderr)
        exit(1)

    widthField = "median" if len(argv) < 3 else argv[2]
    fileName = argv[1]
    outdb = OutputDatabase(fileName)
    widthFields = widthFieldDict[widthField]

    for psName, entry in outdb._db.items():
        fullName = entry["full_name"]
        testResults = entry["test_results"]
        widths = {wf: [] for wf in widthFields}

        for result in testResults.values():
            widthResults = result["widths"]

            for widthField in widthFields:
                widths[widthField].append(widthResults[widthField])

        medians = [f"{wf}: {round(statistics.median(widths[wf]), 2)}" for wf in widthFields]
        print(f"ps_name: {psName}, full_name: {fullName}, {', '.join(medians)}")

if __name__ == "__main__":
    main()



