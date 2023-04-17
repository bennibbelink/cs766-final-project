import cv2
import math
import statistics
import processing
import numpy as np


def find_clusters(circles, num_clusters, dist_threshold, img, bounds=[]):
    if len(bounds) != 0:
        bounds = np.array(bounds)
        min_x = min(bounds[:, 0])
        min_y = min(bounds[:, 1])
        max_x = max(bounds[:, 0])
        max_y = max(bounds[:, 1])
    clusters = []
    for i in circles[0, :]:
        in_bounds = False
        if len(bounds) == 0:
            in_bounds = True
        # this padding of 12 pixels is so that the side pockets don't get included
        elif len(bounds) > 0 and min_x + 12 <= i[0] <= max_x - 12 and min_y + 12 <= i[1] <= max_y - 12:
            in_bounds = True
        if in_bounds:
            found_cluster = False
            for cluster in clusters:
                for circ in cluster:
                    if math.dist((circ[0], circ[1]), (i[0], i[1])) < dist_threshold:
                        cluster.append(i)
                        found_cluster = True
                    if found_cluster: break
                if found_cluster: break
            if not found_cluster:
                clusters.append([i])
    if len(clusters) < num_clusters:
        raise "not enough clusters found"

    # find the n biggest clusters, these are (hopefully) our corner pockets
    clusters.sort(reverse=True, key=len)
    cluster_centers = []
    out_img = img.copy()
    for cluster in clusters[0:num_clusters]:
        xes = []
        yes = []
        radii = []
        for i in cluster:
            xes.append(i[0])
            yes.append(i[1])
            radii.append(i[2])
            cv2.circle(out_img, (i[0], i[1]), i[2], (255, 0, 255), 2)  # draw the outer circle
            cv2.circle(out_img, (i[0], i[1]), 2, (0, 255, 0), 3)  # draw the center of the circle
        cluster_centers.append((statistics.mean(xes), statistics.mean(yes), statistics.mean(radii)))
    if len(bounds) == 0:
        cv2.imwrite("table_clusters.png", out_img)
    else:
        cv2.imwrite("ball_clusters.png", out_img)
    return cluster_centers


def get_corners(masked_img):
    msk_img = masked_img.copy()
    img_blur = processing.blur_img(msk_img, 9)
    gray_blur = cv2.cvtColor(img_blur, cv2.COLOR_RGB2GRAY)
    h_circles = cv2.HoughCircles(gray_blur, cv2.HOUGH_GRADIENT, param1=120, param2=12, dp=1, minRadius=25, maxRadius=30,
                                 minDist=1)
    h_circles = np.uint16(np.around(h_circles))
    msk_img = cv2.cvtColor(msk_img, cv2.COLOR_BGR2RGB)
    for i in h_circles[0, :]:
        cv2.circle(msk_img, (i[0], i[1]), i[2], (0, 255, 0), 2)  # draw the outer circle
        cv2.circle(msk_img, (i[0], i[1]), 2, (0, 0, 255), 3)  # draw the center of the circle

    # construct clusters of the hough circles
    cluster_centers = find_clusters(h_circles, 4, 15, msk_img)
    corners_img = masked_img.copy()
    corners_img = cv2.cvtColor(corners_img, cv2.COLOR_BGR2RGB)
    for c in cluster_centers:
        cv2.circle(corners_img, (c[0], c[1]), 4, (255, 0, 255), 5)
    cv2.imwrite('table_corners.png', corners_img)
    return organize(cluster_centers)


# reorders the corners so that they are TL, TR, BL, BR
def organize(pts):
    def by_x(a): # remember that x is vertical direction, origin is top left
        return a[0]

    def by_y(a): # remember that y is horizontal
        return a[1]

    # find top
    pts.sort(key=by_x)
    left = pts[:2]
    left.sort(key=by_y)
    TL = left[0]
    BL = left[1]
    # find bottom
    right = pts[2:]
    right.sort(key=by_y)
    TR = right[0]
    BR = right[1]
    return TL, TR, BL, BR
