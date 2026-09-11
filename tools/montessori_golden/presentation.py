from __future__ import annotations

from typing import Any

WARNING = (
    "FIXTURE-ONLY: kết quả là kiểm tra contract, không đánh giá trẻ thật và không phải "
    "qualified Montessori/production approval."
)


def build_evaluation_document(
    activity: dict[str, Any], case_input: dict[str, Any], result: dict[str, Any]
) -> dict[str, Any]:
    return {
        "console_schema_version": 1,
        "activity_ref": {"id": activity["id"], "version": activity["version"]},
        "input": case_input,
        "result": result,
        "review_status": activity["review"]["status"],
        "production_eligible": False,
        "warning": WARNING,
    }


def format_evaluation(document: dict[str, Any]) -> str:
    result = document["result"]
    lines = [
        "MONTESSORI_GOLDEN_CONSOLE",
        f"activity={document['activity_ref']['id']}@v{document['activity_ref']['version']}",
        f"status={result['status']}",
    ]
    if result["blocked"]:
        activity_id = document["activity_ref"]["id"]
        lines.append(f"reasons={','.join(result['blocked'][activity_id])}")
    else:
        lines.append("reasons=none")
    lines.extend(
        [
            f"review_status={document['review_status']}",
            "production_eligible=false",
            f"warning={document['warning']}",
        ]
    )
    return "\n".join(lines)


def format_activity_list(summaries: list[dict[str, Any]]) -> str:
    lines = [
        "MONTESSORI_GOLDEN_ACTIVITY_LIST",
        f"count={len(summaries)}",
        "selection_mode=EXPLICIT_ACTIVITY_ONLY",
    ]
    for item in summaries:
        ref = item["activity_ref"]
        ages = item["age_months"]
        readiness = ",".join(item["readiness_ids"])
        materials = ",".join(option["id"] for option in item["material_options"])
        lines.append(
            f"{ref['id']}@v{ref['version']} | {item['title_vi']} | "
            f"age={ages['min']}-{ages['max']} | supervision={item['minimum_supervision']} | "
            f"readiness={readiness} | materials={materials}"
        )
    lines.extend(
        [
            "review_status=PROVISIONAL_OWNER_REVIEWED",
            "production_eligible=false",
            f"warning={WARNING}",
        ]
    )
    return "\n".join(lines)
