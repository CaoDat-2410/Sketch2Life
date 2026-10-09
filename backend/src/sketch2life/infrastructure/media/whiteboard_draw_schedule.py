"""Order traced strokes using reviewed visual regions and narration intervals.

Boxes are placement hints over the *generated scene illustration*, not object
masks. The renderer must not claim semantic segmentation from this heuristic.
"""

from __future__ import annotations

from sketch2life.contracts.schemas.story_video import StoryboardDrawBeatV1


def order_strokes_for_beats(
    strokes: list[dict], beats: tuple[StoryboardDrawBeatV1, ...], *, width: int, height: int
) -> tuple[list[int], list[tuple[float, float, int, int]]]:
    if not beats:
        return list(range(len(strokes))), []
    if abs(beats[0].start_seconds) > 0.01 or any(
        abs(previous.end_seconds - current.start_seconds) > 0.01
        for previous, current in zip(beats, beats[1:], strict=False)
    ):
        raise ValueError("DRAW_BEATS_NOT_CONTIGUOUS")

    groups: list[list[int]] = [[] for _ in beats]
    unassigned: list[tuple[int, float, float]] = []
    for index, stroke in enumerate(strokes):
        points = stroke["points"]
        x = sum(float(point[0]) for point in points) / len(points) / width
        y = sum(float(point[1]) for point in points) / len(points) / height
        owners = [beat_index for beat_index, beat in enumerate(beats)
                  if beat.focus_box[0] <= x <= beat.focus_box[2]
                  and beat.focus_box[1] <= y <= beat.focus_box[3]]
        if owners:
            groups[owners[0]].append(index)
        else:
            unassigned.append((index, x, y))
    if any(not group for group in groups):
        raise ValueError("DRAW_BEAT_EMPTY")
    for index, x, y in unassigned:
        nearest = min(range(len(beats)), key=lambda beat_index: (
            (x - (beats[beat_index].focus_box[0] + beats[beat_index].focus_box[2]) / 2) ** 2
            + (y - (beats[beat_index].focus_box[1] + beats[beat_index].focus_box[3]) / 2) ** 2
        ))
        groups[nearest].append(index)

    order = [index for group in groups for index in group]
    windows: list[tuple[float, float, int, int]] = []
    cursor = 0
    for beat, group in zip(beats, groups, strict=True):
        end = cursor + sum(max(0, len(strokes[index]["points"]) - 1) for index in group)
        windows.append((beat.start_seconds, beat.end_seconds, cursor, end))
        cursor = end
    return order, windows


def visible_segments_at(
    elapsed: float, windows: list[tuple[float, float, int, int]]
) -> int:
    for start, end, first_segment, last_segment in windows:
        drawing_end = start + 0.8 * (end - start)
        if elapsed < drawing_end:
            progress = max(0.0, (elapsed - start) / (drawing_end - start))
            return first_segment + round((last_segment - first_segment) * progress)
    return windows[-1][3]


def color_start_at(
    trigger_segment: int, windows: list[tuple[float, float, int, int]]
) -> tuple[float, float]:
    for start, end, first_segment, last_segment in windows:
        if trigger_segment <= last_segment:
            fraction = (trigger_segment - first_segment) / max(1, last_segment - first_segment)
            return start + 0.8 * (end - start) * fraction, min(0.5, 0.2 * (end - start))
    return windows[-1][1], 0.01
