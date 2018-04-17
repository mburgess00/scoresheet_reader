from imutils.perspective import four_point_transform
from imutils import contours
import numpy as np
import argparse
import imutils
import cv2
import pyzbar.pyzbar as pyzbar

debug = False

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True, help="path to the input image")
args = vars(ap.parse_args())

image = cv2.imread(args["image"])
scaled = imutils.resize(image, height=1000)
qrs = pyzbar.decode(scaled)
qrcode = ""
if len(qrs) > 0:
    qrcode = qrs[0].data

(h, w) = scaled.shape[:2]
h2 = int(h * .85)
w2 = int(w * .65)
cropped = scaled[h2:h, w2:w]
gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
edged = cv2.Canny(blurred, 75, 200)

cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = cnts[0] if imutils.is_cv2() else cnts[1]

if len(cnts) > 0:
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            docCnt = approx
            break

paper = four_point_transform(image, docCnt.reshape(4, 2))
warped = four_point_transform(gray, docCnt.reshape(4, 2))

thresh = cv2.threshold(warped, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = cnts[0] if imutils.is_cv2() else cnts[1]

questionCnts = []

for c in cnts:
    (x, y, w, h) = cv2.boundingRect(c)
    ar = w / float(h)
    if debug:
        print str(x) + "," + str(y) + ": " + str(w) + "x" + str(h) + " " + str(ar)

    if w >= 10 and h >= 10 and ar >= 0.9 and ar <= 1.1:
        if debug:
            print "found a bubble"
        questionCnts.append(c)

if debug:
    print "found " + str(len(questionCnts)) + " bubbles"

questionCnts = contours.sort_contours(questionCnts, method="top-to-bottom")[0]
firstdigit = contours.sort_contours(questionCnts[:6])[0]
seconddigit = contours.sort_contours(questionCnts[6:])[0]

for (q, i) in enumerate(np.arange(0, 6, 6)):
        firstdigitsort = contours.sort_contours(firstdigit[i:i+6])[0]

for (q, i) in enumerate(np.arange(0, 10, 10)):
        seconddigitsort = contours.sort_contours(seconddigit[i:i+10])[0]

notdetected = False

bubbled = None
totalpixels = 0
pixelcount = []
for (j, c) in enumerate(firstdigitsort):
    mask = np.zeros(thresh.shape, dtype="uint8")
    cv2.drawContours(mask, [c], -1, 255, -1)
    mask = cv2.bitwise_and(thresh, thresh, mask=mask)
    total = cv2.countNonZero(mask)
    totalpixels += total
    pixelcount.append(total)
    if bubbled is None or total > bubbled[0]:
        bubbled = (total, j)

avgpixels = totalpixels / float(6)
threshold = avgpixels * 1.5
first = str(bubbled[1])
nummatches=0
if debug:
    print "First Digit Thresholds:"
for i, value in enumerate(pixelcount):
    if debug: 
        print pixelcount[i]
    if pixelcount[i] > threshold:
        nummatches += 1
if bubbled[0] <= threshold:
    notdetected = True
    if debug:
       print "First Digit: found no bubbles over threshold of " + str(threshold)
if nummatches > 1:
    notdetected = True
    if debug:
       print "First Digit: found " + str(nummatches) + " of bubbles over threshold of " + str(threshold)




bubbled = None
totalpixels = 0
pixelcount = []
for (j, c) in enumerate(seconddigitsort):
    mask = np.zeros(thresh.shape, dtype="uint8")
    cv2.drawContours(mask, [c], -1, 255, -1)
    mask = cv2.bitwise_and(thresh, thresh, mask=mask)
    total = cv2.countNonZero(mask)
    totalpixels += total
    pixelcount.append(total)
    if bubbled is None or total > bubbled[0]:
        bubbled = (total, j)

avgpixels = totalpixels / float(10)
threshold = avgpixels * 1.5
second = str(bubbled[1])
nummatches=0
if debug:
    print "Second Digit Thresholds:"
for i, value in enumerate(pixelcount):
    if debug: 
        print pixelcount[i]
    if pixelcount[i] > threshold:
        nummatches += 1
if bubbled[0] <= threshold:
    notdetected = True
    if debug:
       print "Second Digit: found no bubbles over threshold of " + str(threshold)
if nummatches > 1:
    notdetected = True
    if debug:
       print "Second Digit: found " + str(nummatches) + " of bubbles over threshold of " + str(threshold)

print qrcode
if not notdetected:
    print first + second
