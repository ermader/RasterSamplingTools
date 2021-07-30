"""\
Matrix inversion

Created on September 9, 2020

Translated from http://blog.acipo.com/matrix-inversion-in-javascript/

@author Eric Mader
"""

def matrixInvert(M):
    """\
    Returns the inverse of matrix `M`.

    I use Guassian Elimination to calculate the inverse:
    (1) 'augment' the matrix (left) by the identity (on the right)
    (2) Turn the matrix on the left into the identity by elemetry row ops
    (3) The matrix on the right is the inverse (was the identity matrix)
    There are 3 elemtary row ops: (I combine b and c in my code)
    (a) Swap 2 rows
    (b) Multiply a row by a scalar
    (c) Add 2 rows
    """

    # If the matrix isn't square, return None
    if len(M) != len(M[0]): return None

    # create the identity matrix (I), and a copy (C) of the original
    n = len(M)
    I = []
    C = []

    for row in range(n):
        iRow = []
        cRow = []

        for col in range(n):
            iRow.append(1 if row == col else 0)  # 1 if on diagonal, else 0
            cRow.append(M[row][col])  # copy from the original

        I.append(iRow)
        C.append(cRow)

    # Perform elementary row operations
    for i in range(n):
        # get the element e on the diagonal
        e = C[i][i]

        # if we have a 0 on the diagonal (we'll need to swap with a lower row)
        if e == 0:
            # look through every row below the i'th row
            for ii in range(i+1, n):
                # if the ii'th row has a non-0 in the i'th col
                if C[ii][i] != 0:
                    # it would make the diagonal have a non-0 so swap it
                    for j in range(n):
                        e = C[i][j]  # temp store i'th row
                        C[i][j] = C[ii][j]  # replace i'th row by ii'th
                        C[ii][j] = e  # replace ii'th by temp
                        e = I[i][j]  # temp store i'th row
                        I[i][j] = I[ii][j]  # replace i'th row by ii'th
                        I[ii][j] = e  # replace ii'th by temp

                    # don't bother checking other rows since we've swapped
                    break
            # get the new diagonal
            e = C[i][i]
            # if it's still 0, not invertable (error)
            if e == 0: return None

        # Scale this row down by e (so we have a 1 on the diagonal)
        for j in range(n):
            C[i][j] /= e  # apply to original matrix
            I[i][j] /= e  # apply to identity

        # Subtract this row (scaled appropriately for each row) from ALL of
        # the other rows so that there will be 0's in this column in the
        # rows above and below this one
        for ii in range(n):
            # Only apply to other rows (we want a 1 on the diagonal
            if ii == i: continue

            # We want to change this element to 0
            e = C[ii][i]

            # Subtract this row (scaled appropriately for each row) from ALL of
            # current row) but start at the i'th column and assume all the
            # stuff left of diagonal is 0 (which it should be if we made this
            # algorithm correctly)
            for j in range(n):
                C[ii][j] -= e * C[i][j]  # apply to original matrix
                I[ii][j] -= e * I[i][j]  # apply to identity

    # we've done all operations, C should be the identity
    # matrix I should be the inverse
    return I

def test():
    from CurveFitting import multiply

    # test case from http://blog.acipo.com/matrix-inversion-in-javascript/
    M = [[1, 3, 3], [1, 4, 3], [1, 3, 4]]
    MI = matrixInvert(M)
    print(MI)  # print inverse

    # verify that the product of the original matrix and the
    # original matrix is the identity matrix
    print(multiply(M, MI))

if __name__ == "__main__":
    test()
