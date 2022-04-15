"""\
Raster Sampling Tests

Created on October 26, 2020

@author Eric Mader
"""

import typing

import os
from sys import argv, exit, stderr
import re
import math
import logging
import statistics
import numpy as np
import matplotlib

# import matplotlib.axis as maxis
import matplotlib.path as mpath
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import scipy.stats

# from scipy import odr
import statsmodels.api
from UnicodeData.CharNames import CharNames
from TestArguments.Font import Font
from PathLib.PathTypes import Point, Contour  # , Segment
from PathLib.Bezier import Bezier, BContour, BOutline

# from PathLib.BezierUtilities import lli
from PathLib import PathUtilities
from PathLib.Transform import Transform
from PathLib.SegmentPen import SegmentPen
from TestArguments.TestArguments import TestArgs
from TestArguments.CommandLineArguments import CommandLineOption

from RasterSamplingTools.OutputDatabase import OutputDatabase

_usage = """
Usage: rastersamplingtest options...

Options:
--font (fontFile.ttf | fontFile.otf | fontFile.ttc fontName | fontFile.otc fontName)
--glyph (char | /glyphName | uni<4-6 hex digits> | gid<1-5 decimal digits>)
[--widthMethod (leftmost | rightmost | leastspread)] (default: leftmost)
[--mainContour (largest | leftmost | rightmost | tallest)] (default: tallest)
[--range XX-YY] (default: 30-70)
[--direction (ltr | rtl)] (default: ltr)
[--outdb databaseFilePath]
[--loopDetection]
[--autoRangeOff]
[--colon]
[--debug]
"""

# Polynomial = np.polynomial.Polynomial

# Might belong in a utilities module...
def keyForValue(dict: dict[str, int], value: int) -> typing.Optional[str]:
    for k, v in dict.items():
        if v == value:
            return k
    return None


# distance from the point p to the line defined by x = my + k
def distanceFromPointToLine(p: Point, k: float, m: float) -> float:
    return abs(k + m * p[1] - p[0]) / math.sqrt(1 + m * m)


class RasterSamplingTestArgs(TestArgs):
    # __slots__ = "typoBounds", "glyphBounds", "widthMethod", "mainContourType", "loopDetection", "directionAdjust", "outdir", "outdb", "silent", "colon", "showFullName"

    widthMethodLeftmost = 0
    widthMethodRightmost = 1
    widthMethodLeastspread = 2
    boundsTypes = {
        "typographic": (True, False),
        "glyph": (False, True),
        "both": (True, True),
    }
    widthMethods = {
        "leftmost": widthMethodLeftmost,
        "rightmost": widthMethodRightmost,
        "leastspread": widthMethodLeastspread,
    }
    directions = {"ltr": 1, "rtl": -1}

    mainContourLargest = 0
    mainContourLeftmost = 1
    mainContourRightmost = 2
    mainContourTallest = 3
    mainContourTypes = {
        "largest": mainContourLargest,
        "leftmost": mainContourLeftmost,
        "rightmost": mainContourRightmost,
        "tallest": mainContourTallest,
    }

    options = [
        CommandLineOption(
            "widthMethod",
            lambda s, a: CommandLineOption.valueFromDict(
                s.widthMethods, a, "width method spec"
            ),
            lambda a: a.nextExtra("width method"),
            "widthMethod",
            "leftmost",
            required=False,
        ),
        CommandLineOption(
            "range",
            lambda s, a: s.processRange(a),
            lambda a: a.nextExtra("range"),
            "range",
            "30-70",
            required=False,
        ),
        CommandLineOption(
            "mainContour",
            lambda s, a: CommandLineOption.valueFromDict(
                s.mainContourTypes, a, "main contour type"
            ),
            lambda a: a.nextExtra("main contour type"),
            "mainContourType",
            "tallest",
            required=False,
        ),
        CommandLineOption(
            "direction",
            lambda s, a: CommandLineOption.valueFromDict(s.directions, a, "direction"),
            lambda a: a.nextExtra("direction"),
            "directionAdjust",
            "ltr",
            required=False,
        ),
        CommandLineOption(
            "outdb",
            lambda s, a: OutputDatabase(a) if a else None,
            lambda a: a.nextExtra("output db"),
            "outdb",
            None,
            required=False,
        ),
        CommandLineOption(
            "loopDetection", None, True, "loopDetection", False, required=False
        ),
        CommandLineOption("colon", None, True, "colon", False, required=False),
        CommandLineOption(
            "autoRangeOff", None, True, "autoRangeOff", False, required=False
        ),
    ]

    def __init__(self):
        self.outdir = ""
        self.silent = False
        self.showFullName = False

        self.widthMethod = self.widthMethodLeftmost
        self.range = (30, 70)
        self.mainContourType = self.mainContourTallest
        self.directionAdjust = 1
        self.outdb: typing.Optional[OutputDatabase] = None
        self.loopDetection = False
        self.colon = False
        self.autoRangeOff = False

        TestArgs.__init__(self)
        self._options.extend(RasterSamplingTestArgs.options)

    def processRange(self, rangeSpec: str) -> tuple[int, ...]:
        m = re.fullmatch("([0-9]{1,3})-([0-9]{1,3})", rangeSpec)
        if m:
            lowValue, highValue = rangeValues = tuple((int(s) for s in m.groups()))
            if lowValue < highValue <= 100:
                return rangeValues
            
        raise ValueError(f'Invalid range specification: "{rangeSpec}"')

    @property
    def widthMethodName(self):
        return keyForValue(self.widthMethods, self.widthMethod)

    @property
    def mainContourTypeName(self):
        return keyForValue(self.mainContourTypes, self.mainContourType)

    @property
    def directionName(self):
        return keyForValue(self.directions, self.directionAdjust)


oppositeDirection = {
    Bezier.dir_up: Bezier.dir_down,
    Bezier.dir_down: Bezier.dir_up,
    Bezier.dir_flat: Bezier.dir_flat,
    # Bezier.dir_mixed: Bezier.dir_mixed
}

widthSelection = {
    RasterSamplingTestArgs.widthMethodLeftmost: (True, False),
    RasterSamplingTestArgs.widthMethodRightmost: (False, True),
    RasterSamplingTestArgs.widthMethodLeastspread: (True, True),
}


def splitCurve(curve: Bezier, splits: list[Bezier]):
    p1, p2, p3 = curve.controlPoints
    q1 = p1
    r3 = p3
    q2 = PathUtilities.midpoint([p1, p2])
    r2 = PathUtilities.midpoint([p2, p3])
    q3 = r1 = PathUtilities.midpoint([q2, r2])
    q = Bezier([q1, q2, q3])
    r = Bezier([r1, r2, r3])

    if q.direction != Bezier.dir_mixed:
        splits.append(q)
    else:
        splitCurve(q, splits)

    if r.direction != Bezier.dir_mixed:
        splits.append(r)
    else:
        splitCurve(r, splits)


def diff(a: list[float]) -> list[float]:
    prev = a[0]
    return [-prev + (prev := x) for x in a[1:]]


def longestRange(r1: tuple[int, int], r2: tuple[int, int]) -> tuple[int, int]:
    l1 = r1[1] - r1[0]
    l2 = r2[1] - r2[0]
    return r1 if l1 > l2 else r2


lineWidth = 0.3
markerSize = 2.0


class RasterSamplingTest(object):
    # __slots__ = "_args", "_font", "logger", "outline"

    def __init__(self, args: RasterSamplingTestArgs):
        self._args = args
        self._font = Font(
            args.fontFile, fontName=args.fontName, fontNumber=args.fontNumber
        )

        logging.basicConfig(level=logging.DEBUG if args.debug else logging.WARNING)
        self.logger = logging.getLogger("raster-sampling-test")

    @classmethod
    def sortByP0(cls, list: list[Bezier]):
        if len(list) == 0:
            return
        list.sort(key=lambda b: b.startX)

    @classmethod
    def sortByArea(cls, contours: list[BContour], reverse: bool = False):
        contours.sort(key=lambda c: c.boundsRectangle.area, reverse=reverse)

    @classmethod
    def sortByHeight(cls, contours: list[BContour], reverse: bool = False):
        contours.sort(key=lambda c: c.boundsRectangle.height, reverse=reverse)

    @classmethod
    def sortByLeft(cls, contours: list[BContour], reverse: bool = False):
        contours.sort(key=lambda c: c.boundsRectangle.left, reverse=reverse)

    @classmethod
    def rasterLength(cls, raster: Bezier):
        return PathUtilities.length(raster.controlPoints)

    @classmethod
    def curvesAtY(cls, curveList: list[Bezier], y: float):
        return list(filter(lambda curve: curve.boundsRectangle.crossesY(y), curveList))

    @classmethod
    def leftmostPoint(cls, points: list[typing.Optional[Point]], outline: BOutline):
        leftmostX = 65536
        leftmostIndex = -1
        for index, point in enumerate(points):
            # if point is None, the curve is a line
            # that's colinear with the raster
            if point is not None:
                ipx, _ = outline.pointXY(point)
                if ipx < leftmostX:
                    leftmostX = ipx
                    leftmostIndex = index

        return leftmostIndex

    @classmethod
    def leftmostIntersection(
        cls,
        intersections: list[typing.Optional[Point]],
        curves: list[Bezier],
        direction: int,
    ) -> Point:
        leftmostX = 65536
        leftmostC = -1

        for index, curve in enumerate(curves):
            if cls.direction(curve) == direction:
                if ip := intersections[index]:
                    ipx, _ = curve.pointXY(ip)
                    if ipx < leftmostX:
                        leftmostX = ipx
                        leftmostC = index

        return typing.cast(Point, intersections[leftmostC])

    @classmethod
    def rightmostIntersection(
        cls,
        intersections: list[typing.Optional[Point]],
        curves: list[Bezier],
        direction: int,
    ) -> Point:
        rightmostX = -65536
        rightmostC = -1

        for index, curve in enumerate(curves):
            if cls.direction(curve) == direction:
                if ip := intersections[index]:
                    ipx, _ = curve.pointXY(ip)
                    if ipx > rightmostX:
                        rightmostX = ipx
                        rightmostC = index

        return typing.cast(Point, intersections[rightmostC])

    @classmethod
    def offsetPercent(cls, offset: float, outlineBounds: PathUtilities.BoundsRectangle):
        return round((offset - outlineBounds.bottom) / outlineBounds.height * 50)

    @classmethod
    def outlineToPath(cls, outline: BOutline) -> mpath.Path:
        Path = mpath.Path
        codeDict = {
            1: [Path.LINETO],
            2: [Path.CURVE3, Path.CURVE3],
            3: [Path.CURVE4, Path.CURVE4, Path.CURVE4],
        }

        codes: list[typing.Any] = []
        points: list[Point] = []
        pen = None

        for path in outline:
            for curve in path:
                start = curve.pointXY(curve.start)
                if start != pen:
                    points.append(start)
                    codes.append(Path.MOVETO)

                segment = curve.controlPoints
                order = len(segment) - 1
                points.extend([curve.pointXY(p) for p in segment[1:]])
                codes.extend(codeDict[order])

                pen = points[-1]

        return Path(points, codes)

    @classmethod
    def drawPathToAxis(
        cls,
        path: mpath.Path,
        outlineBounds: PathUtilities.BoundsRectangle,
        ax: plt.Axes,
    ):
        ax.set_aspect(1)
        patch = mpatches.PathPatch(path, fc="tab:gray", linewidth=lineWidth, alpha=0.10)
        ax.add_patch(patch)
        ax.plot(
            [outlineBounds.left, outlineBounds.right],
            [0, 0],
            "c--",
            linewidth=lineWidth,
        )
        ax.plot(
            [
                outlineBounds.left,
                outlineBounds.left,
                outlineBounds.right,
                outlineBounds.right,
                outlineBounds.left,
            ],
            [
                outlineBounds.bottom,
                outlineBounds.top,
                outlineBounds.top,
                outlineBounds.bottom,
                outlineBounds.bottom,
            ],
            "m--",
            linewidth=lineWidth,
        )

    @classmethod
    def rangeFallback(
        cls,
        range: tuple[int, int],
        outlineBounds: PathUtilities.BoundsRectangle,
        innerBounds: typing.Optional[PathUtilities.BoundsRectangle],
    ):
        if innerBounds:
            start = cls.offsetPercent(innerBounds.bottom, outlineBounds)
            end = cls.offsetPercent(innerBounds.top, outlineBounds)
        else:
            start = range[0] // 2
            end = range[1] // 2

        return start, end

    def autoRange(self, rasters: list[Bezier], outline: BOutline):
        w = [round(self.rasterLength(r), 2) for r in rasters]
        w1 = diff(w)
        w2 = diff(w1)

        currentRange = (-1, -1)
        bestRange = (-1, -1)

        if not self._args.autoRangeOff:
            for i, v in enumerate(w2):
                if abs(v) < 5.0:
                    if currentRange[0] >= 0:
                        currentRange = currentRange[0], i
                    else:
                        currentRange = i, currentRange[1]
                else:
                    bestRange = longestRange(bestRange, currentRange)
                    currentRange = (-1, -1)

        bestRange = longestRange(bestRange, currentRange)
        return w, w1, w2, bestRange

    @classmethod
    def midpoints(cls, rasters: list[Bezier]):
        return [r.midpoint for r in rasters]

    @classmethod
    def bestFit(
        cls, midpoints: list[Point], outline: BOutline
    ) -> tuple[float, float, float, float, float]:
        # linregress(midpoints) can generate warnings if the best fit line is
        # vertical. So we swap x, y and do the best fit that way.
        # (which of course, will generate warnings if the best fit line is horizontal)
        xs, ys = outline.unzipPoints(midpoints)
        b, a, rValue, pValue, stdErr = scipy.stats.linregress(ys, xs)

        return b, a, rValue, pValue, stdErr

    @classmethod
    def direction(cls, curve: Bezier) -> int:
        startY = curve.startY
        endY = curve.endY

        # minY = min(startY, endY)
        # maxY = max(startY, endY)

        #
        # For the purposes of edge detection
        # we don't care if the curve actually
        # has a mixed direction, only that it
        # tends upward or downward.
        #
        # ocps = curve.controlPoints[1:-1]
        # for ocp in ocps:
        #     ocpx, ocpy = curve.pointXY(ocp)
        #     if ocpy < minY or ocpy > maxY: return Bezier.dir_mixed

        # if we get here, the curve is either order 1 or
        # has a uniform direction. Curves with order 2 or higher
        # with startY and endY equal are likely mixed and got caught
        # above.
        if startY < endY:
            return Bezier.dir_up
        if startY > endY:
            return Bezier.dir_down
        return Bezier.dir_flat

    def scaleContours(self, contours: list[Contour]):
        upem = self._font.unitsPerEm()
        if upem != 1000:
            scaleFactor = 1000 / upem
            scaleTransform = Transform.scale(scaleFactor, scaleFactor)
            return scaleTransform.applyToContours(contours)

        return contours

    # def medianLines(self, line, median):
    #     startX, startY = line.pointXY(line.start)
    #     endX, endY = line.pointXY(line.end)
    #     m2 = median / 2

    #     p1 = line.xyPoint(startX - m2, startY)
    #     p2 = line.xyPoint(endX - m2, endY)
    #     leftLine = self.outline.segmentFromPoints([p1, p2])

    #     p1 = line.xyPoint(startX + m2, startY)
    #     p2 = line.xyPoint(endX + m2, endY)
    #     rightLine = self.outline.segmentFromPoints([p1, p2])

    #     return leftLine, rightLine

    @property
    def postscriptName(self):
        return self._font.postscriptName

    @property
    def font(self):
        return self._font

    def outlineFromGlyph(self, glyphName: str) -> BOutline:
        pen = SegmentPen(self.font.glyphSet, self.logger)
        self.font.glyphSet[glyphName].draw(pen)
        return BOutline(self.scaleContours(pen.contours))

    def outlineFromChar(
        self, char: typing.Union[str, int]
    ) -> typing.Optional[BOutline]:
        charCode = ord(char) if isinstance(char, str) else char
        charName = self.font.glyphNameForCharacterCode(charCode)
        return self.outlineFromGlyph(charName) if charName else None

    def italicAngleFromColonMethod(self):
        outline = self.outlineFromChar(":")

        # We accept more than two contours if the two largest enclose all the others...
        if outline and len(outline.contours) >= 2:
            contours = outline.contours.copy()
            self.sortByArea(contours, reverse=True)

            b0 = contours[0].boundsRectangle
            b1 = contours[1].boundsRectangle

            # make sure any other contours are enclosed by one of the two biggest
            # for c in contours[2:]:
            #     b = c.boundsRectangle
            #     if not (b0.encloses(b) or b1.encloses(b)):
            #         return None

            # We assume that the two largest contours are the dots
            p0 = b0.centerPoint
            p1 = b1.centerPoint

            angle = round(PathUtilities.slopeAngle([p0, p1]), 1)

            return angle

        return None

    def run(self):
        widthMethodStrings = {
            RasterSamplingTestArgs.widthMethodLeftmost: "",
            RasterSamplingTestArgs.widthMethodRightmost: "_rightmost",
            RasterSamplingTestArgs.widthMethodLeastspread: "_leastspread",
        }

        args = self._args
        font = self._font
        indent = ""
        fullName = font.fullName
        if fullName.startswith("."):
            fullName = fullName[1:]

        matplotlib.set_loglevel("warning")
        matplotlib.use("svg")

        glyph = args.getGlyph(font)
        glyphName = glyph.name()
        gidSpec = args.glyphSpec.glyphIDSpecForFont(font)
        charCode = args.glyphSpec.charCodeForFont(font)

        if charCode:
            unicodeName = CharNames.getCharName(charCode)

            charInfo = f"U+{charCode:04X} {unicodeName if unicodeName else '(no Unicode name)'}"
        else:
            unicodeName = ""
            charInfo = f"{gidSpec} {glyphName}"

        fontEntry: OutputDatabase.FontEntry = (
            {}
        )  # this is here to make any incorrect "possibly unbound" errors go away
        testResults: OutputDatabase.TestResults = {}  # this too...
        glyphNameSpec: typing.Optional[str] = None  # and this...
        if args.outdb:
            fontEntry = args.outdb.getEntry(font)
            testResults = args.outdb.getTestResults(fontEntry)
            glyphNameSpec = args.glyphSpec.nameSpecForFont(font)

        if args.silent:
            indent = "        "

            if args.showFullName:
                print(f"    {font.fullName}:")

        if args.colon:
            colonAngle = self.italicAngleFromColonMethod()
            print(f"{indent}italic angle from colon method = {colonAngle}\u00B0")
            if args.outdb:
                fontEntry["italic_angle_from_colon_method"] = colonAngle

        if args.silent:
            print(f"{indent}{charInfo}:")

        widthMethodString = widthMethodStrings[args.widthMethod]
        loopDetectionString = "_loop" if args.loopDetection else ""
        svgName = os.path.join(
            args.outdir,
            f"RasterSamplingTest {fullName}{widthMethodString}{loopDetectionString}_{gidSpec}({glyphName}).svg",
        )

        outline = self.outlineFromGlyph(glyphName)

        self.outline = outline
        path = self.outlineToPath(outline)

        contourCount = len(outline.contours)
        if contourCount > 3:
            print(
                f"{indent}(this glyph has {contourCount} contours, so results may not be useful)"
            )

        glyphResults: dict[
            str,
            typing.Optional[typing.Union[str, int, float, list[int], dict[str, float]]],
        ] = {}  # this is here to make bogus "possibly unbound" errors go away
        if args.outdb:
            glyphName = args.glyphSpec.nameForFont(font)
            codePoints = font.codePointsForGlyphName(glyphName)

            segmentCounts: list[int] = []
            for contour in outline.contours:
                segmentCounts.append(len(contour.beziers))

            glyphResults = {
                "code_points": codePoints,
                "unicode_character_name": unicodeName if unicodeName else "",
                "glyph_id": args.glyphSpec.glyphIDForFont(font),
                "contour_count": contourCount,
                "segment_counts": segmentCounts,
                "width_method": args.widthMethodName,
                "main_contour": args.mainContourTypeName,
                "direction": args.directionName,
            }

        outlineBounds = outline.boundsRectangle
        # outlineBoundsLeft = outlineBounds.left if outlineBounds.left >= 0 else 0
        # outlineBoundsCenter = outlineBoundsLeft + outlineBounds.width / 2

        baseline = [(min(0, outlineBounds.left), 0), (outlineBounds.right, 0)]
        baselineBounds = PathUtilities.BoundsRectangle(*baseline)

        overallBounds = baselineBounds.union(outlineBounds)

        contours = outline.contours.copy()
        if args.mainContourType == RasterSamplingTestArgs.mainContourLargest:
            self.sortByArea(contours, reverse=True)
        elif args.mainContourType == RasterSamplingTestArgs.mainContourTallest:
            self.sortByHeight(contours, reverse=True)
        elif args.mainContourType == RasterSamplingTestArgs.mainContourLeftmost:
            self.sortByLeft(contours, reverse=False)
        else:
            self.sortByLeft(contours, reverse=True)

        mainContour = contours[0]
        mainBounds = mainContour.boundsRectangle

        # Make sure contour with the largest bounding rectangle has
        # an area that is at least 10% of the area of the bounding rectangle
        # of the whole glyph
        outerAreaPercent = round(mainBounds.area / outlineBounds.area * 100.0, 3)
        outerHeightPercent = round(mainBounds.height / outlineBounds.height * 100.0, 3)

        if args.outdb:
            glyphResults["main_contour_area_percent"] = outerAreaPercent
            glyphResults["main_contour_height_percent"] = outerHeightPercent

        if outerAreaPercent < 10.0 or outerHeightPercent < 50.0:
            print(
                f"{indent}The largest contour has an area that is only {outerAreaPercent}% of the total."
            )
            print(
                f"{indent}The tallest contour has an height that is only {outerHeightPercent}% of the total."
            )
            if args.silent:
                print()

            if args.outdb:
                if glyphNameSpec:
                    testResults[glyphNameSpec] = glyphResults
                args.outdb.close()

            fig, ax = plt.subplots()
            outlineCenter = outlineBounds.left + outlineBounds.width / 2
            self.drawPathToAxis(path, outlineBounds, ax)
            ax.text( # type: ignore
                outlineCenter,
                outlineBounds.top + 10,
                f"{fullName}\n{charInfo}",
                va="bottom",
                ha="center",
            )
            ax.text( # type: ignore
                outlineCenter,
                outlineBounds.bottom - 10,
                f"No main contour\nLargest area is {outerAreaPercent}% of the total\nTallest height is {outerHeightPercent}% of the total",
                va="top",
                ha="center",
            )
            ax.set_axis_off()
            plt.savefig(svgName)
            plt.close(fig)
            return

        curveList = [curve for curve in mainContour]
        innerContours: list[BContour] = []
        for contour in contours[1:]:
            contourBounds = contour.boundsRectangle

            if (
                mainBounds.encloses(contourBounds)
                and contourBounds.area / mainBounds.area >= 0.05
            ):
                innerContours.append(contour)
                for curve in contour:
                    curveList.append(curve)

        doLeft, doRight = widthSelection[args.widthMethod]

        rastersLeft: list[Bezier] = []
        rastersRight: list[Bezier] = []
        missedRasterCount = 0
        height = outlineBounds.height
        lowerBound = round(outlineBounds.bottom)
        upperBound = round(outlineBounds.bottom + height)

        # if args.loopDetection and len(innerContours) == 1:
        #     innerBounds = innerContours[0].boundsRectangle
        #     if innerBounds.top >= outlineBounds.top * .70:
        #         # height = innerBounds.height
        #         lowerBound = round(innerBounds.bottom)
        #         upperBound = round(innerBounds.top)

        interval = round(height * 0.02)

        left, _, right, _ = overallBounds.points
        for y in range(lowerBound, upperBound, interval):
            p1 = outline.xyPoint(left, y)
            p2 = outline.xyPoint(right, y)
            raster = outline.segmentFromPoints([p1, p2])

            curvesAtY = self.curvesAtY(curveList, y)
            if len(curvesAtY) == 0:
                missedRasterCount += 1
                continue

            intersections: list[typing.Optional[Point]] = [
                c.intersectWithLine(raster) for c in curvesAtY
            ]

            leftmostCurve = self.leftmostPoint(intersections, outline)
            p1 = typing.cast(Point, intersections[leftmostCurve])
            direction = oppositeDirection[self.direction(curvesAtY[leftmostCurve])]

            # missedLeft = missedRight = False

            if doLeft:
                p2 = self.leftmostIntersection(intersections, curvesAtY, direction)

                if p1 != p2:
                    rastersLeft.append(outline.segmentFromPoints([p1, p2]))
                # else:
                #     missedLeft = True

            if doRight:
                p2 = self.rightmostIntersection(intersections, curvesAtY, direction)

                if p1 != p2:
                    rastersRight.append(outline.segmentFromPoints([p1, p2]))
                # else:
                #     missedRight = True

        innerBounds = None
        if (
            args.loopDetection
            and len(innerContours) == 1
            and innerContours[0].boundsRectangle.top >= outlineBounds.top * 0.70
        ):
            innerBounds = innerContours[0].boundsRectangle

        # topLeft = (outlineBounds.left, outlineBounds.top)
        # topRight = (outlineBounds.right, outlineBounds.top)
        # bottomLeft = (outlineBounds.left, outlineBounds.bottom)
        # bottomRight = (outlineBounds.right, outlineBounds.bottom)
        # aboutPoint = bottomLeft

        wl: list[float] = []
        wl1: list[float] = []
        wl2: list[float] = []
        widthsL: list[float] = []
        rl: tuple[int, int] = (0, 0)

        wr: list[float] = []
        wr1: list[float] = []
        wr2: list[float] = []
        widthsR: list[float] = []
        rr: tuple[int, int] = (0, 0)

        if doLeft:
            wl, wl1, wl2, rl = self.autoRange(rastersLeft, outline)
            if rl[0] >= 0 and rl[1] - rl[0] >= 5:
                start = rl[0]
                limit = rl[1] + 1
            else:
                start, limit = self.rangeFallback(
                    args.range, outlineBounds, innerBounds
                )

            rastersLeft = rastersLeft[start:limit]
            widthsL = wl[start:limit]

        if doRight:
            wr, wr1, wr2, rr = self.autoRange(rastersRight, outline)
            if rr[0] >= 0 and rr[1] - rr[0] >= 5:
                start = rr[0]
                limit = rr[1] + 1
            else:
                start, limit = self.rangeFallback(
                    args.range, outlineBounds, innerBounds
                )

            rastersRight = rastersRight[start:limit]
            widthsR = wr[start:limit]

        if doLeft and doRight:
            midpointsL = self.midpoints(rastersLeft)
            bL, aL, rValueL, pValueL, stdErrL = self.bestFit(midpointsL, outline)

            midpointsR = self.midpoints(rastersRight)
            bR, aR, rValueR, pValueR, stdErrR = self.bestFit(midpointsR, outline)

            if round(stdErrL, 2) <= round(stdErrR, 2):
                rasters = rastersLeft
                chosenWidthMethod = "Left"
                widths, midpoints, b, a, rValue, pValue, stdErr = (
                    widthsL,
                    midpointsL,
                    bL,
                    aL,
                    rValueL,
                    pValueL,
                    stdErrL,
                )
                w, w1, w2, bestRange = wl, wl1, wl2, rl
            else:
                rasters = rastersRight
                chosenWidthMethod = "Right"
                widths, midpoints, b, a, rValue, pValue, stdErr = (
                    widthsR,
                    midpointsR,
                    bR,
                    aR,
                    rValueR,
                    pValueR,
                    stdErrR,
                )
                w, w1, w2, bestRange = wr, wr1, wr2, rr
        else:
            if doLeft:
                rasters = rastersLeft
                chosenWidthMethod = "Left"
                widths, w, w1, w2, bestRange = widthsL, wl, wl1, wl2, rl
            else:
                rasters = rastersRight
                chosenWidthMethod = "Right"
                widths, w, w1, w2, bestRange = widthsR, wr, wr1, wr2, rr

            midpoints = self.midpoints(rasters)
            b, a, rValue, pValue, stdErr = self.bestFit(midpoints, outline)

        my0 = outlineBounds.bottom
        myn = outlineBounds.top

        # x = by + a
        mx0 = b * my0 + a
        mxn = b * myn + a

        orthogonalDistances = [distanceFromPointToLine(p, a, b) for p in midpoints]
        meanOrthogonalDistance = statistics.mean(orthogonalDistances)
        lmod = math.log1p(meanOrthogonalDistance)

        if missedRasterCount > 0:
            print(f"{indent}{missedRasterCount} rasters did not intersect the glyph.")

        print(
            f"{indent}{chosenWidthMethod}: a = {round(a, 2)}, b = {round(b, 4)}, r_value = {round(rValue, 4)}, p_value = {round(pValue, 2)}, lmod = {round(lmod, 4)}"
        )

        strokeAngle = (
            round(math.degrees(math.atan2(mxn - mx0, myn - my0)), 1)
            * args.directionAdjust
        )

        if args.outdb:
            glyphResults["chosen_width_method"] = chosenWidthMethod.lower()
            glyphResults[
                "raster_sample_range"
            ] = f"{bestRange[0] * 2}-{bestRange[1] * 2}"
            glyphResults["fit_results"] = {
                "slope": round(b, 4),
                "intercept": round(a, 2),
                "r_value": round(rValue, 4),
                "p_value": round(pValue, 4),
                "std_err": round(stdErr, 4),
                "log_mean_orthogonal_distance": round(lmod, 4),
                "stroke_angle": strokeAngle,
            }

        avgWidth = round(statistics.mean(widths), 2)
        quartiles = statistics.quantiles(widths, n=4, method="inclusive")
        q1 = round(quartiles[0], 2)
        median = round(quartiles[1], 2)
        q3 = round(quartiles[2], 2)
        minWidth = round(min(widths), 2)
        maxWidth = round(max(widths), 2)

        print(f"{indent}angle = {strokeAngle}\u00B0")

        widthDict = {
            "min": minWidth,
            "q1": q1,
            "median": median,
            "mean": avgWidth,
            "q3": q3,
            "max": maxWidth,
        }
        widthsString = ", ".join([f"{k} = {v}" for k, v in widthDict.items()])
        print(f"{indent}Widths: {widthsString}")
        if args.silent:
            print()

        if args.outdb:
            glyphResults["widths"] = widthDict
            if glyphNameSpec:
                testResults[glyphNameSpec] = glyphResults

            if not args.silent:
                args.outdb.close()

        matplotlib.rcParams["axes.linewidth"] = lineWidth

        figWidth, figHeight = matplotlib.rcParams["figure.figsize"]
        figSize = (figWidth * 1.5, figHeight * 1.5)

        fig = plt.figure(figsize=figSize, constrained_layout=True)
        gs = GridSpec(5, 2, figure=fig, height_ratios=[5, 35, 10, 35, 15]) # type: ignore
        fig.suptitle(f"{fullName}\n{charInfo}")

        ax1 = fig.add_subplot(gs[:, 0])
        self.drawPathToAxis(path, outlineBounds, ax1)

        for r in rasters:
            y = r.startY
            xs = r.startX
            xe = r.endX
            ax1.plot([left, right], [y, y], "r-", linewidth=lineWidth)
            ax1.plot([xs, xs, xe, xe], [y, y, y, y], "bo", markersize=markerSize)

        x, y = zip(*midpoints)
        ax1.plot(x, y, "go", markersize=markerSize)

        ax1.plot([mx0, mxn], [my0, myn], "g-", linewidth=lineWidth, alpha=0.75)

        ax1.set_title(
            f"Stroke angle = {strokeAngle}\u00B0\n{chosenWidthMethod} best fit lmod = {round(lmod, 4)}"
        )

        m2 = median / 2
        ax1.plot(
            [mx0 - m2, mxn - m2],
            [my0, myn],
            c="tab:orange",
            ls="-",
            linewidth=lineWidth,
            alpha=0.75,
        )
        ax1.plot(
            [mx0 + m2, mxn + m2],
            [my0, myn],
            c="tab:orange",
            ls="-",
            linewidth=lineWidth,
            alpha=0.75,
        )
        ax1.set_axis_off()

        ax2 = fig.add_subplot(gs[0, 1])
        ax3 = fig.add_subplot(gs[1, 1])
        ax4 = fig.add_subplot(gs[2, 1])
        ax3.tick_params(labelbottom=False)
        ax4.sharex(ax3)
        # ax2.set_title(f"Stroke Widths of {font.fullName}_{glyphName}")
        ax2.set_axis_off()

        collLabels: list[str] = []
        cellText: list[list[str]] = [[]]
        for l, v in widthDict.items():
            collLabels.append(l.capitalize())
            cellText[0].append(f"{v}")
        tab = ax2.table(
            cellText=cellText,
            cellLoc="center",
            colLabels=collLabels,
            loc="upper center",
            edges="closed",
        )

        for _, cell in tab.get_celld().items():
            cell.set_linewidth(lineWidth)

        n, bins, _ = ax3.hist(
            widths, bins=12, align="mid", density=True, alpha=0.8, linewidth=lineWidth
        )

        # add a 'best fit' line
        mu = statistics.mean(widths)
        sigma = statistics.stdev(widths)
        if sigma == 0.0:
            sigma = 1.0  # hack: if all widths are the same, sigma == 0...
        y = (1 / (np.sqrt(2 * np.pi) * sigma)) * np.exp(
            -0.5 * (1 / sigma * (bins - mu)) ** 2
        )

        widths.sort()

        dens = statsmodels.api.nonparametric.KDEUnivariate(widths)
        dens.fit(bw=0.9)
        densVals = dens.evaluate(widths)

        ax3.plot(bins, y, "m--", widths, densVals, "r--")
        ax3.vlines(
            [avgWidth, median],
            0,
            max(max(n), densVals.max()),
            colors=["tab:green", "tab:orange"],
        )
        # ax3.set_ylabel('Probability density')

        # ax4.set_xlabel('Width')
        ax4.boxplot(
            widths,
            vert=False,
            showmeans=True,
            meanline=True,
            flierprops={"markerfacecolor": "r"},
        )
        ax4.tick_params(labelleft=False)

        ax5 = fig.add_subplot(gs[3, 1])
        ax6 = fig.add_subplot(gs[4, -1])
        ax5.tick_params(labelbottom=False)
        ax6.sharex(ax5)

        x = [n for n in range(len(w))]
        ax5.bar(x, w, alpha=0.8)

        ax6.plot(x[: len(w1)], w1, "r", label="1st")
        ax6.plot(x[: len(w2)], w2, "g", label="2nd")
        miny = ax6.viewLim.ymin
        maxy = ax6.viewLim.ymax

        if bestRange[0] >= 0:
            backgroundColor = "#ffffff80"
            ax5.vlines(bestRange, 0, max(w), ["m", "m"])
            ax6.vlines(bestRange, miny, maxy, ["m", "m"])
            ax5.annotate(
                f"{bestRange[0]}",
                xy=(bestRange[0], max(w)),
                xytext=(-2, 0),
                textcoords="offset points",
                horizontalalignment="right",
                verticalalignment="top",
                backgroundcolor=backgroundColor,
            )
            ax5.annotate(
                f"{bestRange[1]}",
                xy=(bestRange[1], max(w)),
                xytext=(2, 0),
                textcoords="offset points",
                horizontalalignment="left",
                verticalalignment="top",
                backgroundcolor=backgroundColor,
            )

        # ax6.legend()

        plt.savefig(svgName)
        plt.close(fig)


def main():
    argumentList = argv
    args = None
    programName = os.path.basename(argumentList.pop(0))
    if len(argumentList) == 0:
        print(_usage, file=stderr)
        exit(1)
    try:
        args = RasterSamplingTestArgs()
        args.processArguments(argumentList)
    except ValueError as error:
        print(programName + ": " + str(error), file=stderr)
        exit(1)

    test = RasterSamplingTest(args)
    test.run()


if __name__ == "__main__":
    main()
