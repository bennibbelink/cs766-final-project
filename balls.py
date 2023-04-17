import cv2
import table
import numpy as np


class Ball:
    def __init__(self, team, label, loc):
        self.team = team
        self.label = label
        self.loc = loc


def hough_circles(full_img, masked_image, bounds):
    cimg = full_img.copy()
    if len(masked_image.shape) > 2:
        gray = cv2.cvtColor(masked_image, cv2.COLOR_RGB2GRAY)
    else:
        gray = masked_image
    alt = False
    if alt:
        h_circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT_ALT, param1=300, param2=0.5, dp=1, minRadius=14,
                                     maxRadius=16, minDist=1)
    else:
        h_circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, param1=80, param2=8, dp=1, minRadius=12, maxRadius=15,
                                     minDist=1)
    if h_circles is None:
        print("no circles found")
        return []
    h_circles = np.uint16(np.around(h_circles))

    k = 0
    for i in h_circles[0, :]:
        # draw the outer circle
        cv2.circle(cimg, (i[0], i[1]), i[2], (0, 255, 0), 2)
        # draw the center of the circle
        cv2.circle(cimg, (i[0], i[1]), 2, (0, 0, 255), 3)
        cv2.putText(cimg, f'{k}', (i[0], i[1]), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 1)
        k += 1

    cluster_centers = table.find_clusters(h_circles, 16, 15, cimg, bounds=bounds)
    ball_centers_img = full_img.copy()
    for c in cluster_centers:
        cv2.circle(ball_centers_img, (c[0], c[1]), 4, (255, 0, 255), 5)
        cv2.circle(ball_centers_img, (c[0], c[1]), 2 * c[2], (0, 255, 0), 1)
    cv2.imwrite('ball_centers.png', ball_centers_img)
    return cluster_centers


def label_balls(color_img, hough_circs):
    ## get the pixel values of all the circles
    balls = []
    num_solids = 0
    num_stripes = 0
    if len(hough_circs) == 0:
        return balls
    for circle in hough_circs:
        rad = circle[2]
        center_x = circle[1]
        center_y = circle[0]
        # iterate over the box containing the circle, and extend it a bit since our circles arent perfect
        pixels = []
        for i in range(4*rad):
            for j in range(4*rad):
                tmp_x = round(center_x - 2*rad + i)
                tmp_y = round(center_y - 2*rad + j)
                # check that the point is actually in the circle
                if np.power(tmp_x - center_x, 2) + np.power(tmp_y - center_y, 2) < np.power(rad, 2):
                    pix = color_img[tmp_x][tmp_y]
                    pixels.append(pix)
        pixels = np.array(pixels)
        hist, bins = np.histogramdd(pixels, bins=(3, 3, 3), density=False)
        if hist[0,0,0] > 375: # eight ball
            balls.append(Ball(team=None, label="eight", loc=(center_y, center_x)))
        elif hist[2,2,2] > 300: # cue ball
            balls.append(Ball(team=None, label="cue", loc=(center_y, center_x)))
        elif hist[0,0,0] > 310 or np.sum(hist[1]) > 300: # solids
            balls.append(Ball(team="solids", label=str(num_solids), loc=(center_y, center_x)))
            num_solids += 1
        elif hist[2,2,2] > 10: # stripes
            balls.append(Ball(team="stripes", label=str(num_stripes), loc=(center_y, center_x)))
            num_stripes += 1
        elif np.sum(hist) - hist[0,0,0] - hist[2,2,2] > 200:
            balls.append(Ball(team="solids", label=str(num_solids), loc=(center_y, center_x)))
            num_solids += 1
        else:
            balls.append(Ball(team=None, label="unlabeled", loc=(center_y, center_x)))

    labeled_balls = color_img.copy()
    for b in balls:
        if b.team == 'solids': col = (0,255,0)
        if b.team == 'stripes': col = (255,0,255)
        if b.team is None: col = (255, 150, 0)
        cv2.putText(labeled_balls, b.team if b.team else b.label, (b.loc[0],b.loc[1]), cv2.FONT_HERSHEY_PLAIN, 2, col, 2)
        cv2.circle(labeled_balls,(b.loc[0],b.loc[1]),3,col,3)

    cv2.imwrite("labels.png", labeled_balls)
    return balls
