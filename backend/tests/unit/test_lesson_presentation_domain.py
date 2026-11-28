"""Pure T-SLD1 rules: bounded slide edits, URL allowlisting and source staleness."""

from __future__ import annotations

import pytest

from sketch2life.domain.lesson_occurrences.presentation import (
    MAX_SLIDES,
    PresentationRuleError,
    apply_operations,
    command_fingerprint,
    content_hash,
    embed_url,
    make_slide,
    parse_video_url,
    seed_slides,
    stale_reasons,
    validate_subject_text,
)


def test_operations_apply_in_order_and_return_renumbered_copies() -> None:
    original = [make_slide("A", "first", 1, slide_id="slide-a")]
    changed = apply_operations(
        original,
        [
            {"op": "UPDATE_SLIDE", "slide_id": "slide-a", "title": "Edited"},
            {
                "op": "ADD_SLIDE",
                "after_slide_id": "slide-a",
                "title": "B",
                "body_text": "second",
            },
            {
                "op": "MOVE_SLIDE",
                "slide_id": "slide-a",
                "to_position": 2,
            },
        ],
    )
    assert [(slide["slide_id"], slide["position"], slide["title"]) for slide in changed] == [
        (changed[0]["slide_id"], 1, "B"),
        ("slide-a", 2, "Edited"),
    ]
    assert original[0]["title"] == "A" and len(original) == 1


def test_delete_last_slide_unknown_slide_and_slide_limit_are_rejected() -> None:
    with pytest.raises(PresentationRuleError, match="OUT_OF_RANGE") as last:
        apply_operations(
            [make_slide("", "", 1, slide_id="only")],
            [{"op": "DELETE_SLIDE", "slide_id": "only"}],
        )
    assert last.value.field == "operations[0].slide_id"

    with pytest.raises(PresentationRuleError) as missing:
        apply_operations(
            [make_slide("", "", 1, slide_id="known")],
            [{"op": "DELETE_SLIDE", "slide_id": "missing"}],
        )
    assert missing.value.field == "operations[0].slide_id"

    full = [make_slide("", "", index) for index in range(1, MAX_SLIDES + 1)]
    with pytest.raises(PresentationRuleError, match="OUT_OF_RANGE"):
        apply_operations(
            full,
            [{"op": "ADD_SLIDE", "after_slide_id": None, "title": "x", "body_text": "y"}],
        )


def test_set_media_and_clear_media_store_only_the_canonical_video_reference() -> None:
    slides = [make_slide("", "", 1, slide_id="slide-a")]
    with_media = apply_operations(
        slides,
        [
            {
                "op": "SET_MEDIA",
                "slide_id": "slide-a",
                "placement": "RIGHT",
                "media": {"kind": "VIDEO_EMBED", "url": "https://youtu.be/abcdefghijk"},
            }
        ],
    )
    assert with_media[0]["media"] == {
        "kind": "VIDEO_EMBED",
        "provider": "YOUTUBE",
        "video_id": "abcdefghijk",
        "alt_text": "",
        "placement": "RIGHT",
    }
    cleared = apply_operations(with_media, [{"op": "CLEAR_MEDIA", "slide_id": "slide-a"}])
    assert cleared[0]["media"] is None


@pytest.mark.parametrize(
    ("url", "provider", "video_id"),
    [
        ("https://www.youtube.com/watch?v=abcdefghijk", "YOUTUBE", "abcdefghijk"),
        ("https://youtube.com/embed/abcdefghijk", "YOUTUBE", "abcdefghijk"),
        ("https://youtu.be/abcdefghijk", "YOUTUBE", "abcdefghijk"),
        ("https://www.youtube-nocookie.com/embed/abcdefghijk", "YOUTUBE", "abcdefghijk"),
        ("https://vimeo.com/123456", "VIMEO", "123456"),
        ("https://player.vimeo.com/video/123456", "VIMEO", "123456"),
    ],
)
def test_video_allowlist_builds_canonical_embed_urls(
    url: str,
    provider: str,
    video_id: str,
) -> None:
    assert parse_video_url(url) == {"provider": provider, "video_id": video_id}
    expected = (
        f"https://www.youtube-nocookie.com/embed/{video_id}"
        if provider == "YOUTUBE"
        else f"https://player.vimeo.com/video/{video_id}"
    )
    assert embed_url(provider, video_id) == expected


@pytest.mark.parametrize(
    "url",
    [
        "http://youtube.com/watch?v=abcdefghijk",
        "https://user@youtube.com/watch?v=abcdefghijk",
        "https://youtube.com:443/watch?v=abcdefghijk",
        "https://youtube.com.evil.test/watch?v=abcdefghijk",
        "https://xn--youtube-9za.com/watch?v=abcdefghijk",
        "javascript:alert(1)",
        "https://youtube.com/watch?v=abcdefghij",
        "https://youtube.com/watch?v=abcdefghijkl",
        "https://vimeo.com/123/abcdef0123456789",
        "https://youtu.be/abcdefghijk#fragment",
        "https://youtube.com/watch?v=abcdefghijk&v=abcdefghijk",
        "https://youtube.com:/watch?v=abcdefghijk",
        "https://youtube.com/watch?v=abcdefghijk" + "x" * 2048,
    ],
)
def test_video_urls_outside_the_https_allowlist_are_refused(url: str) -> None:
    with pytest.raises(PresentationRuleError) as error:
        parse_video_url(url, field="operations[0].media.url")
    assert error.value.code == "INVALID_FORMAT"
    assert error.value.field == "operations[0].media.url"


def test_seed_hash_fingerprint_and_staleness_are_deterministic() -> None:
    seeded = seed_slides([{"title": "Draw", "description": "Observe"}], seed="PLAN_ACTIVITIES")
    assert seeded[0]["title"] == "Draw" and seeded[0]["position"] == 1
    assert seed_slides([], seed="PLAN_ACTIVITIES")[0]["media"] is None
    assert seed_slides([], seed="BLANK")[0]["body_text"] == ""
    assert content_hash({"b": 2, "a": 1}) == content_hash({"a": 1, "b": 2})
    common = {
        "method": "POST",
        "route": "/revisions",
        "ids": {"occurrence_id": "occ"},
        "body": {"x": 1},
    }
    first = command_fingerprint(**common, if_match='"1"')
    assert first == command_fingerprint(**common, if_match='"1"')
    assert first != command_fingerprint(**common, if_match='"2"')
    assert stale_reasons(
        pinned_plan_revision_id="old",
        current_plan_revision_id="new",
        slides=[{"media": {"kind": "SVG_AI", "svg_draft_id": "draft"}}],
        draft_states={"draft": "DISCARDED"},
    ) == ["PLAN_REVISION_CHANGED", "MEDIA_SOURCE_CHANGED"]


@pytest.mark.parametrize("value", ["đom đóm 2", "art-class 01"])
def test_subject_text_accepts_bounded_unicode_letters_digits_spaces_and_hyphens(value: str) -> None:
    assert validate_subject_text(value) == value


@pytest.mark.parametrize("value", ["", "x" * 81, "cat!", "one_two"])
def test_subject_text_rejects_values_outside_the_small_input_contract(value: str) -> None:
    with pytest.raises(PresentationRuleError):
        validate_subject_text(value)
