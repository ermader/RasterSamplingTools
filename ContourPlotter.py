"""\
Plot a contour

Created June 23, 2020

@author = Eric Mader
"""

from FontDocTools import GlyphPlotterEngine
from svgpathtools import Path
from PathUtilities import PUColor

# Add methods for drawing lines, circles, titles w/o needing to know about contexts?
class ContourPlotter(GlyphPlotterEngine.GlyphPlotterEngine):
    lastCommand = ""

    def __init__(self, bounds, poly=False):
        GlyphPlotterEngine.GlyphPlotterEngine.__init__(self)
        self._boundsAggregator.addBounds(bounds)
        left, bottom, right, top = bounds
        width = right - left
        height = top - bottom
        self.setContentMargins(GlyphPlotterEngine.Margins(width // 20, height // 20, width // 20, height // 20))
        self.setFrameMargins(GlyphPlotterEngine.Margins(10, 10, 10, 10))
        fs = self._contentMargins.top / 2
        self.setLabelFontSize(fs, fs)
        self._poly = poly
        self._lastCommand = ""
        self._fillAttributeStack = []
        self._strokeAttributeStack = []

    @property
    def labelFontSize(self):
        return self._labelFontSize

    @property
    def labelFont(self):
        return self._labelFont

    def pushFillAttributes(self, color=None, opacity=None):
        self._fillAttributeStack.append((self._fillColor, self._fillOpacity))
        if color: self.setFillColor(color)
        if opacity: self.setFillOpacity(opacity)

    def popFillAttributes(self):
        color, opacity = self._fillAttributeStack.pop()
        self.setFillColor(color)
        self.setFillOpacity(opacity)

    def pushStrokeAttributes(self, width=None, color=None, opacity=None, dash=None):
        self._strokeAttributeStack.append((self._strokeWidth, self._strokeColor, self._strokeOpacity, self._strokeDash))
        if width: self.setStrokeWidth(width)
        if color: self.setStrokeColor(color)
        if opacity: self.setStrokeOpacity(opacity)
        if dash: self.setStrokeDash(dash)

    def popStrokeAtributes(self):
        width ,color, opacity, dash = self._strokeAttributeStack.pop()
        self.setStrokeWidth(width)
        self.setStrokeColor(color)
        self.setStrokeOpacity(opacity)
        self.setStrokeDash(dash)

    def pointToString(self, point):
        return ",".join([str(i) for i in point])

    def getCommand(self, command):
        if self._poly:
            if self._lastCommand != command:
                self._lastCommand = command
            else:
                command = " "

        return command

    def drawContours(self, contours, color=None, fill=False, close=True):
        if fill:
            self.pushFillAttributes(color=color, fill=fill)
        elif color:
            self.pushStrokeAttributes(color=color)
            # self._strokeWidth = 2

        path = "<path d='"
        commands = []
        for contour in contours:
                firstPoint = contour[0][0]
                self.moveToXY(*firstPoint)
                commands.append(f"M{self.pointToString(firstPoint)}")

                for segment in contour:
                    if len(segment) == 2:
                        # a line
                        penX, penY = self._pen
                        x, y = segment[1]

                        if penX == x and penY == y:
                            continue
                        elif penX == x:
                            # vertical line
                            command = self.getCommand("V")
                            commands.append(f"{command}{y}")
                        elif penY == y:
                            # horizontal line
                            command = self.getCommand("H")
                            commands.append(f"{command}{x}")
                        else:
                            point = self.pointToString(segment[1])
                            command = self.getCommand("L")
                            commands.append(f"L{point}")
                        self._pen = (x, y)
                    elif len(segment) == 3:
                            p1 = self.pointToString(segment[1])
                            p2 = self.pointToString(segment[2])
                            command = self.getCommand("Q")
                            commands.append(f"{command}{p1} {p2}")
                            self._pen = segment[2]
                    elif len(segment) == 4:
                        p1 = self.pointToString(segment[1])
                        p2 = self.pointToString(segment[2])
                        p3 = self.pointToString(segment[3])
                        command = self.getCommand("C")
                        commands.append(f"{command}{p1} {p2} {p3}")
                        self._pen = segment[3]

                if close: commands.append("Z")

        path += "".join(commands)

        if fill:
            path += f"' {self._fillAttributes()}/>"
            self.popFillAttributes()
        else:
            path += f"' fill='none' {self._strokeAttributes()}/>"
            if color: self.popStrokeAtributes()

        self._content.append(path)

    def drawPaths(self, paths, color=None, fill=False, close=True):
        if fill:
            self.pushFillAttributes(color=color, fill=fill)
            attributes = self._fillAttributes()
        else:
            if color:
                self.pushStrokeAttributes(color=color)
            # self._strokeWidth = 2
            attributes = f"fill='none' {self._strokeAttributes()}"

        for path in paths:
            commands = []
            pointToString = lambda p: self.pointToString(path.pointXY(p))

            firstPoint = path.start
            self.moveToXY(*path.pointXY(firstPoint))
            commands.append(f"M{pointToString(firstPoint)}")

            for curve in path:
                segment = curve.controlPoints
                if len(segment) == 2:
                    # a line
                    penX, penY = self._pen
                    x, y = path.pointXY(segment[1])

                    if penX == x and penY == y:
                        continue
                    elif penX == x:
                        # vertical line
                        command = self.getCommand("V")
                        commands.append(f"{command}{y}")
                    elif penY == y:
                        # horizontal line
                        command = self.getCommand("H")
                        commands.append(f"{command}{x}")
                    else:
                        point = pointToString(segment[1])
                        command = self.getCommand("L")
                        commands.append(f"{command}{point}")
                    self._pen = (x, y)
                elif len(segment) == 3:
                    p1 = pointToString(segment[1])
                    p2 = pointToString(segment[2])
                    command = self.getCommand("Q")
                    commands.append(f"{command}{p1} {p2}")
                    self._pen = path.pointXY(segment[2])
                elif len(segment) == 4:
                    p1 = pointToString(segment[1])
                    p2 = pointToString(segment[2])
                    p3 = pointToString(segment[3])
                    command = self.getCommand("C")
                    commands.append(f"{command}{p1} {p2} {p3}")
                    self._pen = path.pointXY(segment[3])

            # if use_closed_attrib: commands.append("Z")

            path = "".join(commands)
            self._content.append(f"<path d='{path}' {attributes}/>")

        if fill:
            self.popFillAttributes()
        elif color:
            self.popStrokeAtributes()


    def drawPointsAsSegments(self, points, color=None):
        if color: self.pushStrokeAttributes(color=color)  # used to set stroke width to 2...

        path = "<path d='"
        commands = []
        firstPoint = points[0]
        self.moveToXY(*firstPoint)
        commands.append(f"M{self.pointToString(firstPoint)}")
        command = "L"

        for point in points[1:]:
            x, y = point
            penX, penY = self._pen

            if penX == x and penY == y:
                continue

            commands.append(f"{command}{self.pointToString(point)}")
            self._pen = (x, y)
            command = " "

        path += "".join(commands)

        path += f"' fill='none' {self._strokeAttributes()}/>"
        self._content.append(path)
        if color: self.popStrokeAtributes()

    def drawPointsAsCircles(self, points, radius, colors=None, fill=True):
        if isinstance(points[0], complex):
            getXY = lambda p: (p.real, p.imag)
        else:
            getXY = lambda p: p

        if colors:
            if fill:
                self._fillColor = colors[0]
            else:
                self.pushStrokeAttributes(color=colors[0])

        paintMode = GlyphPlotterEngine.PaintMode.fill if fill else GlyphPlotterEngine.PaintMode.stroke

        i = 0
        for point in points:
            x, y = getXY(point)
            color = colors[i % len(colors)] if colors else None
            i += 1
            if fill:
                if color: self.setFillColor(color)
            else:
                if color: self.setStrokeColor(color)
            self.drawCircle(GlyphPlotterEngine.CoordinateSystem.content, x, y, radius, paintMode)

        if colors and not fill: self.popStrokeAtributes()

    def drawComplexPointsAsCircles(self, points, radius, colors=None, fill=True):
        if colors:
            if fill:
                self._fillColor = colors[0]
            else:
                self.pushStrokeAttributes(color=colors[0])

        paintMode = GlyphPlotterEngine.PaintMode.fill if fill else GlyphPlotterEngine.PaintMode.stroke

        i = 0
        for point in points:
            color = colors[i % len(colors)] if colors else None
            i += 1
            if fill:
                if color: self.setFillColor(color)
            else:
                if color: self.setStrokeColor(color)
            self.drawCircle(GlyphPlotterEngine.CoordinateSystem.content, point.real, point.imag, radius, paintMode)

        if colors and not fill: self.popStrokeAtributes()

    def drawCurve(self, segment, color=None):
        self.drawContours([[segment]], color=color, fill=False, close=False)

    def drawText(self, x, y, alignment, text, margin=True):
        coordinates = GlyphPlotterEngine.CoordinateSystem.contentMargins if margin else GlyphPlotterEngine.CoordinateSystem.content
        self.drawLabel(coordinates, x, y, 0, alignment, text)

    colorLightGrey = PUColor.fromName("lightgrey")
    colorBlack = PUColor.fromName("black")

    def drawSkeleton(self, curve, lineColor=colorLightGrey, pointColors=[colorBlack]):
        points = curve.controlPoints
        self._strokWidth = 1
        self.drawPointsAsSegments(points, lineColor)
        self.drawPointsAsCircles(points, 2, pointColors, fill=True)

        self.pushFillAttributes(color=self.colorBlack)
        self.setLabelFontSize(6, 6)
        for point in points:
            x, y = point
            self.drawText(x + 4, y - 4, "left", f"({round(x, 2)}, {round(y, 2)})", margin=False)
        self.popFillAttributes()

    def drawHull(self, curve, t, lineColor=colorLightGrey, pointColor=colorBlack):
        self.drawSkeleton(curve, lineColor, [pointColor])

        if lineColor: self.pushStrokeAttributes(color=lineColor, opacity=0.5)
        order = curve.order
        hull = curve.hull(t)
        start = len(curve.controlPoints)
        while order > 1:
            stop = start + order
            self.drawPointsAsSegments(hull[start:stop], lineColor)
            start = stop
            order -= 1

        if lineColor: self.popStrokeAtributes()

    def drawArrowBetweenPoints(self, startPoint, endPoint, color=None, style="open60", position="end"):
        if color:
            self._strokeColor = color

        self.setStrokeDash("2, 1")
        startX, startY = startPoint
        endX, endY = endPoint
        self.drawArrow(GlyphPlotterEngine.CoordinateSystem.content, startX, startY, endX, endY, style, position)
        self.setStrokeDash(None)




def test():
    import PathUtilities

    testContour = [[(292, 499), (292, 693), (376.5, 810.5)], [(376.5, 810.5), (461, 928), (599, 928)], [(599, 928), (670, 928), (727.5, 895.5)], [(727.5, 895.5), (785, 863), (809, 813)], [(809, 813), (809, 197)], [(809, 197), (775, 139), (719.0, 107.0)], [(719.0, 107.0), (663, 75), (584, 75)], [(584, 75), (457, 75), (374.5, 190.5)], [(374.5, 190.5), (292, 306), (292, 499)]]
    testBounds = PathUtilities.PUBoundsRectangle.fromContour(testContour)

    cp = ContourPlotter(testBounds.points)

    cp.drawContours([testContour], PathUtilities.colorFromName("red"), False)

    image = cp.generateFinalImage()

    imageFile = open(f"Curve Test.svg", "wt", encoding="UTF-8")
    imageFile.write(image)
    imageFile.close()

    pcp = ContourPlotter(testBounds.points, poly=True)
    pcp.drawContours([testContour], PathUtilities.colorFromName("green"), False)

    polyImage = pcp.generateFinalImage()


    polyImageFile = open(f"Poly Curve Test.svg", "wt", encoding="UTF-8")
    polyImageFile.write(polyImage)
    polyImageFile.close()

if __name__ == "__main__":
    test()
