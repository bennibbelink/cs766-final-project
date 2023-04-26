import cv2
import processing
import table
import balls
import numpy as np


def get_balls(LL, UL, LR, UR):
    image_path = "./images/IMG_2737.png"
    color = cv2.imread(image_path, 1)
    masked_img = processing.mask_table(color)
    corners = [(c[0], c[1]) for c in table.get_corners(masked_img=masked_img)]
    blurred_img = processing.blur_img(masked_img, iters=9)
    sch = processing.scharr(blurred_img)
    circles = balls.hough_circles(color, sch, bounds=corners)
    bls = balls.label_balls(color, circles)
    # the src_corners are in order of TL, TR, BL, BR
    src_corners = np.float32(np.array(corners))
    # the dst_corners are the coordinates according to our physics engine
    dst_corners = np.float32(np.array([(70, 510), (70, 70), (986, 510), (986, 70)]))
    M = cv2.getPerspectiveTransform(src_corners, dst_corners)
    src_balls = np.array([ball.loc for ball in bls])
    src_balls = np.array([src_balls], np.float32)
    dest_balls = cv2.perspectiveTransform(src_balls, M)
    warped_img = cv2.warpPerspective(color, M, (1100, 600), flags=cv2.INTER_LINEAR)
    cv2.imwrite("warped_img.png", warped_img)
    for i in range(len(bls)):
        bls[i].loc = dest_balls[0, i]

    # THESE BALLS HAVE ALREADY BEEN MAPPED TO THE PHYSICS COORDINATE SPACE
    return bls
