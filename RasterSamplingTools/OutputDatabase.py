"""\
Output database

Created on July 22, 2021

@author Eric Mader
"""

import typing
import json

from TestArguments.Font import Font


class OutputDatabase(object):

    FontEntry = dict[str, typing.Any]
    TestResults = dict[str, typing.Any]

    def __init__(self, file: str):
        self._file = file
        try:
            inFile = open(file)
        except FileNotFoundError:
            self._db: list[OutputDatabase.FontEntry] = []
        else:
            # We could check for errors in the input file
            # but it's probably better to just err out...
            self._db: list[OutputDatabase.FontEntry] = json.load(inFile)
            inFile.close()

    @property
    def db(self) -> list[FontEntry]:
        return self._db

    def close(self):
        outFile = open(self._file, "w")
        json.dump(self._db, outFile, indent=4)
        outFile.close()

    def getEntry(self, font: Font):
        psName = font.postscriptName

        for entry in self._db:
            if entry["ps_name"] == psName:
                break
        else:
            entry: OutputDatabase.FontEntry = {
                "ps_name": psName,
                "full_name": font.fullName,
                "test_results": {},
            }
            self._db.append(entry)

        if "full_name" not in entry:
            entry["full_name"] = font.fullName

        return entry

    def getTestResults(self, entry: FontEntry) -> TestResults:
        return entry["test_results"]
