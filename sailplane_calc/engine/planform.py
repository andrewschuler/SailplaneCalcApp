"""2D planform outline geometry, for drawing (not analysis) -- see ui/planform_widget.py.

Builds a single closed polygon in (span, chord) coordinates tracing a surface's leading and
trailing edges, root to tip, the same way `geometry.compute_surface` walks panels (cumulative
span/sweep) but keeping every breakpoint instead of reducing to aggregate scalars.
"""
from __future__ import annotations

from .models import PanelInput

Point = tuple[float, float]


def compute_planform_outline(panels: list[PanelInput], mirror: bool) -> list[Point]:
    active = [p for p in panels if p.span > 0]
    if not active:
        return []

    le_points: list[Point] = [(0.0, 0.0)]
    te_points: list[Point] = [(0.0, active[0].chord_root)]
    cumulative_span = 0.0
    cumulative_sweep = 0.0
    for p in active:
        cumulative_span += p.span
        cumulative_sweep += p.sweep_offset
        le_points.append((cumulative_span, cumulative_sweep))
        te_points.append((cumulative_span, cumulative_sweep + p.chord_tip))

    if not mirror:
        # root LE -> tip LE -> tip TE -> root TE (implicitly closed back to root LE)
        return le_points + list(reversed(te_points))

    # Both sides, unrolled as one continuous boundary: left tip LE -> root -> right tip LE ->
    # right tip TE -> root -> left tip TE (implicitly closed back to left tip LE). The root
    # LE/TE points are shared between both sides so each appears exactly once.
    left_le_reversed = [(-s, c) for s, c in reversed(le_points)]
    right_le = le_points[1:]
    right_te_reversed = list(reversed(te_points))
    left_te = [(-s, c) for s, c in te_points[1:]]
    return left_le_reversed + right_le + right_te_reversed + left_te


def compute_planform_panels(panels: list[PanelInput], mirror: bool) -> list[tuple[int, list[Point]]]:
    """Per-panel quads (root LE, tip LE, tip TE, root TE), each tagged with its panel index --
    lets a widget color each panel distinctly. A mirrored panel's counterpart shares the same
    index so both sides get the same color."""
    active = [p for p in panels if p.span > 0]
    result: list[tuple[int, list[Point]]] = []
    cumulative_span = 0.0
    cumulative_sweep = 0.0
    for idx, p in enumerate(active):
        root_le = (cumulative_span, cumulative_sweep)
        tip_le = (cumulative_span + p.span, cumulative_sweep + p.sweep_offset)
        tip_te = (cumulative_span + p.span, cumulative_sweep + p.sweep_offset + p.chord_tip)
        root_te = (cumulative_span, cumulative_sweep + p.chord_root)
        quad = [root_le, tip_le, tip_te, root_te]
        result.append((idx, quad))
        if mirror:
            result.append((idx, [(-s, c) for s, c in quad]))
        cumulative_span += p.span
        cumulative_sweep += p.sweep_offset
    return result


def compute_fin_panels(lower: PanelInput, upper: PanelInput) -> list[tuple[int, list[Point]]]:
    """Lower panel is always index 0, upper always index 1 (regardless of which is active),
    so their colors stay stable as spans change -- matches `compute_fin_outline`'s sign
    convention (lower extends into negative "span")."""
    result: list[tuple[int, list[Point]]] = []
    if lower.span > 0:
        quad = [
            (0.0, 0.0),
            (-lower.span, lower.sweep_offset),
            (-lower.span, lower.sweep_offset + lower.chord_tip),
            (0.0, lower.chord_root),
        ]
        result.append((0, quad))
    if upper.span > 0:
        quad = [
            (0.0, 0.0),
            (upper.span, upper.sweep_offset),
            (upper.span, upper.sweep_offset + upper.chord_tip),
            (0.0, upper.chord_root),
        ]
        result.append((1, quad))
    return result


def compute_fin_outline(lower: PanelInput, upper: PanelInput) -> list[Point]:
    """The vertical fin's lower/upper panels share a root but extend in opposite directions
    (not a chained stack like `compute_planform_outline` handles) -- lower spans into
    negative "span" and upper into positive, matching `tail_cruciform.compute_vertical_fin`'s
    sign convention for `mac_span_location`."""
    root_chord = lower.chord_root if lower.span > 0 else upper.chord_root

    le_points: list[Point] = []
    te_points: list[Point] = []
    if lower.span > 0:
        le_points.append((-lower.span, lower.sweep_offset))
        te_points.append((-lower.span, lower.sweep_offset + lower.chord_tip))
    le_points.append((0.0, 0.0))
    te_points.append((0.0, root_chord))
    if upper.span > 0:
        le_points.append((upper.span, upper.sweep_offset))
        te_points.append((upper.span, upper.sweep_offset + upper.chord_tip))

    if len(le_points) == 1:
        return []
    return le_points + list(reversed(te_points))
