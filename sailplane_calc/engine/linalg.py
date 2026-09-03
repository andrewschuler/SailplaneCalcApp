"""Small generic dense-linear-system solver, used by the Cl distribution VLM (see
cl_distribution.py) to invert its aerodynamic-influence matrix. Kept free of any
VLM-specific naming so it's independently testable and reusable.
"""
from __future__ import annotations


def solve_linear_system(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    """Solves A x = B for x, where A is NxN and B is NxM (M right-hand-side columns solved
    off one Gauss-Jordan elimination with partial pivoting).

    A pivot column that's still ~0 after searching for the best available pivot (e.g. a
    degenerate row from a zero-span panel mid-edit) is left as an identity row instead of
    raising -- the corresponding unknowns resolve to whatever B held there, which for the
    all-zero RHS columns this module is used with just means "no contribution", the same
    crash-avoidance convention as geometry.safe_div.
    """
    n = len(a)
    m = len(b[0]) if b else 0

    # Augmented matrix: each row is [A row..., B row...], mutated in place via elimination.
    aug = [list(a[i]) + list(b[i]) for i in range(n)]

    for col in range(n):
        pivot_row = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot_row][col]) < 1e-12:
            continue  # degenerate column -- leave this unknown decoupled (see docstring)
        aug[col], aug[pivot_row] = aug[pivot_row], aug[col]

        pivot_val = aug[col][col]
        aug[col] = [v / pivot_val for v in aug[col]]

        for r in range(n):
            if r == col:
                continue
            factor = aug[r][col]
            if factor == 0.0:
                continue
            aug[r] = [rv - factor * cv for rv, cv in zip(aug[r], aug[col])]

    return [row[n : n + m] for row in aug]
