"""\
Font Database

Created on March 19, 2021

@author Eric Mader
"""

import typing

import json

# from re import fullmatch
from TestArguments.GlyphSpec import GlyphSpec
from TestArguments.Font import Font


class FontDatabase:
    __slots__ = "_db", "_defaultTests", "_testDefaults"

    Info = dict[str, typing.Any]
    Test = dict[str, typing.Any]

    def __init__(self, file: str):
        self._db = json.load(open(file))

        # This code assumes that the default tests are first in the file
        # and always exist
        self._defaultTests: list[FontDatabase.Test] = self._db[0].get("default_tests", "")
        self._testDefaults: FontDatabase.Test = self._db[0].get("test_defaults", "")

    def getFontInfo(self, font: Font) -> Info:
        NameFunc = typing.Callable[[Font], typing.Optional[str]]
        psNameFunc: NameFunc = lambda f: f.postscriptName
        familyNameFunc: NameFunc = lambda f: f.familyName
        fullNameFunc: NameFunc = lambda f: f.fullName

        for info in self._db:
            for key, func in [
                ("ps_name", psNameFunc),
                ("family_name", familyNameFunc),
                ("full_name", fullNameFunc),
            ]:
                name = info.get(key, "")
                if name == func(font):
                    return info

        return {}

    def getTestDefaults(self, info: Info) -> Test:
        testDefaults = self._testDefaults.copy()

        infoDefaults = info.get("test_defaults", {})
        for key, value in infoDefaults.items():
            testDefaults[key] = value

        return testDefaults

    def getIgnoreGlyphList(self, font: Font, info: Info) -> list[GlyphSpec]:
        ignoreList: list[GlyphSpec] = []
        infoIgnoreList = info.get("ignore_glyphs", [])

        for spec in infoIgnoreList:
            glyphSpec = GlyphSpec(spec)
            nameSpec = typing.cast(GlyphSpec, glyphSpec.nameSpecForFont(font))
            ignoreList.append(nameSpec)

        return ignoreList

    @staticmethod
    def testsHaveGlyph(tests: list[Test], glyph: str):
        for test in tests:
            if test.get("glyph", "") == glyph:
                return True

        return False

    @staticmethod
    def copyTest(test: Test, glyphNameSpec: str, testDefaults: Test) -> Test:
        testCopy = test.copy()
        testCopy["glyph"] = glyphNameSpec

        for key, value in testDefaults.items():
            if key not in testCopy:
                testCopy[key] = value

        return testCopy

    def getTests(self, font: Font, info: Info) -> list[Test]:
        tests: list[FontDatabase.Test] = []
        infoTests = info.get("tests", [])
        testDefaults = self.getTestDefaults(info)
        ignoreList = self.getIgnoreGlyphList(font, info)

        for test in infoTests:
            glyphSpec = GlyphSpec(test["glyph"])
            glyphNameSpec = glyphSpec.nameSpecForFont(font)
            if glyphNameSpec:
                tests.append(self.copyTest(test, glyphNameSpec, testDefaults))

        for defaultTest in self._defaultTests:
            glyphSpec = GlyphSpec(defaultTest["glyph"])
            glyphNameSpec = glyphSpec.nameSpecForFont(font)
            if (
                glyphNameSpec
                and not glyphNameSpec in ignoreList
                and not self.testsHaveGlyph(tests, glyphNameSpec)
            ):
                tests.append(self.copyTest(defaultTest, glyphNameSpec, testDefaults))

        return tests

    def getTest(self, test: Test):
        glyph: str = test["glyph"]
        range = test["range"]
        widthMethod: str = test["width_method"]
        mainContour: str = test["main_contour"]
        direction: str = test["direction"]
        loopDetect: bool = test["loop_detect"]

        return glyph, range, widthMethod, mainContour, direction, loopDetect


def printTests(db: FontDatabase, font: Font):
    info = db.getFontInfo(font)
    print(f"Tests for {font.fullName}")
    tests = db.getTests(font, info)

    for test in tests:
        glyph, range, widthMethod, mainContour, direction, loopDetect = db.getTest(test)
        print(
            f"    glyph: {glyph}, range: {range}, width_method: {widthMethod}, main_contour: {mainContour}, direction: {direction}, loop_detect: {loopDetect}"
        )
    print()


def test():
    db = FontDatabase("FontDatabase.json")
    printTests(
        db, Font("/Users/emader/Downloads/Eric-test-fonts/Ayres Royal/AyresRoy.otf")
    )
    printTests(
        db, Font("/Users/emader/Downloads/Eric-test-fonts/Ayres Royal/AYRERP__.TTF")
    )
    printTests(
        db,
        Font(
            "/Users/emader/Downloads/TestFonts/Rough paths/BakerieRough/BakerieRough-Medium.otf"
        ),
    )
    printTests(
        db, Font("/Users/emader/Downloads/AppFonts/Loopiejuice/Loopiejuice-Regular.ttf")
    )
    printTests(
        db, Font("/Users/emader/Downloads/AppFonts/GoudyOldStyle/GoudyOldSty-Reg.ttf")
    )
    printTests(
        db, Font("/Users/emader/Downloads/AppFonts/GoudyOldStyle/GoudyOldSty-Bol.ttf")
    )
    printTests(
        db, Font("/Users/emader/Downloads/Eric-test-fonts/Catwing/catwing fuzz.otf")
    )
    printTests(db, Font("/System/Library/Fonts/GeezaPro.ttc", fontName="GeezaPro"))
    printTests(db, Font("/System/Library/Fonts/Supplemental/AppleMyungjo.ttf"))
    printTests(
        db,
        Font("/System/Library/Fonts/STHeiti Medium.ttc", fontName="STHeitiSC-Medium"),
    )


if __name__ == "__main__":
    test()
