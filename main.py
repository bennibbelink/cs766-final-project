import cv2
import processing
import homography
import table
import balls


def main():
    image_path = "./images/IMG_2737.png"
    color = cv2.imread(image_path, 1)
    masked_img = processing.mask_table(color)
    corners = [(c[0], c[1]) for c in table.get_corners(masked_img=masked_img)]
    blurred_img = processing.blur_img(masked_img, iters=9)
    sch = processing.scharr(blurred_img)
    circles = balls.hough_circles(color, sch, bounds=corners)
    bls = balls.label_balls(color, circles)
    # the corners are in order of TL, TR, BL, BR
    H = homography.compute_homography(corners, [(0, 0), (0, 100), (50, 0), (50, 100)])  # RIGHT NOW THIS IS A FAKE DEST
    src_balls = [ball.loc for ball in bls]
    dest_balls = homography.apply_homography(H, src_balls)
    for i in range(len(bls)):
        bls[i].loc = dest_balls[i]

    # this bls array should be ready to go into the physics engine
    # (assuming the dest pts are fixed for the homography)


if __name__ == "__main__":
    main()
