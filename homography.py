import numpy as np
import scipy.sparse.linalg as sla
import warnings
warnings.filterwarnings('ignore')  # for annoying complex number warnings


def compute_homography(src_pts, dest_pts):
    np_src = np.array(src_pts)
    np_dest = np.array(dest_pts)
    # construct A
    A = np.zeros((len(src_pts[:]) * 2, 9))
    A[0::2, 2] = 1
    A[1::2, 5] = 1
    A[0::2, 0:2] = np_src
    A[1::2, 3:5] = np_src
    A[0::2, 6] = - np_dest[:, 0] * np_src[:, 0]
    A[1::2 ,6] = - np_dest[:, 1] * np_src[:, 0]
    A[0::2, 7] = - np_dest[:, 0] * np_src[:, 1]
    A[1::2, 7] = - np_dest[:, 1] * np_src[:, 1]
    A[0::2, 8] = - np_dest[:, 0]
    A[1::2, 8] = - np_dest[:, 1]
    w, v = sla.eigs(A.T @ A, 1, which="SR")
    return np.reshape(v, (3, 3))


def apply_homography(H, src_pts):
    np_src = np.array(src_pts)
    dest_pts = np.zeros(np_src.shape)
    for i in range(len(np_src)):
        pt = np_src[i, :]
        vec = np.zeros((3, ))
        vec[0:2] = pt.T
        vec[2] = 1
        d = H @ vec
        dest_pts[i, :] = d[0:2] / d[2]
    return dest_pts
