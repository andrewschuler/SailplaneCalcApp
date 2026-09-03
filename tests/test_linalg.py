import pytest

from sailplane_calc.engine.linalg import solve_linear_system


def test_identity_matrix_returns_b_unchanged():
    a = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    b = [[1, 4], [2, 5], [3, 6]]
    x = solve_linear_system(a, b)
    for x_row, b_row in zip(x, b):
        assert x_row == pytest.approx(b_row)


def test_hand_solvable_3x3_system():
    # 2x + y     = 5
    #  x + 3y + z = 10
    #      y + 4z = 9
    a = [[2, 1, 0], [1, 3, 1], [0, 1, 4]]
    b = [[5], [10], [9]]
    x = solve_linear_system(a, b)
    # Verify by substitution rather than a hand-picked closed-form answer, and check A x == b.
    x0, x1, x2 = x[0][0], x[1][0], x[2][0]
    assert 2 * x0 + x1 == pytest.approx(5)
    assert x0 + 3 * x1 + x2 == pytest.approx(10)
    assert x1 + 4 * x2 == pytest.approx(9)


def test_multi_rhs_matches_solving_columns_individually():
    a = [[4, 1], [2, 3]]
    b1 = [[1], [2]]
    b2 = [[5], [-1]]
    batched = solve_linear_system(a, [[b1[0][0], b2[0][0]], [b1[1][0], b2[1][0]]])
    individually_1 = solve_linear_system(a, b1)
    individually_2 = solve_linear_system(a, b2)
    assert [row[0] for row in batched] == pytest.approx([row[0] for row in individually_1])
    assert [row[1] for row in batched] == pytest.approx([row[0] for row in individually_2])


def test_singular_row_does_not_raise():
    a = [[1, 0, 0], [0, 0, 0], [0, 0, 1]]
    b = [[3], [7], [9]]
    x = solve_linear_system(a, b)
    assert x[0][0] == pytest.approx(3)
    assert x[2][0] == pytest.approx(9)
    # The degenerate unknown is left decoupled rather than raising or blowing up.
    assert x[1][0] == pytest.approx(7)


def test_partial_pivoting_required():
    # Naive (no-pivot) elimination would divide by the 0 in the top-left corner.
    a = [[0, 1], [1, 1]]
    b = [[2], [3]]
    x = solve_linear_system(a, b)
    assert x[0][0] == pytest.approx(1)
    assert x[1][0] == pytest.approx(2)
