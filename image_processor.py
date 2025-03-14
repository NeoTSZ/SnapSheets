# Import modules/packages.
import cv2 as cv
from matplotlib import pyplot as plt
import numpy as np

def processImage(image):
    # Original image
    image = cv.cvtColor(image, cv.COLOR_BGR2RGB)

    # Grayscale image
    gray = cv.cvtColor(image, cv.COLOR_RGB2GRAY)

    # Threshold image
    _, thresholded = cv.threshold(
        gray,
        0,
        255,
        cv.THRESH_BINARY + cv.THRESH_OTSU
    )

    # Getting contours.
    contours, _ = cv.findContours(
        thresholded,
        cv.RETR_EXTERNAL,
        cv.CHAIN_APPROX_SIMPLE
    )
    minValidArea = int((image.shape[0] * image.shape[1]) / 4)
    validContours = []
    for contour in contours:
        if cv.contourArea(contour) > minValidArea:
            validContours.append(contour)

    # Refining and drawing contours.
    contoured = image.copy()
    refiningScalar = 2
    isRectangle = False
    pageBox = []
    while isRectangle == False:
        # This loop is repeated until a rectangular shape is found.
        refiningScalar = refiningScalar * 0.5
        if refiningScalar < 0.0001:
            return {
                'original': image,
                'contours': False,
                'straight': False
            }
        for contour in validContours:
            approxPolygon = cv.approxPolyDP(
                contour,
                refiningScalar * cv.arcLength(contour, True),
                True
            )

            # Checking if a closed, 4-sided polygon was detected.
            if len(approxPolygon) == 4:
                # Drawing a rectangular contour upon success.
                isRectangle = True
                pageBox = approxPolygon
                cv.drawContours(
                    contoured,
                    [approxPolygon],
                    -1,
                    (255, 0, 255),
                    4
                )
                break

    # Ordering the corners.
    pageCorners = pageBox.reshape(4, 2)
    for i in range(4):
        for j in range(3):
            if pageCorners[j][1] > pageCorners[j + 1][1]:
                temp = pageCorners[j].copy()
                pageCorners[j] = pageCorners[j + 1].copy()
                pageCorners[j + 1] = temp.copy()
    if pageCorners[0][0] > pageCorners[1][0]:
        temp = pageCorners[0]
        pageCorners[0] = pageCorners[1]
        pageCorners[1] = temp
    if pageCorners[2][0] > pageCorners[3][0]:
        temp = pageCorners[2]
        pageCorners[2] = pageCorners[3]
        pageCorners[3] = temp
    pageCorners = np.array(pageCorners, dtype='float32')

    # Setting the target dimensions.
    paperRatio = 1.41 # A4 Standard
    targetWidth = 720
    targetHeight = int(1.41 * 720)
    targetCorners = np.array(
        [
            [0, 0],
            [targetWidth, 0],
            [0, targetHeight],
            [targetWidth, targetHeight]
        ],
        dtype='float32'
    )

    # Warping the image to straighten it out.
    warpingMatrix = cv.getPerspectiveTransform(pageCorners, targetCorners)
    warped = cv.warpPerspective(image, warpingMatrix, (targetWidth, targetHeight))

    return {
        'original': image,
        'contours': contoured,
        'straight': warped
    }