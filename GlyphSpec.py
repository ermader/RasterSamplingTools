"""\
Process glyph specs like "/name", "uni04C0", "l" and "gid400"

Created on July 5, 2021

@author Eric Mader
"""

import re

nameRE = re.compile(r"/(.+)")
uniRE = re.compile(r"uni([0-9a-fA-F]{4,6})")
gidRE = re.compile(r"gid([0-9]{1,5})")

class GlyphSpec(object):
    name = 0
    charCode = 1
    glyphID = 2
    unknown = 3

    __slots__ = "_spec", "_type"

    @classmethod
    def specFromName(cls, name):
        return f"/{name}" if name else None

    @classmethod
    def specFromCharCode(cls, charCode):
        return f"uni{charCode:04X}" if charCode else None

    @classmethod
    def specFromGlyphID(cls, gid):
        return f"gid{gid}" if gid else None

    def __init__(self, glyphSpec):
        if len(glyphSpec) == 1:
            self._spec = ord(glyphSpec)
            self._type = GlyphSpec.charCode
            return

        m = nameRE.fullmatch(glyphSpec)
        if m:
            self._spec = m.group(1)
            self._type = GlyphSpec.name
            return

        m = uniRE.fullmatch(glyphSpec)
        if m:
            self._spec = int(m.group(1), base=16)
            self._type = GlyphSpec.charCode
            return

        m = gidRE.fullmatch(glyphSpec)
        if m:
            self._spec = int(m.group(1))
            self._type = GlyphSpec.glyphID
            return

        self._spec = ""
        self._type = GlyphSpec.unknown

    def __eq__(self, other):
        return self._spec == other._spec and self._type == other._type

    def __ne__(self, other):
        return self._type != other._type or self._spec != other._spec

    @property
    def spec(self):
        return self._spec

    @property
    def type(self):
        return self._type

    def nameForFont(self, font):
        if self._type == GlyphSpec.charCode:
            return font.glyphNameForCharacterCode(self._spec)

        if self._type == GlyphSpec.glyphID:
            names = font.glyphNames()
            return names[self._spec] if self._spec < len(names) else ""

        if self._type == GlyphSpec.name:
            names = font.glyphNames()
            return self._spec if self._spec in names else ""

        return None

    def glyphIDForFont(self, font):
        name = self.nameForFont(font)
        names = font.glyphNames()

        try:
            return names.index(name)
        except ValueError:
            return None

    def charCodeForFont(self, font):
        charName = self.nameForFont(font)
        cmap = font._ttFont.getBestCmap()

        for code, name in cmap.items():
            if name == charName:
                return code

        return None

    def nameSpecForFont(self, font):
        return self.specFromName(self.nameForFont(font))

    def glyphIDSpecForFont(self, font):
        return self.specFromGlyphID(self.glyphIDForFont(font))

    def charCodeSpecForFont(self, font):
        return self.specFromCharCode(self.charCodeForFont(font))