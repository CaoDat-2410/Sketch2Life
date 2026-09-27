"""Bounded educational storyboard generation for whiteboard video."""

from __future__ import annotations

from typing import Literal
from uuid import uuid4

from sketch2life.contracts.schemas.whiteboard_storyboard import (
    WhiteboardStoryboardSceneV1,
    WhiteboardStoryboardV1,
)

AudienceBand = Literal["EARLY_PRIMARY", "PRIMARY"]


class WhiteboardStoryboardGenerator:
    """Generate reviewed, age-bounded storyboards from grounded image claims.

    This first slice is intentionally deterministic. It establishes the contract and
    prevents an unreviewed model from inventing child-facing facts. New topics can be
    added as reviewed templates, then replaced by an approved model adapter later.
    """

    def generate(
        self,
        *,
        subject_claim: str,
        feature_claim: str = "ria mèo",
        audience_band: AudienceBand = "EARLY_PRIMARY",
    ) -> WhiteboardStoryboardV1:
        subject = subject_claim.strip().casefold()
        feature = feature_claim.strip().casefold()
        if subject not in {"con mèo", "mèo", "cat"} or feature not in {
            "ria mèo",
            "râu mèo",
            "whiskers",
        }:
            raise ValueError("no reviewed whiteboard knowledge template matches these claims")

        if audience_band == "EARLY_PRIMARY":
            age_min, age_max = 6, 8
            scenes = (
                WhiteboardStoryboardSceneV1(
                    scene_id="scene-1",
                    duration_seconds=3.0,
                    narration_vi="Bạn có biết vì sao mèo có những sợi ria dài bên má không?",
                    visual_prompt_vi=(
                        "Một chú mèo hoạt hình thân thiện trên nền sáng, "
                        "khung dọc 9:16."
                    ),
                    motion="INTRO",
                    source_claims=("cat", "whiskers"),
                ),
                WhiteboardStoryboardSceneV1(
                    scene_id="scene-2",
                    duration_seconds=4.0,
                    narration_vi=(
                        "Ria mèo rất nhạy, giúp mèo cảm nhận vật ở gần "
                        "và luồng không khí xung quanh."
                    ),
                    visual_prompt_vi=(
                        "Cận cảnh khuôn mặt mèo; ria được highlight, "
                        "các luồng khí nhẹ di chuyển quanh ria."
                    ),
                    motion="FOCUS",
                    source_claims=("cat", "whiskers"),
                ),
                WhiteboardStoryboardSceneV1(
                    scene_id="scene-3",
                    duration_seconds=4.0,
                    narration_vi=(
                        "Nhờ vậy, mèo có thể định hướng và tránh vật cản "
                        "khi đi trong nơi hẹp hoặc thiếu sáng."
                    ),
                    visual_prompt_vi=(
                        "Mèo đi qua một khoảng hẹp, các đường đo khoảng cách "
                        "và vật cản được minh họa rõ ràng."
                    ),
                    motion="DEMONSTRATE",
                    source_claims=("cat", "whiskers"),
                ),
                WhiteboardStoryboardSceneV1(
                    scene_id="scene-4",
                    duration_seconds=3.0,
                    narration_vi="Vì thế, chúng ta không nên tự ý cắt ria của mèo nhé!",
                    visual_prompt_vi=(
                        "Mèo ngồi vui vẻ cạnh biểu tượng ria; khung kết luận "
                        "đơn giản, thân thiện với trẻ."
                    ),
                    motion="RECAP",
                    source_claims=("cat", "whiskers"),
                ),
            )
        else:
            age_min, age_max = 9, 12
            scenes = (
                WhiteboardStoryboardSceneV1(
                    scene_id="scene-1",
                    duration_seconds=3.0,
                    narration_vi="Ria mèo không chỉ là những sợi lông trang trí.",
                    visual_prompt_vi=(
                        "Mèo hoạt hình, cận cảnh hai bên má, "
                        "phong cách minh họa khoa học."
                    ),
                    motion="INTRO",
                    source_claims=("cat", "whiskers"),
                ),
                WhiteboardStoryboardSceneV1(
                    scene_id="scene-2",
                    duration_seconds=5.0,
                    narration_vi=(
                        "Chúng giúp mèo phát hiện thay đổi rất nhỏ của không khí "
                        "và vật thể ở gần."
                    ),
                    visual_prompt_vi=(
                        "Minh họa luồng khí chạm vào ria và truyền tín hiệu "
                        "về vùng cảm giác ở mặt mèo."
                    ),
                    motion="FOCUS",
                    source_claims=("cat", "whiskers"),
                ),
                WhiteboardStoryboardSceneV1(
                    scene_id="scene-3",
                    duration_seconds=4.0,
                    narration_vi=(
                        "Đó là lý do ria hỗ trợ mèo định hướng trong không gian hẹp "
                        "và ánh sáng yếu."
                    ),
                    visual_prompt_vi="Mèo đo khoảng cách giữa hai vật cản trong một hành lang hẹp.",
                    motion="DEMONSTRATE",
                    source_claims=("cat", "whiskers"),
                ),
                WhiteboardStoryboardSceneV1(
                    scene_id="scene-4",
                    duration_seconds=3.0,
                    narration_vi=(
                        "Ria là một bộ phận cảm giác quan trọng, "
                        "nên không nên tự ý cắt chúng."
                    ),
                    visual_prompt_vi=(
                        "Infographic ngắn tóm tắt: cảm nhận, định hướng, "
                        "tránh vật cản."
                    ),
                    motion="RECAP",
                    source_claims=("cat", "whiskers"),
                ),
            )

        return WhiteboardStoryboardV1(
            storyboard_id=f"storyboard-{uuid4()}",
            topic_vi="Ria mèo dùng để làm gì?",
            audience_age_min=age_min,
            audience_age_max=age_max,
            duration_seconds=sum(scene.duration_seconds for scene in scenes),
            source_claims=("cat", "whiskers"),
            scenes=scenes,
        )

    def generate_for_age(
        self,
        *,
        subject_claim: str,
        feature_claim: str,
        age_months: int,
    ) -> WhiteboardStoryboardV1:
        """Resolve an adult-supplied P1 age into a reviewed audience band."""

        if not 72 <= age_months <= 155:
            raise ValueError("no reviewed whiteboard audience band matches this age")
        audience_band: AudienceBand = (
            "EARLY_PRIMARY" if age_months < 108 else "PRIMARY"
        )
        return self.generate(
            subject_claim=subject_claim,
            feature_claim=feature_claim,
            audience_band=audience_band,
        )


__all__ = ["AudienceBand", "WhiteboardStoryboardGenerator"]
