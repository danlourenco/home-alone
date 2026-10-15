# fractions along a receding wall from one frame: corners x0,x1 and two equal-width features (projective 1-D map)
import sys
from scipy.optimize import brentq
def solve(x0, x1, A, B):
    s = lambda x, c: (x - x0) / ((x1 * (c + 1) - x0) - c * x)
    f = lambda c: (s(A[1], c) - s(A[0], c)) - (s(B[1], c) - s(B[0], c))
    c = brentq(f, -0.95, 20)
    return c, [round(s(v, c), 3) for v in (*A, *B)]
if __name__ == "__main__":
    v = list(map(float, sys.argv[1:]))
    c, fr = solve(v[0], v[1], v[2:4], v[4:6])
    print("c", round(c, 3), "edges", fr, "centres", round((fr[0]+fr[1])/2, 3), round((fr[2]+fr[3])/2, 3), "widths", round(fr[1]-fr[0], 3))
