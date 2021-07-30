"""\
Text Utilities.

Created on October 30, 2020

Much of this code based on code in GlyphShaper.py from FontDocTools

@author Eric Mader
"""

from sys import stderr

try:
    # macOS APIs via PyObjC
    import CoreText
    import CoreFoundation
    import Foundation
except ImportError:
    print("This tool currently only runs on macOS with PyObjC installed.", file=stderr)
    exit(1)

def _drawableString(text, ctFont):
    """\
    Creates an AttributedString with the given text and font.
    """

    # pylint: disable=no-self-use
    # pylint: disable=no-member; pylint can’t see imports from PyObjC modules.

    attrString = CoreFoundation.CFAttributedStringCreateMutable(CoreFoundation.kCFAllocatorDefault, 0)
    length = CoreFoundation.CFStringGetLength(text)
    CoreFoundation.CFAttributedStringReplaceString(attrString, CoreFoundation.CFRangeMake(0, 0), text)
    CoreFoundation.CFAttributedStringSetAttribute(attrString, CoreFoundation.CFRangeMake(0, length), CoreText.kCTFontAttributeName, ctFont)
    return attrString

def ctFont(fontName, fontSize):
    """\
    Returns the CoreText font instance for the specified font.
    """

    # pylint: disable=no-member; pylint can’t see imports from PyObjC modules.

    return CoreText.CTFontCreateWithName(fontName, fontSize, None)

def stringWidth(string, ctFont):
    """\
    Returns the width of the given string
    rendered in the given CoreText font.
    """

    # pylint: disable=no-member; pylint can’t see imports from PyObjC modules.

    drawable = _drawableString(string, ctFont)
    line = CoreText.CTLineCreateWithAttributedString(drawable)

    # The PyObjC adaptation of CTLineGetTypographicBounds returns a tuple (width, ascender, descender, linegap).
    (width, _, _, _) = CoreText.CTLineGetTypographicBounds(line, None, None, None)

    return width

