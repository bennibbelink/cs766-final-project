import numpy as np
import cv2


def mask_table(bgr_img):
    pixels = []
    for i in bgr_img:
        for j in i:
            pixels.append(j)
    pixels = np.array(pixels)
    bins = [0,100,150,255]
    hist, bins = np.histogramdd(pixels, bins=(bins, bins, bins))

    # find the highest histogram bin
    max_r, max_g, max_b, max_val = 0, 0, 0, 0
    for r in range(hist.shape[0]):
        for g in range(hist.shape[1]):
            for b in range(hist.shape[2]):
                if hist[r][g][b] > max_val:
                    max_val = hist[r][g][b]
                    (max_r, max_g, max_b) = r, g, b
    bins = bins[0]
    lower = np.array([bins[max_r], bins[max_g], bins[max_b]])
    upper = np.array([bins[max_r + 1], bins[max_g + 1], bins[max_b + 1]])
    # just get the pixels in the highest histogram bin
    mask = cv2.inRange(bgr_img, lower, upper)
    # fill in the holes
    kernel = np.ones((7, 7),np.uint8)
    dilation = cv2.dilate(mask, kernel, iterations=10)
    # dilation is grayscale, lets convert it to have three channels
    rgb_dilation = np.uint8(np.zeros((dilation.shape[0], dilation.shape[1], 3)))
    for i in range(rgb_dilation.shape[0]):
        for j in range(rgb_dilation.shape[1]):
            rgb_dilation[i][j][:] = dilation[i][j]

    res = cv2.bitwise_and(bgr_img, rgb_dilation)
    res = cv2.cvtColor(res, cv2.COLOR_BGR2RGB)
    return res


def blur_img(img, iters):
    blurred = img.copy()
    kernelsize = (5,5)
    for i in range(iters):
        blurred = cv2.GaussianBlur(blurred, kernelsize, sigmaX=0, sigmaY=0)
    return blurred


def scharr(img):
    scharr_X = cv2.Scharr(img, cv2.CV_64F, 1, 0)
    scharr_X_abs = np.uint8(np.absolute(scharr_X))
    scharr_Y = cv2.Scharr(img, cv2.CV_64F, 0, 1)
    scharr_Y_abs = np.uint8(np.absolute(scharr_Y))
    scharr_XY_combined = cv2.bitwise_or(scharr_Y_abs,scharr_X_abs)
    return scharr_XY_combined