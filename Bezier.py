"""\
A bézier curve object

Created on August 30, 2020

Much of this code translated from bezier.js, utils.js and others
from https://github.com/Pomax/BezierInfo-2

@author Eric Mader
"""

import math
import types
from decimal import Decimal, getcontext
import BezierUtilities as butils
import PathUtilities
import CurveFitting
from ContourPlotter import ContourPlotter

MAX_SAFE_INTEGER = +9007199254740991  # Number.MAX_SAFE_INTEGER
MIN_SAFE_INTEGER = -9007199254740991  # Number.MIN_SAFE_INTEGER

class Bezier(object):
    dir_mixed = -1
    dir_flat = 0
    dir_up = 1
    dir_down = 2

    __slots__ = "_controlPoints", "_t1", "_t2", "_dcPoints", "_extrema", "_length", "_bbox", "_boundsRectangle", \
                "_lut", "_direction", "_linear", "_clockwise", "_start", "_end"

    def __init__(self, controlPoints):
        self._controlPoints = controlPoints
        self._t1 = 0
        self._t2 = 1
        self._dcPoints = None
        self._extrema = None
        self._length = None
        self._bbox = None
        self._boundsRectangle = None
        self._lut = []

        self._direction = self._computeDirection()

        # a bit of a hack to deal with the fact that control points
        # are sometimes Decimal values...
        def fp(p): return (float(p[0]), float(p[1]))

        cp = [fp(p) for p in self.controlPoints]
        aligned = self._align(cp, [cp[0], cp[-1]])
        self._linear = len([x for x in aligned if abs(x[1]) > 0.0001]) == 0

        angle = butils.angle(cp[0], cp[-1], cp[1])
        self._clockwise = angle > 0

    def _computeDirection(self):
        p0x, p0y = self._controlPoints[0]
        p1x, p1y = self._controlPoints[1]

        if self.order == 1:
            if p0y == p1y:
                return Bezier.dir_flat

            if p0y < p1y:
                return Bezier.dir_up

            return Bezier.dir_down

        p2x, p2y = self._controlPoints[2]
        if self.order == 2:
            if p0y <= p1y <= p2y:
                return Bezier.dir_up
            if p0y >= p1y >= p2y:
                return Bezier.dir_down

            # we assume that a quadratic bezier won't be flat...
            return Bezier.dir_mixed

        p3x, p3y = self._controlPoints[3]
        if self.order == 3:
            if p0y <= p1y <= p2y <= p3y:
                return Bezier.dir_up
            if p0y >= p1y >= p2y >= p3y:
                return Bezier.dir_down

            # we assume that a cubic bezier won't be flat...
            return Bezier.dir_mixed

        # For now, just say higher-order curves are mixed...
        return Bezier.dir_mixed

    def _compute(self, t):
        # shortcuts...
        if t == 0: return self._controlPoints[0]

        if t == 1: return self._controlPoints[self.order]

        mt = 1 - t
        p = self._controlPoints

        # constant?
        if self.order == 0: return self._controlPoints[0]

        # linear?
        if self.order == 1:
            p0x, p0y = p[0]
            p1x, p1y = p[1]
            return (mt * p0x + t * p1x, mt * p0y + t * p1y)

        # quadratic / cubic?
        if self.order < 4:
            mt2 = mt * mt
            t2 = t * t

            if self.order == 2:
                p = [p[0], p[1], p[2], (0, 0)]
                a = mt2
                b = mt * t * 2
                c = t2
                d = 0
            elif self.order == 3:
                a = mt2 * mt
                b = mt2 * t * 3
                c = mt * t2 * 3
                d = t * t2

            p0x, p0y = p[0]
            p1x, p1y = p[1]
            p2x, p2y = p[2]
            p3x, p3y = p[3]
            rx = a * p0x + b * p1x + c * p2x + d * p3x
            ry = a * p0y + b * p1y + c * p2y + d * p3y
            return (rx, ry)
        else:
            # higher order curves: use de Casteljau's computation
            #   JavaScript code does this:
            #     const dCpts = JSON.parse(JSON.stringify(points));
            #   This is a copy operation...
            dcPoints = p
            while len(dcPoints) > 1:
                newPoints = []
                for i in range(len(dcPoints) - 1):
                    x0, y0 = dcPoints[i]
                    x1, y1 = dcPoints[i + 1]
                    nx = x0 + (x1 - x0) * t
                    ny = y0 + (y1 - y0) * t
                    newPoints.append((nx, ny))
                dcPoints = newPoints
            return dcPoints[0]

    def _derivative(self, t):
        p = self.dcPoints[0]
        mt = 1 - t

        if self.order == 2:
            p = [p[0], p[1], (0, 0)]
            a = mt
            b = t
            c = 0
        elif self.order == 3:
            a = mt * mt
            b = mt * t * 2
            c = t * t

        p0x, p0y = p[0]
        p1x, p1y = p[1]
        p2x, p2y = p[2]

        # if t is Decimal, convert the x, y coordinates to Decimal
        if type(t) == type(Decimal(0)):
            p0x = Decimal(p0x)
            p0y = Decimal(p0y)
            p1x = Decimal(p1x)
            p1y = Decimal(p1y)
            p2x = Decimal(p2x)
            p2y = Decimal(p2y)

        rx = a * p0x + b * p1x + c * p2x
        ry = a * p0y + b * p1y + c * p2y
        return (rx, ry)

    def _tangent(self, t):
        d = self._derivative(t)
        q = math.hypot(d[0], d[1])
        return (d[0] / q, d[1] / q)

    def _normal(self, t):
        d = self._derivative(t)
        q = math.hypot(d[0], d[1])
        return (-d[1] / q, d[0] / q)

    def _getminmax(self, d, list):
        # if (!list) return { min: 0, max: 0 };
        min = +9007199254740991  # Number.MAX_SAFE_INTEGER
        max = -9007199254740991  # Number.MIN_SAFE_INTEGER

        if 0 not in list: list.insert(0, 0)
        if 1 not in list: list.append(1)

        for i in range(len(list)):
            c = self.get(list[i])
            if c[d] < min: min = c[d]
            if c[d] > max: max = c[d]

        return (min, max)

    @property
    def start(self):
        return self._controlPoints[0]

    @property
    def startX(self):
        return self.start[0]

    @property
    def startY(self):
        return self.start[1]

    @property
    def end(self):
        return self._controlPoints[-1]

    @property
    def endX(self):
        return self.end[0]

    @property
    def endY(self):
        return self.end[1]

    @property
    def bbox(self):
        if not self._bbox:
            extrema = self.extrema
            result = {}

            for dim in range(2):
                result[dim] = self._getminmax(dim, extrema[dim])

            self._bbox = result

        return self._bbox

    @property
    def tightbbox(self):
        aligned = self.align()
        tBounds = aligned.boundsRectangle
        angle = PathUtilities.rawSlopeAngle(self.controlPoints)
        translate = PathUtilities.PUTransform.rotateAndMove((0, 0), self.controlPoints[0], angle)
        tbContour = translate.applyToContour(tBounds.contour)
        return tbContour

    @property
    def boundsRectangle(self):
        if not self._boundsRectangle:
            bbox = self.bbox
            minX, maxX = bbox[0]
            minY, maxY = bbox[1]
            self._boundsRectangle = PathUtilities.PUBoundsRectangle((minX, minY), (maxX, maxY))

        return self._boundsRectangle

    @property
    def skeletonBounds(self):
        sbounds = PathUtilities.PUBoundsRectangle.fromContour([self.controlPoints])
        sbounds.right += 40
        return sbounds

    def get(self, t):
        return self._compute(t)

    @staticmethod
    def _align(points, segment):
        angle = PathUtilities.rawSlopeAngle(segment)
        transform = PathUtilities.PUTransform.moveAndRotate(segment[0], (0, 0), -angle)
        return transform.applyToSegment(points)

    @property
    def controlPoints(self):
        return self._controlPoints

    @property
    def order(self):
        return len(self._controlPoints) - 1

    @property
    def direction(self):
        return self._direction

    @property
    def midpoint(self):
        return self.get(0.5)

    @property
    def dcPoints(self):
        if not self._dcPoints:
            dpoints = []
            p = self._controlPoints
            d = len(p)

            while d > 1:
                dpts = []
                c = d - 1
                for j in range(c):
                    x0, y0 = p[j]
                    x1, y1 = p[j+1]
                    dpts.append((c*(x1-x0), c*(y1-y0)))
                dpoints.append(dpts)
                p = dpts
                d -= 1

            self._dcPoints = dpoints

        return self._dcPoints

    @property
    def extrema(self):
        if not self._extrema:
            result = {}
            roots = []

            for dim in range(2):
                p = list(map(lambda p: p[dim], self.dcPoints[0]))
                result[dim] = butils.droots(p)
                if self.order == 3:
                    p = list(map(lambda p: p[dim], self.dcPoints[1]))
                    result[dim].extend(butils.droots(p))
                result[dim] = list(filter(lambda t: t >= 0 and t <= 1, result[dim]))
                roots.extend(sorted(result[dim]))

            result[2] = butils.removeDuplicates(sorted(roots))

            self._extrema = result

        return self._extrema

    def overlaps(self, curve):
        return self.boundsRectangle.intersection(curve.boundsRectangle) is not None

    def hull(self, t):
        p = self.controlPoints
        q = [pt for pt in p]

        # we lerp between all points at each iteration, until we have 1 point left.
        while len(p) > 1:
            _p = []
            for i in range(len(p) - 1):
                pt = butils.lerp(t, p[i], p[i + 1])
                q.append(pt)
                _p.append(pt)
            p = _p

        return q

    # LUT == LookUp Table
    def getLUT(self, steps=100):
        if len(self._lut) == steps: return self._lut

        self._lut = []
        # We want a range from 0 to 1 inclusive, so
        # we decrement steps and use range(steps+1)
        steps -= 1
        for t in range(steps+1):
            self._lut.append(self.get(t / steps))

        return self._lut

    def _arcfun(self, t):
        dx, dy = self._derivative(t)

        # getcontext().prec += 2
        result = (dx * dx + dy * dy).sqrt()
        # getcontext().prec -= 2
        return result

    @classmethod
    def pointXY(cls, point):
        return point

    @classmethod
    def xyPoint(cls, x, y):
        return x, y

    @property
    def length(self):
        if not self._length:
            z = Decimal(0.5)
            sum = Decimal(0)

            getcontext().prec += 2
            for i in range(len(butils.tValues)):
                t = butils.tValues[i].fma(z, z)
                sum = butils.cValues[i].fma(self._arcfun(t), sum)

            length = z * sum
            getcontext().prec -= 2
            self._length = +length

        return self._length

    def split(self, t1, t2=None):
        # shortcuts...
        if t1 == 0 and t2: return self.split(t2)[0]
        if t2 == 1: return self.split(t1)[1]

        # no shortcut: use "de Casteljau" iteration.
        q = self.hull(t1)
        if self.order == 2:
            left = Bezier([q[0], q[3], q[5]])
            right = Bezier([q[5], q[4], q[2]])
        else:
            left = Bezier([q[0], q[4], q[7], q[9]])
            right = Bezier([q[9], q[8], q[6], q[3]])

        # make sure we bind _t1/_t2 information!
        left._t1 = butils.map(0, 0, 1, self._t1, self._t2)
        left._t2 = butils.map(t1, 0, 1, self._t1, self._t2)
        right._t1 = butils.map(t1, 0, 1, self._t1, self._t2)
        right._t2 = butils.map(1, 0, 1, self._t1, self._t2)

        # if we have no t2, we're done
        if not t2: return (left, right, q)

        t2 = butils.map(t2, t1, 1, 0, 1)
        return right.split(t2)[0]

    def roots(self, segment=None):

        if segment:
            p = Bezier._align(self.controlPoints, segment)
        else:
            p = self.controlPoints

        def reduce(t):
            return 0 <= t <= 1 or butils.approximately(t, 0) or butils.approximately(t, 1)

        order = len(p) - 1
        if order == 2:
            a = p[0][1]
            b = p[1][1]
            c = p[2][1]
            d = a - 2 * b + c
            if d != 0:
                m1 = -butils.sqrt(b * b - a * c)
                m2 = -a + b
                v1 = -(m1 + m2) / d
                v2 = -(-m1 + m2) / d
                return list(filter(reduce, [v1, v2]))
            elif b != c and d == 0:
                return list(filter(reduce, [(2 * b - c) / (2 * b - 2 * c)]))

            return []

        # see http://www.trans4mind.com/personal_development/mathematics/polynomials/cubicAlgebra.htm
        pa = p[0][1]
        pb = p[1][1]
        pc = p[2][1]
        pd = p[3][1]

        d = -pa + 3 * pb - 3 * pc + pd
        a = 3 * pa - 6 * pb + 3 * pc
        b = -3 * pa + 3 * pb
        c = pa

        if butils.approximately(d, 0):
            # this is not a cubic curve.
            if butils.approximately(a, 0):
                # in fact, this is not a quadratic curve either.
                if butils.approximately(b, 0):
                    # in fact, there are no solutions
                    return []

                # linear solution:
                return list(filter(reduce, [-c / b]))

            # quadratic solution:
            q = butils.sqrt(b * b - 4 * a * c)
            a2 = 2 * a
            return list(filter(reduce, [(q - b) / a2, (-b - q) / a2]))

        # at this point, we know we need a cubic solution:
        a /= d
        b /= d
        c /= d

        p = (3 * b - a * a) / 3
        p3 = p / 3
        q = (2 * a * a * a - 9 * a * b + 27 * c) / 27
        q2 = q / 2
        discriminant = q2 * q2 + p3 * p3 * p3

        if discriminant < 0:
            mp3 = -p / 3
            mp33 = mp3 * mp3 * mp3
            r = butils.sqrt(mp33)
            t = -q / (2 * r)
            # cosphi = t < -1 ? -1: t > 1 ? 1: t
            cosphi = -1 if t < -1 else 1 if t > 1 else t
            phi = math.acos(cosphi)
            crtr = butils.crt(r)
            t1 = 2 * crtr
            x1 = t1 * math.cos(phi / 3) - a / 3
            x2 = t1 * math.cos((phi + butils.tau) / 3) - a / 3
            x3 = t1 * math.cos((phi + 2 * butils.tau) / 3) - a / 3
            return list(filter(reduce, [x1, x2, x3]))
        elif butils.approximately(discriminant, 0):  # discriminant == 0:
            u1 = butils.crt(-q2) if q2 < 0 else -butils.crt(q2)
            x1 = 2 * u1 - a / 3
            x2 = -u1 - a / 3
            return list(filter(reduce, [x1, x2]))
        else:
            sd = butils.sqrt(discriminant)
            u1 = butils.crt(-q2 + sd)
            v1 = butils.crt(q2 + sd)
            return list(filter(reduce, [u1 - v1 - a / 3]))

    def align(self, segment=None):
        if not segment:
            segment = self.controlPoints

        return Bezier(Bezier._align(self.controlPoints, segment))

    def normal(self, t):
        dx, dy = self._derivative(t)
        q = butils.sqrt(dx * dx + dy * dy)
        return (-dy / q, dx / q)


    def simple(self):
        if self.order == 3:
            a1 = butils.angle(self.controlPoints[0], self.controlPoints[3], self.controlPoints[1])
            a2 = butils.angle(self.controlPoints[0], self.controlPoints[3], self.controlPoints[2])
            if (a1 > 0 and a2 < 0) or (a1 < 0 and a2 > 0): return False

        n1x, n1y = self.normal(0)
        n2x, n2y = self.normal(1)
        s = n1x * n2x + n1y * n2y
        return abs(math.acos(s)) < math.pi / 3

    def reduce(self):
        pass1 = []
        pass2 = []

        # first pass: split on extrema
        extrema = self.extrema[2]
        if not 0 in extrema: extrema.insert(0, 0)
        if not 1 in extrema: extrema.append(1)

        t1 = extrema[0]
        for i in range(1, len(extrema)):
            t2 = extrema[i]
            segment = self.split(t1, t2)
            segment._t1 = t1
            segment._t2 = t2
            pass1.append(segment)
            t1 = t2

        # second pass: further reduce these segments to simple segments
        step = 0.01
        for p1 in pass1:
            t1 = 0
            t2 = 0
            while t2 <= 1:
                t2 = t1 + step
                while t2 <= 1:
                    segment = p1.split(t1, t2)
                    if not segment.simple():
                        t2 -= step
                        if abs(t1 - t2) < step:
                            # we can never form a reduction
                            return []
                        segment = p1.split(t1, t2)
                        segment._t1 = butils.map(t1, 0, 1, p1._t1, p1._t2)
                        segment._t2 = butils.map(t2, 0, 1, p1._t1, p1._t2)
                        pass2.append(segment)
                        t1 = t2
                        break
                    t2 += step

            if t1 < 1:
                segment = p1.split(t1, 1)
                segment._t1 = butils.map(t1, 0, 1, p1._t1, p1._t2)
                segment._t2 = p1._t2
                pass2.append(segment)

        return pass2

    def lineIntersects(self, line):
        p1, p2 = line
        p1x, p1y = p1
        p2x, p2y = p2
        mx = min(p1x, p2x)
        my = min(p1y, p2y)
        MX = max(p1x, p2x)
        MY = max(p1y, p2y)

        def onLine(t):
            x, y = self.get(t)
            return butils.between(x, mx, MX) and butils.between(y, my, MY)

        return list(filter(onLine, self.roots(line)))

    def intersectWithLine(self, line):
        if self.order == 1:
            return butils.lli(self.controlPoints, line.controlPoints)

        roots = self.roots(line.controlPoints)

        if roots:
            root = 0 if roots[0] < 0 else 1 if roots[0] > 1 else roots[0]

            return self.get(root)

        return None

    @staticmethod
    def curveIntersects(c1, c2, intersectionThreshold=0.5):
        pairs = []

        # step 1: pair off any overlapping segments
        for l in c1:
            for r in c2:
                if l.overlaps(r):
                    pairs.append((l, r))

        # step 2: for each pairing, run through the convergence algorithm.
        intersections = []
        for pair in pairs:
            result = butils.pairiteration(pair[0], pair[1], intersectionThreshold)
            if len(result) > 0:
                intersections.extend(result)

        return intersections

    def selfIntersects(self, intersectionThreshold=0.5):
        # "simple" curves cannot intersect with their direct
        # neighbor, so for each segment X we check whether
        # it intersects [0:x-2][x+2:last].
        reduced = self.reduce()
        length = len(reduced) - 2
        results = []

        for i in range(length):
            left = reduced[i]
            right = reduced[i+2:]
            result = Bezier.curveIntersects(left, right, intersectionThreshold)
            results.extend(result)

        return results

    def intersects(self, curve, intersectionThreshold=0.5):
        if curve is None: return self.selfIntersects(intersectionThreshold)
        # if curve is a line: self.lineIntersects(line, intersectionThreshold)
        #if curve instanceOf Bezier: curve = curve.reduce()

        return Bezier.curveIntersects(self.reduce(), curve.reduce(), intersectionThreshold)

    def getABC(self, t):
        hull = self.hull(t)
        points = self.controlPoints
        if self.order == 2:
            A = points[1]
            B = hull[5]
            ratio = butils.quadraticRatio(t)
        elif self.order == 3:
            A = hull[5]
            B = hull[9]
            ratio = butils.cubicRatio(t)

        C = butils.lli4(A, B, points[0], points[-1])

        return (A, B, C, ratio, hull)

    def raiseOrder(self):
        p = self.controlPoints
        k = len(p)
        np = [p[0]]
        for i in range(k):
            pix, piy = pi = p[i]
            pimx, pimy = pim = p[i - 1]
            x = ((k - i) / k) * pix + (i / k) * pimx
            y = ((k - i) / k) * piy + (i / k) * pimy
            np.append((x, y))
        np.append(p[-1])
        return Bezier(np)

    def offset(self, t, d=None):
        def rp(r):
            if r._linear:
                return r.offset(t)[0]
            return r.scale(t)

        if d:
            cx, cy = c = self.get(t)
            nx, ny = n = self.normal(t)
            px = cx + nx * d
            py = cy + ny * d
            return [c, n, (px, py)]

        if self._linear:
            nv = self.normal(0)
            coords = list(map(lambda p: (p[0] + t * nv[0], p[1] + t * nv[1]), self.controlPoints))
            return [Bezier(coords)]

        reduced = self.reduce()
        return list(map(rp, reduced))

    def scale(self, d):
        distanceFn = None
        order = self.order

        if type(d) == types.FunctionType:
            distanceFn = d

        if distanceFn and order == 2: return self.raiseOrder().scale(distanceFn)

        # TODO: add special handling for degenerate (=linear) curves.
        clockwise = self._clockwise
        r1 = distanceFn(0) if distanceFn else d
        r2 = distanceFn(1) if distanceFn else d
        v = [self.offset(0, 10), self.offset(1, 10)]
        np = [(0, 0) for _ in range(order+1)]
        ox, oy = o = butils.lli4(v[0][2], v[0][0], v[1][2], v[1][0])

        if not o:
            raise ValueError("Cannot scale this curve. Try reducing it first.")

        # move all points by distance 'd' wrt the origin 'o'

        # move end points by fixed distance along normal.
        for t in range(2):
            px, py = self.controlPoints[t * order]
            px += (r2 if t > 0 else r1) * v[t][1][0]  # v[t].n.x
            py += (r2 if t > 0 else r1) * v[t][1][1]  # v[t].n.y
            np[t * order] = (px, py)

        if distanceFn is None:
            # move control points to lie on the intersection of the offset
            # derivative vector, and the origin-through-control vector
            for t in range(2):
                if order == 2 and t > 0: break
                px, py = p = np[t * order]
                dx, dy = d = self._derivative(t)
                p2 = (px + dx, py + dy)
                np[t + 1] = butils.lli4(p, p2, o, self.controlPoints[t + 1])

            return Bezier(np)

        # move control points by "however much necessary to
        # ensure the correct tangent to endpoint".
        for t in range(2):
            if order == 2 and t > 0: break
            px, py = p = self.controlPoints[t + 1]
            ovx, ovy = (px - ox, py - oy)
            rc = distanceFn((t + 1) / order) if distanceFn else d
            if distanceFn and not clockwise: rc = -rc
            m = math.hypot(ovx, ovy)
            ovx /= m
            ovy /= m
            np[t + 1] = (px + rc * ovx, py + rc * ovy)

        return Bezier(np)

class BContour(object):
    def __init__(self, contour):
        beziers = []
        bounds = PathUtilities.PUBoundsRectangle()

        for segment in contour:
            bezier = Bezier(segment)
            bounds = bounds.union(bezier.boundsRectangle)
            beziers.append(bezier)

        self._beziers = beziers
        self._bounds = bounds
        self._lut = []
        self._start = beziers[0].start
        self._end = beziers[-1].end

    def __getitem__(self, index):
        return self._beziers[index]

    def __setitem__(self, index, value):
        self._beziers[index] = Bezier(value)
        # self._length = None
        self._start = self._beziers[0].start
        self._end = self._beziers[-1].end

    def __delitem__(self, index):
        del self._beziers[index]
        # self._length = None
        self._start = self._beziers[0].start
        self._end = self._beziers[-1].end

    def __iter__(self):
        return self._beziers.__iter__()

    def getLUT(self, steps=100):
        if len(self._lut) == steps: return self._lut

        self._lut = []
        startPoint = 0
        for curve in self._beziers:
            self._lut.extend(curve.getLUT(steps)[startPoint:])
            # for every curve but the first, the first point is
            # the same as the last point of the last curve
            startPoint = 1

        return self._lut

    @classmethod
    def _findClosest(cls, point, LUT):
        x, y = point
        closest = MAX_SAFE_INTEGER
        for index in range(len(LUT)):
            px, py = LUT[index]
            dist = math.hypot(px - x, py - y)
            if dist < closest:
                closest = dist
                i = index

        return i

    @classmethod
    def _refineBinary(cls, point, curve, LUT, i):
        closest = MAX_SAFE_INTEGER
        steps = len(LUT)
        TT = [t / (steps - 1) for t in range(steps)]
        px, py = point

        for _ in range(25):  # This is for safety; the loop should always break
            steps = len(LUT)
            i1 = 0 if i == 0 else i - 1
            i2 = i if i == steps - 1 else i + 1
            t1 = TT[i1]
            t2 = TT[i2]
            lut = []
            tt = []
            step = (t2 - t1) / 5

            if step < 0.001: break
            lut.append(LUT[i1])
            tt.append(TT[i1])
            for j in range(1, 4):
                nt = t1 + (j * step)
                nx, ny = n = curve.get(nt)
                dist = math.hypot(nx - px, ny - py)
                if dist < closest:
                    closest = dist
                    q = n
                    i = j
                lut.append(n)
                tt.append(nt)
            lut.append(LUT[i2])
            tt.append(TT[i2])

            # update the LUT to be our new five point LUT, and run again.
            LUT = lut
            TT = tt

        return (q, closest)

    def findClosestPoint(self, point, steps):
        nCurves = len(self.beziers)
        curve2 = None
        i = self._findClosest(point, self.getLUT(steps))

        if i < steps:
            curve = self.beziers[0]
            if i == steps - 1 and nCurves >= 2: curve2 = self.beziers[1]
        else:
            i -= steps
            s1 = steps - 1
            ix = i // s1 + 1
            curve = self.beziers[ix]
            if ix < nCurves - 1: curve2 = self.beziers[ix + 1]
            i %= s1

        LUT = curve.getLUT(steps)
        cip, closest = self._refineBinary(point, curve, LUT, i)

        if curve2:
            LUT = curve2.getLUT(steps)
            cip2, c2 = self._refineBinary(point, curve2, LUT, 0)

            if c2 < closest:
                closest = c2
                cip = cip2

        return (closest, cip)

    def pointToString(self, point):
        return ",".join([str(i) for i in point])

    def d(self, useSandT=False, use_closed_attrib=False, rel=False):
        """Returns a path d-string for the path object.
        For an explanation of useSandT and use_closed_attrib, see the
        compatibility notes in the README."""

        commands = []
        lastCommand = ""
        pen = firstPoint = self.start
        commands.append(f"M{self.pointToString(firstPoint)}")

        def getCommand(command, lastCommand):
            return " " if lastCommand == command else command, command

        for bezier in self.beziers:
            segment = bezier.controlPoints
            if len(segment) == 2:
                # a line
                penX, penY = pen
                x, y = segment[1]

                if penX == x and penY == y:
                    continue
                elif penX == x:
                    # vertical line
                    command, lastCommand = getCommand("V", lastCommand)
                    commands.append(f"{command}{y}")
                elif penY == y:
                    # horizontal line
                    command, lastCommand = getCommand("H", lastCommand)
                    commands.append(f"{command}{x}")
                else:
                    point = self.pointToString(segment[1])
                    command, lastCommand = getCommand("L", lastCommand)
                    commands.append(f"{command}{point}")
                pen = (x, y)
            elif len(segment) == 3:
                    p1 = self.pointToString(segment[1])
                    p2 = self.pointToString(segment[2])
                    command, lastCommand = getCommand("Q", lastCommand)
                    commands.append(f"{command}{p1} {p2}")
                    pen = segment[2]
            elif len(segment) == 4:
                p1 = self.pointToString(segment[1])
                p2 = self.pointToString(segment[2])
                p3 = self.pointToString(segment[3])
                command, lastCommand = getCommand("C", lastCommand)
                commands.append(f"{command}{p1} {p2} {p3}")
                pen = segment[3]

        # if use_closed_attrib: commands.append("Z")

        return "".join(commands)

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @property
    def boundsRectangle(self):
        return self._bounds

    @property
    def beziers(self):
        return self._beziers

    @classmethod
    def pointXY(cls, point):
        return Bezier.pointXY(point)

    @classmethod
    def xyPoint(cls, x, y):
        return Bezier.xyPoint(x, y)

class BOutline(object):
    __slots__ = "_bContours", "_bounds"

    def __init__(self, contours):
        bounds = PathUtilities.PUBoundsRectangle()
        bContours = []

        for contour in contours:
            bc = BContour(contour)
            bContours.append(bc)
            bounds = bounds.union(bc.boundsRectangle)

        self._bContours = bContours
        self._bounds = bounds

    def __iter__(self):
        return self._bContours.__iter__()

    @classmethod
    def pointXY(cls, point):
        return Bezier.pointXY(point)

    @classmethod
    def xyPoint(cls, x, y):
        return Bezier.xyPoint(x, y)

    @classmethod
    def segmentFromPoints(cls, points):
        return Bezier(points)

    @classmethod
    def unzipPoints(cls, points):
        xs = []
        ys = []

        for x, y in points:
            xs.append(x)
            ys.append(y)

        return xs, ys

    @classmethod
    def pathFromSegments(cls, *segments):
        return BContour([s.controlPoints for s in segments])

    @property
    def bContours(self):
        return self._bContours

    @property
    def contours(self):
        return self._bContours

    @property
    def boundsRectangle(self):
        return self._bounds

def drawCurve(cp, curve, color=None):
    if curve.order <= 3:
        cp.drawCurve(curve.controlPoints, color)
    else:
        lpts = curve.getLUT()
        cp.drawPointsAsSegments(lpts, color)

def drawContour(cp, contour, color=None):
    for bezier in contour.beziers:
        cp.drawCurve(bezier.controlPoints, color)

def drawOutline(cp, outline, color=None):
    for bc in outline.bContours:
        drawContour(cp, bc, color=color)
        drawContour(cp, bc, color=color)

def fitCurveToPoints(points, polygonal=True):
    p, m, s, c = CurveFitting.fit(points, polygonal=polygonal)
    cx, cy = c
    bpoints = []
    for i in range(len(p)):
        bpoints.append((cx[i][0], cy[i][0]))

    return Bezier(bpoints)

def getDefaultQuadratic():
    qPoints = [(70, 50), (20, 190), (250, 240)]
    return Bezier(qPoints)

def getDefaultCubic():
    cPoints = [(120, 140), (35, 100), (220, 40), (220, 260)]
    return Bezier(cPoints)

def test():
    from FontDocTools import GlyphPlotterEngine

    colorRed = PathUtilities.PUColor.fromName("red")
    colorGreen = PathUtilities.PUColor.fromName("green")
    colorBlue = PathUtilities.PUColor.fromName("blue")
    colorGold = PathUtilities.PUColor.fromName("gold")
    colorMagenta = PathUtilities.PUColor.fromName("magenta")
    colorCyan = PathUtilities.PUColor.fromName("cyan")
    colorYellow = PathUtilities.PUColor.fromName("yellow")
    colorBlack = PathUtilities.PUColor.fromName("black")
    colorLightGrey = PathUtilities.PUColor.fromName("lightgrey")
    colorLightBlue = PathUtilities.PUColor.fromName("lightblue")
    colorLightGreen = PathUtilities.PUColor.fromName("lightgreen")
    colorOrange = PathUtilities.PUColor.fromName("orange")
    colorAqua = PathUtilities.PUColor.fromName("aqua")
    colorDarkGrey = PathUtilities.PUColor.fromName("darkgrey")

    curvePoints = [(90, 140), (25, 210), (230, 210), (150, 10)]
    # curvePoints = [(70, 0), (20, 140), (250, 190)]
    # curvePoints = [(0, 50), (100, 200)]

    curve1 = Bezier(curvePoints)

    bounds1 = curve1.boundsRectangle

    cp1 = ContourPlotter(bounds1.points)

    cp1.drawCurve(curve1.controlPoints, colorBlue)


    tbContour = curve1.tightbbox
    cp1._boundsAggregator.addBounds(PathUtilities.PUBoundsRectangle.fromContour(tbContour).points)
    cp1.setStrokeOpacity(0.5)

    cp1.drawContours([bounds1.contour], colorGold)

    cp1.drawContours([tbContour], colorMagenta)

    image1 = cp1.generateFinalImage()

    imageFile1 = open(f"Curve Bounding Boxes Test.svg", "wt", encoding="UTF-8")
    imageFile1.write(image1)
    imageFile1.close()

    cp1 = ContourPlotter(bounds1.points)

    cp1.drawCurve(curve1.controlPoints, colorBlue)
    cp1.setStrokeOpacity(0.5)

    nPoints = 10
    lLength = 20
    for i in range(nPoints + 1):
        t = i / nPoints
        px, py = curve1.get(t)

        tpx, tpy = curve1._tangent(t)
        tx = tpx * lLength/2
        ty = tpy * lLength/2
        cp1.drawContours([[[(px - tx, py - ty), (px + tx, py + ty)]]], colorRed)

        npx, npy = curve1._normal(t)
        nx = npx * lLength/2
        ny = npy * lLength/2
        cp1.drawContours([[[(px - nx, py - ny), (px + nx, py + ny)]]], colorGreen)

    image1 = cp1.generateFinalImage()

    imageFile1 = open(f"Curve Tangents and Normals Test.svg", "wt", encoding="UTF-8")
    imageFile1.write(image1)
    imageFile1.close()

    cp1 = ContourPlotter(bounds1.points)
    lpts = curve1.getLUT(30)
    cp1.drawPointsAsSegments(lpts, colorBlue)

    image1 = cp1.generateFinalImage()

    imageFile1 = open(f"Curve Flattening Test.svg", "wt", encoding="UTF-8")
    imageFile1.write(image1)
    imageFile1.close()

    cp1 = ContourPlotter(bounds1.points)
    lpts = curve1.getLUT(100)
    cp1.drawPointsAsCircles(lpts, 0.5, [colorBlue])

    image1 = cp1.generateFinalImage()

    imageFile1 = open(f"Curve as Points Test.svg", "wt", encoding="UTF-8")
    imageFile1.write(image1)
    imageFile1.close()

    curve5Points = [(0, 5), (40, 5), (40, 40), (80, 40), (80, -50), (120, -50)]

    curve5 = Bezier(curve5Points)
    # bounds5 = curve5.boundsRectangle
    bounds5 = PathUtilities.PUBoundsRectangle.fromContour([curve5.controlPoints])

    cp5 = ContourPlotter(bounds5.points)
    lpts = curve5.getLUT(100)
    # cp5.drawPointsAsCircles(lpts, 0.5, colorBlue)
    cp5.drawPointsAsSegments(lpts, colorBlue)
    cp5.drawSkeleton(curve5, colorLightBlue)
    # cp5.drawHull(curve5, 0.5, colorLightBlue)

    image5 = cp5.generateFinalImage()

    imageFile5 = open(f"Fifth Order Curve Test.svg", "wt", encoding="UTF-8")
    imageFile5.write(image5)
    imageFile5.close()

    curve9Points = [(175, 178), (220, 250), (114, 285), (27, 267), (33, 159), (146, 143), (205, 33), (84, 117), (43, 59), (58, 24)]
    curve9 = Bezier(curve9Points)
    bounds9 = curve9.boundsRectangle
    bounds9 = PathUtilities.PUBoundsRectangle.fromContour([curve9.controlPoints])

    cp9 = ContourPlotter(bounds9.points)
    lpts = curve9.getLUT(200)
    # cp9.drawPointsAsCircles(lpts, 0.5, colorBlue)
    cp9.drawPointsAsSegments(lpts, colorBlue)
    cp9.drawSkeleton(curve9, colorLightBlue, [colorBlack])

    image9 = cp9.generateFinalImage()

    imageFile9 = open(f"Ninth Order Curve Test.svg", "wt", encoding="UTF-8")
    imageFile9.write(image9)
    imageFile9.close()

    curve2 = getDefaultCubic()
    bounds2 = curve2.boundsRectangle

    lpts = curve2.getLUT(16)
    aLen = 0
    for i in range(len(lpts) - 1):
        aLen += PathUtilities.length([lpts[i], lpts[i+1]])

    cp2 = ContourPlotter(bounds2.points)
    margin = cp2._contentMargins.left
    cp2.drawCurve(curve2.controlPoints, colorBlue)
    cp2.drawText(bounds2.width / 2 + margin, cp2.labelFontSize / 4 - cp2._contentMargins.top, "center", f"Curve length: {curve2.length}")
    image2 = cp2.generateFinalImage()
    imageFile2 = open("Curve Length Test.svg", "wt", encoding="UTF-8")
    imageFile2.write(image2)
    imageFile2.close()

    cp2 = ContourPlotter(bounds2.points)


    lpts = curve2.getLUT(16)
    aLen = 0
    for i in range(len(lpts) - 1):
        aLen += PathUtilities.length([lpts[i], lpts[i + 1]])

    cp2.drawPointsAsSegments(lpts, colorBlue)
    cp2.drawText(bounds2.width / 2 + margin, cp2.labelFontSize / 4 - cp2._contentMargins.top, "center", f"Approximate curve length, 16 steps: {aLen}")

    image2 = cp2.generateFinalImage()
    imageFile2 = open("Approximate curve Length Test.svg", "wt", encoding="UTF-8")
    imageFile2.write(image2)
    imageFile2.close()

    cp2 = ContourPlotter(bounds2.points)
    left, right, _ = curve2.split(0.50)
    cp2.drawCurve(left.controlPoints, colorBlue)
    cp2.drawCurve(right.controlPoints, colorMagenta)
    cp2.drawHull(curve2, 0.5, colorLightGreen)


    image2 = cp2.generateFinalImage()
    imageFile2 = open("Split Curve Test.svg", "wt", encoding="UTF-8")
    imageFile2.write(image2)
    imageFile2.close()

    def generate(curve):
        pts = [(0, 0)]

        steps = 100
        for v in range(1, steps + 1):
            t = Decimal(v) / steps
            left, _, _ = curve.split(t)
            d = left.length
            pts.append((float(d), float(t)))

        return pts

    pts = generate(curve2)
    c2len = curve2.length
    ts = []
    s = 8
    for i in range(s+1):
        target = (i * c2len) / s
        for p in range(len(pts)):
            if pts[p][0] > target:
                p -= 1
                break

        if p < 0: p = 0
        if p == len(pts): p = len(pts) - 1
        ts.append(pts[p])

    colors = [colorMagenta, colorCyan]
    idx = 0

    cp2 = ContourPlotter(bounds2.points)

    cp2.setStrokeColor(colors[0])
    p0 = curve2.get(pts[0][1])
    x, y = curve2.get(0)
    cp2.drawPointsAsCircles([(x, y)], 4, fill=False)

    for i in range(1, len(pts)):
        p1 = curve2.get(pts[i][1])
        cp2.drawContours([[[p0, p1]]])
        if pts[i] in ts:
            idx += 1
            cp2.setStrokeColor(colors[idx % len(colors)])
            cp2.drawPointsAsCircles([p1], 4, fill=False)
        p0 = p1

    image2 = cp2.generateFinalImage()
    imageFile2 = open("Curve Fixed Interval Test.svg", "wt", encoding="UTF-8")
    imageFile2.write(image2)
    imageFile2.close()

    l1 = [(50, 250), (150, 190)]
    l2 = [(50, 50), (170, 130)]

    ip = butils.lli(l1, l2)

    bounds2 = PathUtilities.PUBoundsRectangle(l1[0], l1[1], l2[0], l2[1], ip)
    cp2 = ContourPlotter(bounds2.points)
    cp2.setStrokeWidth(1)
    cp2.drawContours([[l1]])
    cp2.drawContours([[l2]])
    cp2.setStrokeColor(colorRed)


    cp2.drawPointsAsCircles([ip], 3, fill=False)

    image2 = cp2.generateFinalImage()
    imageFile2 = open("Line Intersect Test.svg", "wt", encoding="UTF-8")
    imageFile2.write(image2)
    imageFile2.close()

    l3 = [(25, 40), (230, 280)]
    curve3Points = [(100, 60), (30, 240), (210, 70), (160, 270)]
    curve3 = Bezier(curve3Points)
    boundsc3 = curve3.boundsRectangle
    boundsl3 = PathUtilities.PUBoundsRectangle.fromContour([l3])
    bounds3 = boundsc3.union(boundsl3)
    cp3 = ContourPlotter(bounds3.points)
    cp3.drawCurve(curve3.controlPoints, colorBlue)
    cp3.drawContours([[l3]], colorGreen)

    roots = curve3.roots(l3)

    cp3.setStrokeColor(colorCyan)
    cp3.setLabelFontSize(6, 6)
    for t in roots:
        ip = curve3.get(t)
        ipx, ipy = ip
        cp3.drawPointsAsCircles([ip], 3, fill=False)
        cp3.drawText(ipx + 6, ipy - 6, "left", f"t = {t}", margin=False)

    image3 = cp3.generateFinalImage()
    image3File = open("Line and Curve Intersect Test.svg", "wt", encoding="UTF-8")
    image3File.write(image3)
    image3File.close()

    curve4Points = [(10, 200), (90, 270), (40, 160), (220, 80)]
    curve5Points = [(5, 150), (180, 280), (80, 50), (210, 120)]

    curve4 = Bezier(curve4Points)
    curve5 = Bezier(curve5Points)

    bounds = curve4.boundsRectangle.union(curve5.boundsRectangle)
    cp4 = ContourPlotter(bounds.points)
    cp4.setStrokeWidth(1)
    # cp4.setStrokeOpacity(0.8)
    cp4.drawCurve(curve4.controlPoints, colorGreen)
    cp4.drawCurve(curve5.controlPoints, colorBlue)

    def same(a, b):
        return abs(a[0] - b[0]) < 0.01 and abs(a[1] - b[1]) < 0.01

    results = curve4.intersects(curve5)

    tvals = []
    last = (2.0, 2.0)
    for tval in results:
        if not same(tval, last):
            tvals.append(tval)
            last = tval

    cp4.setStrokeColor(colorCyan)
    for tval in tvals:
        ip = curve4.get(tval[0])
        cp4.drawPointsAsCircles([ip], 3, fill=False)

    image4 = cp4.generateFinalImage()
    image4File = open("Curve and Curve Intersect Test.svg", "wt", encoding="UTF-8")
    image4File.write(image4)
    image4File.close()

    lpts = curve2.controlPoints
    A, B, C, ratio, _ = curve2.getABC(0.5)

    bounds = PathUtilities.PUBoundsRectangle.fromContour([curve2.controlPoints])
    cp2 = ContourPlotter(bounds.points)
    cp2.drawCurve(curve2.controlPoints, colorBlue)

    cp2.setStrokeWidth(1)
    cp2.drawSkeleton(curve2)

    cp2.drawPointsAsSegments([lpts[0], lpts[3]], colorLightGrey)
    cp2.drawPointsAsCircles([A, B, C], 2, [colorBlack], fill=False)
    cp2.drawPointsAsSegments([B, C], colorGreen)
    cp2.drawPointsAsSegments([B, A], colorRed)

    cp2.drawText(A[0] + 4, A[1] - 4, "left", "A", margin=False)
    cp2.drawText(B[0] + 4, B[1] - 4, "left", "B (t = 0.5)", margin=False)
    cp2.drawText(C[0] + 4, C[1] - 4, "left", "C", margin=False)

    image2 = cp2.generateFinalImage()
    image2File = open("ABC Test.svg", "wt", encoding="UTF-8")
    image2File.write(image2)
    image2File.close()

    curve6Points = [(100, 70), (30, 140), (200, 250), (210, 140)]
    curve6 = Bezier(curve6Points)

    t = 0.5
    # preserve struts for B when repositioning
    A, B, C, ratio, hull = curve6.getABC(t)
    Bx, By = B
    Cx, Cy = C
    Blx, Bly = hull[7]
    Brx, Bry = hull[8]
    dblx, dbly = dbl = (Blx - Bx, Bly - By)
    dbrx, dbry = dbr = (Brx - Bx, Bry - By)
    pts = curve6.controlPoints

    newBx = Bx - 30
    newBy = By + 15
    newB = (newBx, newBy)


    newAx, newAy = newA = (newBx - (Cx - newBx) / ratio,
            newBy - (Cy - newBy) / ratio)

    # find new point on s--c1
    p1x, p1y = p1 = (newBx + dblx, newBy + dbly)
    sc1 = (newAx - (newAx - p1x) / (1 - t),
            newAy - (newAy - p1y) / (1 - t))
    # find new point on c2--e
    p2x, p2y = p2 = (newBx + dbrx, newBy + dbry)
    sc2 = (newAx + (p2x - newAx) / (t),
            newAy + (p2y - newAy) / (t))

    # construct new c1` based on the fact that s--sc1 is s--c1 * t
    nc1 = (pts[0][0] + (sc1[0] - pts[0][0]) / (t),
            pts[0][1] + (sc1[1] - pts[0][1]) / (t))

    # construct new c2` based on the fact that e--sc2 is e--c2 * (1-t)
    nc2 = (pts[3][0] - (pts[3][0] - sc2[0]) / (1 - t),
            pts[3][1] - (pts[3][1] - sc2[1]) / (1 - t))

    npts = [pts[0], nc1, nc2, pts[3]]
    nCurve = Bezier(npts)

    bounds6 = PathUtilities.PUBoundsRectangle.fromContour([curve6.controlPoints])
    nBounds = PathUtilities.PUBoundsRectangle.fromContour([nCurve.controlPoints])
    bounds = bounds6.union(nBounds)
    cp6 = ContourPlotter(bounds.points)
    cp6.setStrokeOpacity(0.5)
    cp6.setStrokeWidth(1)
    cp6.drawCurve(curve6.controlPoints, colorBlue)
    cp6.drawCurve(nCurve.controlPoints, colorGreen)

    cp6.setStrokeOpacity(1.0)
    cp6.drawPointsAsCircles([B], 2, [colorBlack], fill=False)
    cp6.drawPointsAsCircles([(newBx, newBy)], 2, [colorBlack], fill=False)
    cp6.drawArrowBetweenPoints(B, newB, colorRed, style="closed45")

    cp6.drawSkeleton(curve6, lineColor=colorLightBlue)
    cp6.drawSkeleton(nCurve, lineColor=colorLightGreen)
    # cp6.drawHull(curve6, 0.5, colorLightBlue)
    # cp6.drawHull(nCurve, 0.5, colorLightGreen)

    image6 = cp6.generateFinalImage()
    image6File = open("Curve Molding Test.svg", "wt", encoding="UTF-8")
    image6File.write(image6)
    image6File.close()

    lpts = [(56, 147), (144, 217), (188, 115)]

    (Sx, Sy), (Bx, By), (Ex, Ey) = S, B, E = lpts

    Cx, Cy = C = ((Sx + Ex) / 2, (Sy + Ey) / 2)

    ratio = butils.cubicRatio(0.5)
    Ax, Ay = A = (Bx + (Bx - Cx) / ratio, By + (By - Cy) / ratio)

    selen = PathUtilities.length([S, E])
    bclen_min = selen / 8
    bclen = PathUtilities.length([B, C])
    be12dist = bclen_min + bclen / 4  # aesthetics = 4
    bx = be12dist * (Ex - Sx) / selen
    by = be12dist * (Ey - Sy) / selen
    e1x, e1y = e1 = (Bx - bx, By - by)
    e2x, e2y = e2 = (Bx + bx, By + by)
    v1x, v1y = v1 = (Ax + (e1x - Ax) * 2, Ay + (e1y - Ay) * 2)
    v2x, v2y = v2 = (Ax + (e2x - Ax) * 2, Ay + (e2y - Ay) * 2)
    nc1 = (Sx + (v1x - Sx) * 2, Sy + (v1y - Sy) * 2)
    nc2 = (Ex + (v2x - Ex) * 2, Ey + (v2y - Ey) * 2)

    curve = Bezier([S, nc1, nc2, E])
    # bounds = PathUtilities.PUBoundsRectangle.fromContour([curve.controlPoints])
    bounds = curve.skeletonBounds

    cp6 = ContourPlotter(bounds.points)
    cp6.drawCurve(curve.controlPoints, colorBlue)
    cp6.drawPointsAsSegments([S, E], colorLightGrey)
    cp6.drawHull(curve, 0.5)
    cp6.drawPointsAsCircles([C], 1)
    cp6.drawPointsAsCircles([B], 2, fill=False)
    cp6.drawPointsAsCircles([A], 1)


    image6 = cp6.generateFinalImage()
    image6File = open("Point Curve Test.svg", "wt", encoding="UTF-8")
    image6File.write(image6)
    image6File.close()

    points = [(70, 120), (90, 200), (150, 200), (170, 120)]

    curve = fitCurveToPoints(points, polygonal=True)
    # bounds = curve.boundsRectangle
    bounds = curve.skeletonBounds
    cp6 = ContourPlotter(bounds.points)
    cp6.drawCurve(curve.controlPoints, colorBlue)
    cp6.drawSkeleton(curve)
    cp6.drawPointsAsCircles(points[1:-1], 2, [colorGreen], fill=False)

    image6 = cp6.generateFinalImage()
    image6File = open("Curve Fitting Test.svg", "wt", encoding="UTF-8")
    image6File.write(image6)
    image6File.close()

    curve = fitCurveToPoints(points, polygonal=False)
    # bounds = curve.boundsRectangle
    bounds = curve.skeletonBounds
    cp6 = ContourPlotter(bounds.points)
    cp6.drawCurve(curve.controlPoints, colorBlue)
    cp6.drawSkeleton(curve)
    cp6.drawPointsAsCircles(points[1:-1], 2, [colorGreen], fill=False)

    image6 = cp6.generateFinalImage()
    image6File = open("Equadistant Curve Fitting Test.svg", "wt", encoding="UTF-8")
    image6File.write(image6)
    image6File.close()

    curvePoints = [(288, 182), (258, 66), (85, 70), (52, 124), (54, 278), (216, 183), (261, 270), (58, 204), (84, 303), (238, 352)]
    testPoints = [(280, 135), (175, 80), (75, 105), (100, 230), (105, 295), (218, 292)]
    pointColors = [colorRed, colorGreen, colorBlue, colorYellow, colorOrange, colorCyan, colorMagenta]
    curve = Bezier(curvePoints)
    bounds = curve.skeletonBounds
    cp = ContourPlotter(bounds.points)
    drawCurve(cp, curve, colorBlue)
    cp.drawSkeleton(curve, lineColor=colorLightBlue, pointColors=pointColors)

    def findClosest(point, LUT):
        x, y = point
        closest = +9007199254740991  # Number.MAX_SAFE_INTEGER
        for index in range(len(LUT)):
            px, py = LUT[index]
            dist = math.hypot(px - x, py - y)
            if dist < closest:
                closest = dist
                i = index

        return i

    """\
      We already know that LUT[i1] and LUT[i2] are *not* good distances,
      so we know that a better distance will be somewhere between them.
      We generate three new points between those two, so we end up with
      five points, and then check which three of those five are a new,
      better, interval to check within.
    """
    def refineBinary(point, curve, LUT, i):
        closest = +9007199254740991  # Number.MAX_SAFE_INTEGER
        steps = len(LUT)
        TT = [t/(steps - 1) for t in range(steps)]
        px, py = point

        for _ in range(25):  # This is for safety; the loop should always break
            steps = len(LUT)
            i1 = 0 if i == 0 else i - 1
            i2 = i if i == steps - 1 else i + 1
            t1 = TT[i1]
            t2 = TT[i2]
            lut = []
            tt = []
            step = (t2 - t1) / 5

            if step < 0.001: break
            lut.append(LUT[i1])
            tt.append(TT[i1])
            for j in range(1, 4):
                nt = t1 + (j * step)
                nx, ny = n = curve.get(nt)
                dist = math.hypot(nx - px, ny - py)
                if dist < closest:
                    closest = dist
                    q = n
                    i = j
                lut.append(n)
                tt.append(nt)
            lut.append(LUT[i2])
            tt.append(TT[i2])

            # update the LUT to be our new five point LUT, and run again.
            LUT = lut
            TT = tt

        return q

    candidateColor = PathUtilities.PUColor(100, 255, 100)
    closestColor = PathUtilities.PUColor(100, 100, 255)

    def projectionTest(point, curve, LUT, cp):
        i = findClosest(testPoint, LUT)
        candidates = [LUT[i]]
        if i > 0: candidates.append(LUT[i - 1])
        if i < len(LUT) - 1: candidates.append(LUT[i + 1])

        cp.drawPointsAsCircles(candidates, 3, [candidateColor])

        for candidate in candidates:
            cp.drawCurve([testPoint, candidate], candidateColor)

        closest = refineBinary(testPoint, curve, LUT, i)
        cp.drawPointsAsCircles([closest], 3, [closestColor])
        cp.drawCurve([testPoint, closest], closestColor)
        cp.drawPointsAsCircles([testPoint], 3, [colorDarkGrey])

    LUT = curve.getLUT(20)

    for testPoint in testPoints:
        projectionTest(testPoint, curve, LUT, cp)

    image = cp.generateFinalImage()
    imageFile = open("Point Projection Test.svg", "wt", encoding="UTF-8")
    imageFile.write(image)
    imageFile.close()

    curve = getDefaultCubic()
    bounds = curve.boundsRectangle

    reduced = curve.reduce()

    offset1 = curve.offset(-20)
    offset2 = curve.offset(20)

    for o in offset1:
        bounds = bounds.union(o.boundsRectangle)

    for o in offset2:
        bounds = bounds.union(o.boundsRectangle)

    cp = ContourPlotter(bounds.points)

    for r in reduced:
        color = PathUtilities.PUColor.randomHSLColor()
        drawCurve(cp, r, color)
        cp.drawPointsAsCircles([r.controlPoints[0]], 2, [color])
    cp.drawPointsAsCircles([reduced[-1].controlPoints[-1]], 2, [color])

    cp.pushStrokeAttributes(opacity=0.3)
    cp.pushFillAttributes(opacity=0.3)

    for o in offset1:
        drawCurve(cp, o, colorRed)
        cp.drawPointsAsCircles([o.controlPoints[0]], 2, [colorRed])
    cp.drawPointsAsCircles([offset1[-1].controlPoints[-1]], 2, [colorRed])

    for o in offset2:
        drawCurve(cp, o, colorBlue)
        cp.drawPointsAsCircles([o.controlPoints[0]], 2, [colorBlue])
    cp.drawPointsAsCircles([offset2[-1].controlPoints[-1]], 2, [colorBlue])

    image = cp.generateFinalImage()
    imageFile = open("Curve Offset Test.svg", "wt", encoding="UTF-8")
    imageFile.write(image)
    imageFile.close()

    def linearDistanceFunction(d, tlen, alen, slen):
        f1 = alen / tlen
        f2 = (alen + slen) / tlen
        return lambda v: butils.map(v, 0, 1, f1 * d, f2 * d)

    def outline(curve, d):
        fcurves = []
        bcurves = []
        bounds = curve.boundsRectangle
        reduced = curve.reduce()
        alen = 0
        tlen = float(curve.length)

        for segment in reduced:
            slen = float(segment.length)
            fc = segment.scale(linearDistanceFunction(-d, tlen, alen, slen))
            bounds = bounds.union(fc.boundsRectangle)
            fcurves.append(fc)

            bc = segment.scale(linearDistanceFunction(d, tlen, alen, slen))
            bounds = bounds.union(bc.boundsRectangle)
            bcurves.append(bc)

            alen += slen

        # JavaScript code does this to enable it to draw
        # fcurves and bcurves as one continuous shape...
        # map(lambda s: s.controlPoints.reverse(), bcurves)
        # bcurves.reverse()
        # fcurves.extend(bcurves)
        return (fcurves, bcurves, bounds)

    curve = getDefaultCubic()
    fcurves, bcurves, bounds = outline(curve, 20)
    cp = ContourPlotter(bounds.points)

    PathUtilities.PUColor.setCurrentHue()
    drawCurve(cp, curve, colorBlue)

    for fc in fcurves:
        drawCurve(cp, fc, colorRed)

    for bc in bcurves:
        drawCurve(cp, bc, colorGreen)

    image = cp.generateFinalImage()
    imageFile = open("Curve Graduated Offset Test.svg", "wt", encoding="UTF-8")
    imageFile.write(image)
    imageFile.close()

    kappa = 0.5519768352769461
    r = 100
    quarterCirclePoints = [(r, 0), (r, kappa * r), (kappa * r, r), (0, r)]
    quarterCircle = Bezier(quarterCirclePoints)
    cp = ContourPlotter((-100, -100, 100, 100))
    cp.drawPointsAsSegments([(0, 100), (0, -100)], colorDarkGrey)
    cp.drawPointsAsSegments([(100, 0), (-100, 0)], colorDarkGrey)
    cp.drawPointsAsCircles([(0, 0)], r, [colorDarkGrey], fill=False)

    cp.pushStrokeAttributes(opacity=0.25)
    drawCurve(cp, quarterCircle, colorRed)

    mirror = PathUtilities.PUTransform.mirror(xAxis=True)
    mpoints = mirror.applyToSegment(quarterCircle.controlPoints)
    c = Bezier(mpoints)
    drawCurve(cp, c, colorGreen)

    mirror = PathUtilities.PUTransform.mirror(xAxis=True, yAxis=True)
    mpoints = mirror.applyToSegment(quarterCircle.controlPoints)
    c = Bezier(mpoints)
    drawCurve(cp, c, colorBlue)

    mirror = PathUtilities.PUTransform.mirror(yAxis=True)
    mpoints = mirror.applyToSegment(quarterCircle.controlPoints)
    c = Bezier(mpoints)
    drawCurve(cp, c, colorCyan)


    image = cp.generateFinalImage()
    imageFile = open("Cubic Circle Test.svg", "wt", encoding="UTF-8")
    imageFile.write(image)
    imageFile.close()

if __name__ == "__main__":
    test()
