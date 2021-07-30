"""\
Command line argument processor for glyph tests.

Created on October 26, 2020

@author Eric Mader
"""
from re import fullmatch
from GlyphSpec import GlyphSpec
from FontDocTools.ArgumentIterator import ArgumentIterator

class TestArgumentIterator(ArgumentIterator):
    def __init__(self, arguments):
        ArgumentIterator.__init__(self, arguments)

    def nextOptional(self):
        """\
        Returns an optional next extra argument.
        Returns None if there’s no more argument, or if the next
        argument starts with “--”.
        """
        try:
            nextArgument = self._next()
        except StopIteration:
            return None

        if nextArgument.startswith("--"):
            self._nextPos -= 1
            return None

        return nextArgument

    def nextExtraAsFont(self, valueName):
        """\
        Returns a tuple (fontFile, fontName).
        The font file is taken from the first extra argument.
        If the font file name ends in “.ttc”, the font name is taken from
        the second extra argument; otherwise it is None.
        Raises ValueError if there’s no more argument, or if the next
        argument starts with “--”, or if it’s not a valid file name,
        or if there’s no font name along with a font file name ending in “.ttc”.
        """
        fontFile = self.nextExtra(valueName + " file")
        fontName = None
        if fontFile.endswith(".ttc"):
            fontName = self.nextExtra(valueName + " name")
        elif not fontFile.endswith(".ttf") and not fontFile.endswith(".TTF") and not fontFile.endswith(".otf") and not fontFile.endswith(".ufo"):
            raise ValueError(f"Expected file name with “.ttf” or “.otf” or “.ufo”; got “{fontFile}”.")
        return (fontFile, fontName)

    def getGlyphList(self):
        glist = []
        nextArg = self.nextOptional()
        while nextArg:
            glist.append(nextArg)
            nextArg = self.nextOptional()

        return glist

class TestArgs:
    __slots__ = "debug", "fontFile", "fontName", "fontNumber", "glyphSpec", "range"
    def __init__(self):
        self.debug = False
        self.fontFile = None
        self.fontName = None
        self.fontNumber = None
        self.glyphSpec = None
        self.range = (30, 70)
        # self.steps = 20

    @classmethod
    def forArguments(cls, argumentList):
        args = TestArgs()
        args.processArguments(argumentList)
        return args

    def processArguments(self, argumentList):
        arguments = TestArgumentIterator(argumentList)
        argumentsSeen = {}

        for argument in arguments:
            if argument in argumentsSeen:
                raise ValueError("Duplicate option “" + argument + "”.")
            argumentsSeen[argument] = True

            self.processArgument(argument, arguments)

        self.completeInit()

    def processArgument(self, argument, arguments):
        if argument == "--font":
            self.fontFile, self.fontName = arguments.nextExtraAsFont("font")
        elif argument == "--glyph":
            extra = arguments.nextExtra("glyph specification")
            self.processGlyph(extra)
        # elif argument == "--steps":
        #     self.steps = arguments.nextExtraAsPosInt("steps")
        elif argument == "--debug":
            self.debug = True
        else:
            raise ValueError(f"Unrecognized option “{argument}”.")

    def processGlyph(self, specString):
        self.glyphSpec = GlyphSpec(specString)

        if self.glyphSpec.type == GlyphSpec.unknown:
            raise ValueError(f"Invalid glyph specification “{specString}”.")
            self.glyphSpec = None

    def completeInit(self):
        """\
        Complete initialization of a shaping spec after some values have
        been set from the argument list.
        Check that required data has been provided and fill in defaults for others.
        Raise ValueError if required options are missing, or invalid option
        combinations are detected.
        """

        if not self.fontFile:
            raise ValueError("Missing “--font” option.")
        if not self.glyphSpec:
            raise ValueError("Missing “--glyph”")

    def getGlyph(self, font):
        return font.glyphForName(self.glyphSpec.nameForFont(font))
