#!/usr/bin/env python3

from PIL import Image
from scipy.fftpack import rfft
import tempfile
import os
import subprocess


NW = 420
NH = 594
BASELINE_ZONE = (0.15, 0.33)
OMIT_THIN_DISTANCE = 10 # 5mm

def normalizedSequence(lst):
    maxV, minV = max(lst), min(lst)
    return [(i - minV) / (maxV - minV) for i in lst]

def diffRiseDropFilter(lst, riseThreshold=0.2, dropThreshold=-0.2):
    s, e = -1, -1
    ret = []
    v0 = lst[0]
    for i in range(1, len(lst)):
        v = lst[i]
        d = v - v0
        if d >= riseThreshold:
            s = i
        elif d <= dropThreshold:
            if s >= 0:
                e = i
                ret.append((s, e))
                s, e = -1, -1
        v0 = v
    return [int((a+b)/2) for a,b in ret]


def schmittRiseDropFilter(lst, riseThreshold=0.2, dropThreshold=0.2):
    s, e = -1, -1
    ret = []
    for i in range(0, len(lst)):
        v = lst[i]
        if s < 0:
            if v >= riseThreshold:
                s = i
        else:
            if v <= dropThreshold:
                e = i
                ret.append((s, e))
                s, e = -1, -1
    return [int((a+b)/2) for a,b in ret]

def findBaseline(image):
    global NH, NW, BASELINE_ZONE

    h1, h2 = int(NH * BASELINE_ZONE[0]), int(NH * BASELINE_ZONE[1])
    zone = image.crop((0, h1, NW, h2))
    zoneW, zoneH = zone.size
    data = list(zone.getdata())

    ffts = []

    for h in range(0, zoneH):
        lineData = data[h*zoneW:][:zoneW]
        fftRet = rfft(lineData, n=20)
        ffts.append(fftRet)
    
    finder = normalizedSequence([max(i[10:]) for i in ffts])
    lines = diffRiseDropFilter(finder, riseThreshold=0.2, dropThreshold=-0.2)

    return int(lines[0] + h1)

def _filterBinaryImageAndGetLines(img, constrastThreshold, filterFunc):
    data = list(img.getdata())
    w, h = img.size
    lineAvg = [0] * h 
    for i in range(0, h):
        row = "".join([
            i > constrastThreshold and "1" or " "
            for i in data[i*w:][:w]
        ]).strip()
        if row:
            lineAvg[i] = row.count("1") / len(row)
    lineAvg = normalizedSequence(lineAvg)
    return filterFunc(lineAvg)
    


def findRowCutLines(nImage, nBaselineY, constrastThreshold=128, threshold=0.2):
    nImageW, nImageH = nImage.size
    nImageBody = nImage.crop((0, nBaselineY, nImageW, nImageH))
#    filterFunc = lambda a: diffRiseDropFilter(a, riseThreshold=threshold, dropThreshold=threshold)
    filterFunc = lambda a: schmittRiseDropFilter(a, riseThreshold=threshold, dropThreshold=threshold)
    lines = _filterBinaryImageAndGetLines(nImageBody, constrastThreshold, filterFunc)
    return [i + nBaselineY for i in lines]

def findColumnCutLines(
    nImage, nRowCutLineY1, nRowCutLineY2, constrastThreshold=128, threshold=0.9
):
    nImageW, nImageH = nImage.size
    nRowCutLineYmin = min(nRowCutLineY1, nRowCutLineY2)
    nRowCutLineYmax = max(nRowCutLineY1, nRowCutLineY2)
    nImageRow = nImage.crop((0, nRowCutLineYmin, nImageW, nRowCutLineYmax))

    nImageRotated = nImageRow.transpose(Image.ROTATE_270)
    filterFunc = lambda a: schmittRiseDropFilter(a, riseThreshold=threshold, dropThreshold=threshold)
    columns = _filterBinaryImageAndGetLines(nImageRotated, constrastThreshold, filterFunc)
    return columns

def normalizeImage(image):
    global NW, NH
    w, h = image.size
    return image.resize((NW, NH), Image.ANTIALIAS), (NW/w, NH/h)

def enlargeImage(image):
    # create a 2x so large image with original pasted in center and margins
    # white
    w, h = image.size
    W, H = 2 * w, 2 * h
    ret = Image.new("L", (W, H), 255)
    ret.paste(image, (int(w / 2), int(h / 2)))
    return ret

def cropQRCodeAndRecognize(rImage, boundaries):
    w, h = rImage.size
    l, t, r, b = boundaries
    ext = 4
    l -= ext
    t -= ext
    r += ext
    b += ext
    if l < 0: l = 0
    if t < 0: t = 0
    if r > w: r = w
    if b > h: b = h
    img = rImage.crop((l, t, r, b))

    tempdir = tempfile.gettempdir()
    filename = "nddpef-%s.png" % os.urandom(16).hex()
    fullpath = os.path.join(tempdir, filename)

    enlargeImage(img).save(fullpath)
    try:
        data = subprocess.check_output(["zbarimg", "--raw", "-q", fullpath])
    except:
        data = None

    #os.unlink(fullpath)
    return data




##############################################################################

def scan(filename, threshold=80):
    global OMIT_THIN_DISTANCE

    rImage = Image.open(filename).convert("L")
    rImageW, rImageH = rImage.size
    nImage, nRatio = normalizeImage(rImage)
    nRatioW, nRatioH = nRatio
    nImageW, nImageH = nImage.size

    nBaselineY = findBaseline(nImage) # Y of baseline in normalized image
    if not nBaselineY: return None
    rBaselineY = int(nBaselineY / nRatioH)

    rImageMetadata = rImage.crop((0, 0, rImageW, rBaselineY))
    rImageBody = rImage.crop((0, rBaselineY, rImageW, rImageH))

    # find cut lines for image body
    nRowCutLines = findRowCutLines(nImage, nBaselineY, threshold=0.8)
    nRowCutLines += [nBaselineY, nImageH]
    nRowCutLines.sort()

    print("Row cut:", [int(i / nRatioH) for i in nRowCutLines])

    for i in range(1, len(nRowCutLines)): # cut nImage into rows
        nYmin, nYmax = nRowCutLines[i-1], nRowCutLines[i]
        if nYmax - nYmin < OMIT_THIN_DISTANCE: continue
        nColumnCutLines = findColumnCutLines(
            nImage, nRowCutLines[i-1], nRowCutLines[i], # from row cut line 1-2
            constrastThreshold=128, threshold=0.9
        )
        nColumnCutLines += [0, nImageW]
        nColumnCutLines.sort()

        for j in range(1, len(nColumnCutLines)):
            nXmin, nXmax = nColumnCutLines[j-1], nColumnCutLines[j]
            if nXmax - nXmin < OMIT_THIN_DISTANCE: continue

            rXmin, rXmax = int(nXmin / nRatioW), int(nXmax / nRatioW)
            rYmin, rYmax = int(nYmin / nRatioH), int(nYmax / nRatioH)

            ret = cropQRCodeAndRecognize(rImage, (rXmin, rYmin, rXmax, rYmax))
            if ret:
                yield ret




if __name__ == "__main__":
    import sys
    count = 0
    for each in scan(sys.argv[1]):
        print(each)
        count += 1
    
    print("\n")
    print("%d pieces found." % count)
