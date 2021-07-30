"""\
RSTFont.py

Created on July 30, 2021
Based on GTFont from GlyphTest.py

@author Eric Mader
"""

from fontTools.ttLib import ttFont, TTLibError
from FontDocTools.Font import Font, Glyph

class RSTFont(Font):
    def __init__(self, fontFile, fontName=None, fontNumber=None):
        Font.__init__(self, fontFile, fontName, fontNumber)

    def __contains__(self, item):
        return item in self._ttFont

    def __getitem__(self, item):
        return self._ttFont[item]

    @classmethod
    def _getFontName(cls, ttFont, nameID):
        nameRecord = ttFont["name"].getName(nameID, 3, 1, 0x0409)  # name, Windows, Unicode BMP, English
        if nameRecord is None:
            nameRecord = ttFont["name"].getName(nameID, 1, 0)  # name, Mac, Roman
        if nameRecord is not None:
            return str(nameRecord)
        return None

    @classmethod
    def _getPostScriptName(cls, ttFont):
        return cls._getFontName(ttFont, 6)

    @classmethod
    def _getFullName(cls, ttFont):
        return cls._getFontName(ttFont, 4)

    @classmethod
    def _getFamilyName(cls, ttFont):
        return cls._getFontName(ttFont, 1)

    @property
    def postscriptName(self):
        return self._getPostScriptName(self._ttFont)

    @property
    def fullName(self):
        return self._getFullName(self._ttFont)

    @property
    def familyName(self):
        return self._getFamilyName(self._ttFont)

    def glyphNameForCharacterCode(self, charCode):
        return self._ttFont.getBestCmap().get(charCode, "")

    @property
    def glyphSet(self):
        return self._ttFont.getGlyphSet()

    @property
    def hmtxMetrics(self):
        if not self._hMetrics:
            self._hMetrics = self["hmtx"].metrics
        return self._hMetrics

    @property
    def vmtxMetrics(self):
        if not self._vMetrics and "vmtx" in self:
            self._vMetrics = self["vmtx"].metrics
        return self._vMetrics

    @property
    def typographicAscender(self):
        return self.fontMetric("OS/2", "sTypoAscender")

    @property
    def typographicDescender(self):
        return self.fontMetric("OS/2", "sTypoDescender")

    def __str__(self):
        return self.postscriptName

    def glyphForName(self, glyphName):
        """\
        Returns the glyph with the given name.
        """
        glyphs = self._glyphs
        if glyphName in glyphs:
            return glyphs[glyphName]
        if glyphName not in self._ttGlyphSet:
            raise ValueError(f"Unknown glyph name: “{glyphName}”.")
        # glyph = GTGlyph(self, glyphName)
        glyph = Glyph(glyphName, self)
        glyphs[glyphName] = glyph
        return glyph


    def glyphForIndex(self, index):
        """\
        Returns the glyph with the given glyph index.
        """
        return self.glyphForName(self.glyphName(index))


    def glyphForCharacter(self, char):
        """\
        Returns the nominal glyph for the given Unicode character.
        """

        charCode = ord(char) if type(char) == type("") else char
        return self.glyphForName(self.glyphNameForCharacterCode(charCode))

    def unicodeForName(self, charName):
        for code, name in self._ttFont.getBestCmap().items():
            if name == charName:
                return code

        return None

    def hasCharacterCode(self, char):
        charCode = ord(char) if type(char) == type("") else char
        cmap = self._ttFont.getBestCmap()
        return char in cmap.keys()

    def hasGlyphName(self, glyphName):
        names = self.glyphNames()
        return glyphName in names

    def hasGlyphIndex(self, glyphIndex):
        names = self.glyphNames()
        return glyphIndex < len(names)
