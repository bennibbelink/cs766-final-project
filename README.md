# cs766-final-project
Final project for CS 766 Computer Vision

[Summary page](https://bennibbelink.github.io/cs766-final-project/)

## Assumptions
- all balls are on the table (16 total)

## Notes
Right now it is very fragile, really only works well on IMG_2737.  It took a lot of manual tuning to get the
circle transforms to work correctly as well as the ball labeling (using histograms)

The pipeline looks something like this:
1. Mask the image using a histogram (and some morphological processing) to extract mainly just the pool table
2. Apply a circle hough transform to find circles the size of pockets
    - Then find clusters of circles and take the top 4, these are the corner pockets
    - Find the centroid of each cluster and this is what we use as the corner
    - Its not perfect but it seemed like a better strategy than using hough line transforms and finding intersections (shadows make it hard)
3. Once again apply a circle hough transform, this time to find circles the size of balls
    - We use the same clustering technique, only this time using the corners of the table as a bounding box (with some padding). This is necessary since our maskinig isnt perfect, some circles may show up in the background (or the pockets again, hence the padding)
    - Find the centroid of each cluster, thats our ball. This is very imperfect.  The shadows were once again making it very difficult to develop a robust solution, so in many cases the cluster includes circles from a ball and its respective shadows.  This causes the centroids to likely be inaccurate
4. Use a bounding circle for each ball found (twice the radius, because of the shadow making our centers off) and apply a 3D histogram of the pixel values in the bounding circle.  Then it took some playing around with different logic/thresholds to make it label the balls correctly.  This part is very fragile, a little hacky
5. Using the corners of the table we found and the corner coordinates we will use in our physics engine, we compute a homography to map points from the image into our physics coordinate system
