"""\
Utilities for bézier curves

Created on August 30, 2020

Much of this code translated from bezier.js, utils.js and others
from https://github.com/Pomax/BezierInfo-2

@author Eric Mader
"""

import math
from decimal import Decimal

# Legendre-Gauss abscissae with n=24 (x_i values, defined at i=n as the roots of the nth order Legendre polynomial Pn(x))
tValues = [
    Decimal("-0.0640568928626056260850430826247450385909"),
    Decimal("0.0640568928626056260850430826247450385909"),
    Decimal("-0.1911188674736163091586398207570696318404"),
    Decimal("0.1911188674736163091586398207570696318404"),
    Decimal("-0.3150426796961633743867932913198102407864"),
    Decimal("0.3150426796961633743867932913198102407864"),
    Decimal("-0.4337935076260451384870842319133497124524"),
    Decimal("0.4337935076260451384870842319133497124524"),
    Decimal("-0.5454214713888395356583756172183723700107"),
    Decimal("0.5454214713888395356583756172183723700107"),
    Decimal("-0.6480936519369755692524957869107476266696"),
    Decimal("0.6480936519369755692524957869107476266696"),
    Decimal("-0.7401241915785543642438281030999784255232"),
    Decimal("0.7401241915785543642438281030999784255232"),
    Decimal("-0.8200019859739029219539498726697452080761"),
    Decimal("0.8200019859739029219539498726697452080761"),
    Decimal("-0.8864155270044010342131543419821967550873"),
    Decimal("0.8864155270044010342131543419821967550873"),
    Decimal("-0.9382745520027327585236490017087214496548"),
    Decimal("0.9382745520027327585236490017087214496548"),
    Decimal("-0.9747285559713094981983919930081690617411"),
    Decimal("0.9747285559713094981983919930081690617411"),
    Decimal("-0.9951872199970213601799974097007368118745"),
    Decimal("0.9951872199970213601799974097007368118745"),
]

# Legendre-Gauss weights with n=24 (w_i values, defined by a function linked to in the Bezier primer article)
cValues = [
    Decimal("0.1279381953467521569740561652246953718517"),
    Decimal("0.1279381953467521569740561652246953718517"),
    Decimal("0.1258374563468282961213753825111836887264"),
    Decimal("0.1258374563468282961213753825111836887264"),
    Decimal("0.121670472927803391204463153476262425607"),
    Decimal("0.121670472927803391204463153476262425607"),
    Decimal("0.1155056680537256013533444839067835598622"),
    Decimal("0.1155056680537256013533444839067835598622"),
    Decimal("0.1074442701159656347825773424466062227946"),
    Decimal("0.1074442701159656347825773424466062227946"),
    Decimal("0.0976186521041138882698806644642471544279"),
    Decimal("0.0976186521041138882698806644642471544279"),
    Decimal("0.086190161531953275917185202983742667185"),
    Decimal("0.086190161531953275917185202983742667185"),
    Decimal("0.0733464814110803057340336152531165181193"),
    Decimal("0.0733464814110803057340336152531165181193"),
    Decimal("0.0592985849154367807463677585001085845412"),
    Decimal("0.0592985849154367807463677585001085845412"),
    Decimal("0.0442774388174198061686027482113382288593"),
    Decimal("0.0442774388174198061686027482113382288593"),
    Decimal("0.0285313886289336631813078159518782864491"),
    Decimal("0.0285313886289336631813078159518782864491"),
    Decimal("0.0123412297999871995468056670700372915759"),
    Decimal("0.0123412297999871995468056670700372915759"),
]

# float precision significant decimal
epsilon = 0.000001

# trig constants
pi = math.pi
tau = math.tau
quart = pi / 4


def approximately(a, b, precision=epsilon):
    """Return True if a is approximately equal to b (within the given precision)"""
    return abs(a - b) <= precision

def between(v, m, M):
    return m <= v <= M or (approximately(v, m) or approximately(v, M))

def sqrt(x):
    try:
        r = math.sqrt(x)
    except:
        # JavaScript sqrt() returns NaN for negative x.
        # If we do the same, then the rest of the code
        # will behave as the JavaScript code does...
        r = math.nan

    return r

def crt(v):
    """Return the cube root of v"""
    return -math.pow(-v, 1 / 3) if v < 0 else math.pow(v, 1 / 3)

def removeDuplicates(l):
    """Return a list that is l with the duplicate entries removed."""

    #The JavaScript idiom for this is:
    # results = results.filter(function (v, i) {
    #   return results.indexOf(v) === i;
    # });

    # This can't be done like this in Python because the filter callback
    # only takes one argument. So, we have to do it by hand.

    result = []
    for i in range(len(l)):
        v = l[i]
        if l.index(v) == i:
            result.append(v)

    return result

def lli8(x1, y1, x2, y2, x3, y3, x4, y4):
    nx = (x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)
    ny = (x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)
    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

    # d == 0 means that the lines are parallel
    if d == 0: return None

    return (nx / d, ny / d)


def lli4(p1, p2, p3, p4):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    return lli8(x1, y1, x2, y2, x3, y3, x4, y4)


def lli(l1, l2):
    return lli4(l1[0], l1[1], l2[0], l2[1])


def droots(p):
    # quadratic roots are easy
    if len(p) == 3:
        a = p[0]
        b = p[1]
        c = p[2]
        d = a - 2 * b + c

        if d != 0:
            m1 = - sqrt(b * b - a * c)
            m2 = -a + b
            v1 = -(m1 + m2) / d
            v2 = -(-m1 + m2) / d
            return [v1, v2]

        if b != c and d == 0:
            return [(2 * b - c) / (2 * (b - c))]

        return []

    # linear roots are even easier
    if len(p) == 2:
        a = p[0]
        b = p[1]

        if a != b:
            return [a / (a - b)]

    return []


def lerp(r, v1, v2):
    """"Linear intrpolation between v1, v2"""
    v1x, v1y = v1
    v2x, v2y = v2
    return (v1x + r * (v2x - v1x), v1y + r * (v2y - v1y))

def quadraticRatio(t):
    t2 = 2 * t
    top = t2 * t - t2
    bottom = top + 1
    return abs(top / bottom)

def cubicRatio(t):
    mt = (1 - t)
    t3 = t * t * t
    mt3 = mt * mt * mt
    bottom = t3 + mt3
    top = bottom - 1
    return abs(top / bottom)

def map(v, ds, de, ts, te):
    """\
    Map the value v, in range [ds, de] to
    the corresponding value in range [ts, te]
    """
    d1 = de - ds
    d2 = te - ts
    v2 = v - ds
    r = v2 / d1

    return ts + d2 * r

def angle(o, v1, v2):
    ox, oy = o
    v1x, v1y = v1
    v2x, v2y = v2
    dx1 = v1x - ox
    dy1 = v1y - oy
    dx2 = v2x - ox
    dy2 = v2y - oy
    cross = dx1 * dy2 - dy1 * dx2
    dot = dx1 * dx2 + dy1 * dy2

    return math.atan2(cross, dot)

def pairiteration(c1, c2, intersectionThreshold=0.5):
    c1b = c1.boundsRectangle
    c2b = c2.boundsRectangle
    r = 100000

    if c1b.height + c1b.width < intersectionThreshold and c2b.height + c2b.width < intersectionThreshold:
        return [(((r * (c1._t1 + c1._t2)) / 2) / r, ((r * (c2._t1 + c2._t2)) / 2) / r)]

    cc1left, cc1right, _ = c1.split(0.5)
    cc2left, cc2right, _ = c2.split(0.5)
    pairs = [(cc1left, cc2left), (cc1left, cc2right), (cc1right, cc2right), (cc1right, cc2left)]
    pairs = list(filter(lambda pair: pair[0].overlaps(pair[1]), pairs))

    results = []
    if len(pairs) == 0: return results

    for pair in pairs:
        left, right = pair
        results.extend(pairiteration(left, right, intersectionThreshold))

    return removeDuplicates(results)

def test():
    print("No tests...")

if __name__ == "__main__":
    test()
