from __future__ import annotations

import argparse
import hashlib
import tempfile
import zipfile
from pathlib import Path

from docx import Document


SOURCE_SHA256 = "47F23FD4486A4605208BB44A7B3696081F973DF74D4F1B8D56F7D35C34DF6956"

# Existing v1.1 form fields are expanded in place using Master SRS v2.0.
# No paragraphs, sections, tables, or signature blocks are added or removed.
REPLACEMENTS = {
    18: "Sketch2Life is an adult-supervised system for children under 9 years (0–107 completed months; product bands 0–35, 36–71 and 72–107 months) that transforms a child's drawing and description into a personalized Montessori learning experience. A verified adult owns each ChildProfile, supplies or confirms age and relevant learning context, and remains present for the session; children do not have independent accounts. The workflow combines reviewed AI proposals with separate adult decisions, then returns the child to a concrete activity away from the screen. Responsive Parent Web and adult-facing Guide/Admin surfaces complement the Android app. Ages 9–12 remain preserved in the catalog and historical records but are outside supported profiles, activity discovery and age-sensitive generation.",
    19: "-\tA drawing and a child's words can reveal an interest or intended subject, but either source may be ambiguous. Parents and Guides need a reviewable way to connect the adult-confirmed meaning to appropriate Montessori work without treating model guesses as facts.",
    20: "-\tActivity discovery returns the complete reviewed set matching the Gate-A-confirmed topic and the child's exact supported age. Only inactive/unreviewed or blocked catalog status, age/topic mismatch, authored safety or policy rules, and required supervision may exclude a match; adult-confirmed interests order or explain results. Readiness, prior work, prerequisite sequence and available materials do not filter the discovery set.",
    21: "-\tChildren's drawings and speech differ from standard image and speech-model inputs. The system must keep image and narration evidence distinguishable, expose conflicts and uncertainty to the adult, and allow transcript correction, re-recording or a safe general explanation.",
    22: "-\tA digital result conflicts with the intended pedagogy if it becomes the destination. Keep digital use to about 10 minutes per session, excluding physical work, and end with the exact adult-approved activity, preparation and supervision guidance for an off-screen handoff.",
    23: "-\tChild-directed stories, illustrations, audio/video and activities need age-appropriate language, reviewed educational sources, claim-level citations, content and physical-safety checks, and adult review before delivery. Uncertain image labels must not become unsupported species-specific facts.",
    24: "-\tDrawings, voice recordings, transcripts, generated derivatives and observations are sensitive child data. Collect or use research data only with guardian consent and a defined protocol; product records need owner-scoped access, data minimization, retention choice, archive-before-purge and deletion evidence.",
    27: "Build Sketch2Life as an adult-supervised session: an adult authenticates, opens a child profile with consent and adult-sourced age, then captures the original drawing and optional child narration. Media admission, ASR/VLM analysis and fusion produce a proposal with source evidence and uncertainty for Gate A. After the adult confirms meaning, discovery returns every reviewed activity matching the confirmed topic and exact age, ordered by adult-confirmed interests and constrained only by catalog status, topic/age compatibility, safety/policy and required supervision. Gate B binds the adult's selected activity and objective. Reviewed knowledge then supports an age-aware story draft; the adult edits and approves the exact script before image generation. PixiJS explores the unchanged original while a separate illustrated story/video job runs. The system releases the child only when outputs pass required checks and provides a safe, supervised handoff, feedback and history.",
    28: "-\tDrawing Capture and Child Narration: An accompanying adult captures the original drawing and, with guardian consent, records the child's description. The adult may assist, correct the transcript or request a new recording; the source image/audio stay distinguishable from derived files and are not replaced by generated media.",
    29: "-\tMultimodal Understanding and Gate A: Media admission validates supported type, size and integrity; ASR transcribes speech and vision analyzes the drawing. Fusion preserves each claim's source, uncertainty and disagreement. A verified Parent or assigned Guide reviews the proposed meaning, corrects it or asks for another recording. Gate A confirms meaning only; it does not approve an activity or story.",
    30: "-\tMontessori Mapping and Gate B: Once Gate A confirms the topic, return the full active, reviewed set compatible with that topic and exact age. Exclude only blocked/unreviewed/inactive entries, topic or age mismatches, authored safety/policy failures, and unmet required-supervision rules; use adult-confirmed interests for ordering or match explanations. Do not hide matches because readiness, history, sequence or materials are missing. Show materials, substitutes, preparation and safe-use guidance after selection. A verified adult separately approves the exact activity/objective pair at Gate B.",
    31: "-\tReviewed Knowledge and Story Planning: Query versioned, reviewed educational sources using the Gate-A-confirmed subject, Gate-B activity/objective, adult/profile-sourced age band, relevant readiness context and selected language. Keep observed details separate from sourced educational facts; cite each factual claim to its reviewed source and locator. Label any imaginative connective language clearly, and use general wording or request adult correction when the subject remains uncertain.",
    32: "-\tPersonalized Drawing Exploration: After Gate B, use PixiJS/GSAP for a deterministic learning thread on the child's original drawing: focus a subject, reveal details on tap and show selected relationships with source-derived layers or restrained 2.5D motion. Preserve the source artifact and hashes; every cut-out or scene asset is a traceable derivative. Animation failure falls back to the same approved still image and activity.",
    33: "-\tIllustrated Story Video: Prepare a 40–60 second story tied to the confirmed subject and approved objective. The adult can edit with supported quick controls, free text or both; every edit returns a complete new revision, and the adult approves the exact script, sources, age band, language and voice before any image-generation request. Generate derived scene illustrations, separate TTS from raw child narration, and assemble narration-timed scenes into a validated MP4 using Wan2.2 TI2V-5B as the scene-motion baseline. Report READY only after duration, complete audio, content/safety and provenance checks pass.",
    34: "-\tHands-On Activity Delivery: End with the exact Gate-B-approved activity and objective, including reviewed materials, possible home substitutes, setup, ordered steps, safety points and required adult supervision. Stop digital playback before the activity begins. Children aged 0–35 months require participating caregiver presence and direct supervision.",
    35: "-\tSafety, Fallback and Recovery: Validate text, image, audio, video and physical-activity instructions before showing or handing them off. Use typed progress and failure states, bounded idempotent retries and a still-image fallback where supported; a retry must not duplicate a job or change the approved activity. Do not report video READY or continue to handoff while required media, audio, safety or provenance checks are incomplete.",
    36: "-\tObservation and History: Let an authorized adult record completed, partially completed or not-attempted outcomes, observations and interests against the exact activity/objective version. Record per-session digital screen time separately; viewing or elapsed time must never be treated as proof that physical work was completed. Apply consent, owner-scoped access and retention/deletion controls.",
    40: "•\tWith an accompanying adult, provide the original drawing and an optional spoken description; the adult may assist with capture and transcript correction. Children do not sign in or manage profile, consent or payment settings.",
    41: "•\tExplore a PixiJS experience derived from the unchanged drawing and watch the separately produced, adult-approved illustrated story with its selected TTS narration when media is ready.",
    42: "•\tWith the accompanying adult, receive the exact approved Montessori activity, required materials or substitutes, preparation, steps and supervision guidance, then continue away from the device.",
    45: "•\tCreate and manage owned ChildProfiles under 9 years (0–107 completed months), using adult-supplied or adult-confirmed age/band and relevant readiness context. Record guardian consent and retention choice; changes to age or profile context invalidate affected drafts before age-sensitive use.",
    46: "•\tReview Gate A's proposed subject, transcript, source evidence, conflicts and uncertainty; correct the meaning, edit the transcript or request a new recording. Only an authorized adult can confirm the meaning used by later steps.",
    47: "•\tAt Gate B, review the complete topic-and-exact-age matching activity set and its interest-based ordering, then approve the exact activity/objective pair. See materials, home substitutes, setup, steps and adult safety/supervision guidance for the selected activity.",
    48: "•\tAfter the off-screen handoff, mark the activity completed, partially completed or not attempted and record observations; completion is an adult-entered outcome, not inferred from playback or screen time.",
    49: "•\tView owner-scoped interest and activity history, adult observations, per-session digital screen time and a minimal live session phase/status/progress projection through responsive Parent Web.",
    50: "•\tAssign or immediately revoke Guides, manage consent, retention and deletion, and view plans, included profiles/credits, top-ups and current household/class balance. An adult may choose a plan or top-up and see its terms before checkout; monthly paid plans renew manually, and entitlement or top-up credits appear only after backend-verified payment. Children cannot purchase or change entitlements.",
    55: "•\tReview assigned-child observations and the topic/age-matching discovery set; record a permitted activity selection or override with actor, reason and catalog version. No override may bypass catalog, authored safety/policy or required-supervision constraints.",
    59: "•\tAdmit and validate supported media, retain original references, transcribe narration through an ASR adapter, analyze the drawing and fuse evidence with per-source provenance, confidence and uncertainty.",
    60: "•\tKeep image/narration conflicts visible, use the child's description as evidence where appropriate, and return uncertain proposals for Gate A correction or a safe generalization. Never infer a child's age or readiness from image/audio.",
    61: "•\tAfter Gate A, return every reviewed activity matching the confirmed topic and exact adult-sourced product age. Filter only catalog status, topic/age compatibility, authored safety/policy and required supervision; order or explain results with adult-confirmed interests without readiness/history/material suppression.",
    62: "•\tRetrieve knowledge from reviewed sources with claim-level citations and create age/readiness-constrained story drafts from the adult/profile-sourced 0–107 month band. Vary vocabulary, sentence complexity, fact count, pacing and explanation depth; do not use uncertain subject guesses as factual claims.",
    63: "•\tCreate PixiJS exploration from the original drawing, keeping original and derived asset hashes, anchors, scene mapping and provenance linked; preserve the source and support a still-image fallback.",
    64: "•\tSupport complete immutable story revisions from quick controls and/or adult free-form edits, conflict validation, selected supported locale/voice, exact-script approval and separate TTS/illustration/video steps. Do not submit image-generation work until the adult approves the exact script package.",
    65: "•\tApply text, activity, audio, video and provenance validators; use typed async job states, idempotency, bounded retry and safe recovery. Mark the illustrated video READY only after its 40–60 second MP4, complete narration/audio and required checks are present.",
    68: "•\tManage verified adult accounts, roles, ChildProfile ownership and Guide assignments through server-side authorization, audit changes, and prevent client-supplied identity or role data from granting access.",
    69: "•\tConfigure approved model profiles, age/content-safety policies, screen-time and operational limits with versioning, audit and safe rollback.",
    70: "•\tManage guardian-consent records, retention and deletion requests; archive eligible child records before purge and keep security/audit records governed separately from child-data retention.",
    71: "•\tMonitor processing jobs, model versions, notifications and platform health. Raw child-content access is limited to authorized break-glass support with a reason, temporary scope, redaction and audit.",
    74: "-\tOff-Screen Orientation: Target about 10 minutes of digital use per session, excluding the physical activity. Every completed digital flow presents an adult-approved off-screen activity and safe handoff rather than optimizing for longer viewing.",
    75: "-\tOwnership and Provenance of the Child's Work: Keep the original drawing immutable. PixiJS preserves its lines; story-video redraws are linked derivatives with source, scene, model and revision provenance and never replace the source artifact.",
    76: "-\tSafe Handling of Misrecognition: Do not show a confident unsupported identification to the child. Expose uncertainty and conflicting evidence to the adult, require confirmation/correction or use a general explanation, and prevent uncertain labels from grounding specific factual claims or activity eligibility.",
    77: "-\tContent and Activity Safety: Check child-facing text, illustrations, narration/video and physical steps for age-appropriate content, authored policy and required adult supervision before display or handoff; retain direct caregiver supervision requirements for children aged 0–35 months.",
    78: "-\tPedagogical Correctness: Return the complete reviewed set for the confirmed topic and exact age, applying only catalog, topic/age, safety/policy and required-supervision discovery constraints. Use adult-confirmed interests for ordering; show readiness, sequence and material information as context/guidance without filtering otherwise matching results.",
    79: "-\tPrivacy of Children's Data: Require guardian consent for research collection; enforce owner/active-assignment access, least privilege, data minimization, retention choice, archive-before-purge and deletion evidence for drawings, audio, transcripts, scripts, generated media and observations. Do not store raw payment credentials or provider secrets on mobile.",
    80: "-\tResponsiveness and Recovery: Show safe, bounded progress for asynchronous work; preserve job/session idempotency; return typed failure and retry choices; and degrade to a still image without changing the Gate-B-approved activity or falsely reporting successful video generation.",
    81: "-\tOffline Tolerance: Keep capture and saved activity instructions usable during poor connectivity where locally available. Queue generation safely, communicate queued/failed/retry states and resume without duplicate jobs or unauthorized state changes.",
    85: "The project combines Montessori pedagogy and developmental psychology with sketch/multimodal understanding, topic-and-age activity discovery, source-grounded child-facing GenAI, adult review, data provenance and privacy. Discovery eligibility remains distinct from adult pedagogical context and safety rules for carrying out a selected activity.",
    98: "These concepts are applied by building the target workflow and contracts with synthetic fixtures during development, reviewing Montessori mappings and safety guidance with qualified Guides, and studying families only under guardian consent, privacy controls and a defined research protocol.",
    99: "-\tBuild and version a reviewed Montessori knowledge base of areas, materials, activities, age compatibility, readiness/context, prerequisites, required supervision, safety rules, preparation and home substitutes.",
    100: "-\tCollect and annotate children's drawing, adult-supplied age/context, description and Guide mapping only under consent and the study protocol; pseudonymize research records and preserve source provenance and deletion controls.",
    101: "-\tBuild the multimodal understanding engine with media admission, ASR/VLM/fusion, source-specific evidence and explicit uncertainty; validate adult Gate A confirmation, correction, transcript editing and re-recording.",
    102: "-\tImplement PixiJS exploration on original artwork with traceable derived layers, focus/tap interaction, source-preserving animation and a still-image recovery path.",
    103: "-\tImplement reviewed-source retrieval, age-aware claim-cited story drafting, complete immutable revisions, quick/free-form edits, exact adult script approval, selected-locale TTS, illustrated-scene assembly and media validation.",
    104: "–\tImplement full topic-and-exact-age activity discovery with catalog, topic, age, safety and required-supervision exclusions and interest-based ordering; verify readiness, prior work, sequence or missing materials never suppress otherwise eligible matches.",
    105: "-\tEncode and validate child-content, activity, media, consent, authorization, provenance, age and required-supervision rules; exercise safe fallback and handoff behavior with synthetic cases and qualified review.",
    106: "-\tBuild the supervised Android session, responsive Parent Web and desktop Guide/Admin surfaces for profile/consent, Gate A/B, package and balance visibility, story/video, feedback, screen-time and off-screen handoff.",
    107: "-\tEvaluate mappings, recognition and media quality with held-out data and Guide ratings; any household study uses consent, a defined sample/design, data minimization, deletion steps and duration/thresholds set in its protocol before collection.",
    110: "-\tParent and Child Android Mobile Application with supervised participation: adult-owned profiles, drawing/narration capture, Gate A/B review, PixiJS exploration, approved story/video playback, package/credit view and off-screen activity delivery.",
    111: "-\tResponsive Parent Web, desktop-first Montessori Guide Console and Admin Console for verified adult access, profile/consent/assignment management, assigned-child review, feedback/history, retention/deletion and operations. Parent Web also presents plan terms, top-ups, payment state and owner-scoped credit balance.",
    112: "-\tMontessori Curriculum Knowledge Base: reviewed and versioned areas, materials, topic-linked activities, exact age compatibility, readiness/context, prerequisite relations, safety and required-supervision rules, preparation and home substitutes.",
    113: "-\tMultimodal Drawing Understanding Engine: media admission, ASR/VLM/fusion, source-specific claims and uncertainty, adult-assisted input, transcript correction and Gate-A confirmation support.",
    114: "-\tPersonalized Drawing Exploration Engine: PixiJS/GSAP interaction, anchored source-derived layers, original-art animation, scene provenance and still-image fallback.",
    115: "-\tAge-Aware Story Experience Service: reviewed evidence and claim citations, age-aware script/scene plans, quick and free-form immutable revisions, adult approval of the exact script package and supported locale/voice selection.",
    116: "-\tTopic-and-Age Activity Discovery: complete reviewed matches for adult-confirmed topic and exact age; catalog, topic, age, safety and required-supervision filtering; adult-confirmed-interest ordering without readiness/history/material suppression.",
    117: "-\tIllustrated Story Video and Narration Pipeline: 40–60 second derivative MP4 with approved script, selected TTS narration, scene-timed assembly, age/content/safety and provenance validation, async progress, retry and recovery.",
    118: "-\tResearch and Evaluation Outputs: consent-governed annotated drawing dataset and evaluation report covering multimodal accuracy, complete activity-set quality, Guide agreement, safety/supervision, adult corrections, off-screen outcomes and per-session screen time.",
    121: "The project is organised into four coordinated Work Packages covering requirements and evaluation, core services, AI and media, and user-facing applications.",
    122: "-\tWP1 - Project Management, Montessori Domain and Evaluation: requirements traceability, reviewed catalog and source criteria, consent/privacy protocol, safety review, acceptance measures, Guide assessment and evaluation analysis.",
    123: "-\tWP2 - Backend, Identity, Curriculum Services and Recommender: adult authentication and authorization, ChildProfile ownership, Guide assignments, consent/retention, versioned contracts, complete topic/age discovery, package entitlement and server-authoritative idempotent credit/payment records.",
    124: "-\tWP3 - Understanding, Story and Media: media admission, ASR/VLM/fusion, uncertainty, reviewed-source retrieval, claim-cited story and immutable script workflow, TTS, Pixi provenance, derived illustration/video generation, READY validation and typed recovery.",
    125: "-\tWP4 - Mobile, Parent Web and Guide/Admin Surfaces: supervised capture and adult review, profile/consent and package visibility, Pixi/story playback, safe activity instructions, off-screen handoff, feedback/history, screen-time and usability evidence.",
    129: "The study asks whether combining a child's drawing and description improves subject understanding, and whether complete reviewed activity discovery for the adult-confirmed topic and exact age, ordered by confirmed interests, helps Montessori Guides select appropriate work while preserving safety and supervision. It also evaluates adult correction and whether the full Pixi/story experience supports a supervised off-screen handoff within bounded digital time.",
    132: "-\tConstruct a reviewed Montessori curriculum knowledge base and annotated drawing set with topic links, supported age compatibility, adult context, safety/supervision metadata, provenance and consent-governed research records.",
    133: "-\tMeasure subject identification with image-only, description-only and combined inputs on held-out data; report results separately across product bands 0–35, 36–71 and 72–107 months and relevant curriculum areas.",
    134: "-\tHave trained Montessori Guides assess whether the complete confirmed-topic/exact-age set is relevant and complete and whether adult-confirmed-interest ordering is useful; compare with an unconstrained-similarity baseline and report inter-rater agreement.",
    135: "-\tMeasure whether returned activities meet reviewed-catalog, topic/age, authored safety/policy and required-supervision rules; report safety compliance separately from Guide judgments and interest-ranking quality.",
    136: "-\tIn a consented household study, measure session count, digital screen time, adult-recorded off-screen completion and interviews; compare the full flow with delivery of the same activity without animation, with sampling/design specified in the protocol.",
    137: "-\tMeasure Gate-A adult corrections and whether corrections recover an appropriate topic/activity/objective; evaluate story/video factual citations, age suitability and output validation as separate quality measures.",
    140: "The mixed-methods study covers children under 9 (0–107 completed months) and spontaneous drawings; existing 9–12 catalog rows are outside supported-product and study scope. Use held-out data for recognition, blinded trained-Guide ratings for activity-set quality/completeness and inter-rater agreement, and separate checks for safety/supervision, citations, adult correction, off-screen completion and screen time. A household study may include observation and interviews. Its protocol defines consent, pseudonymization, access, deletion, sample, design, duration and thresholds before collection. No long-term learning benefit is claimed.",
    143: "The study tests whether an adult-supervised, source-grounded digital experience can bridge from a child's drawing to appropriate hands-on work. It evaluates multimodal understanding, complete topic/age discovery, interest ordering, adult correction, story provenance and off-screen outcomes, reports methodological limits, and makes no claim of long-term educational benefit.",
    155: "-\tThe complete digital flow is a short bridge to physical Montessori work. Evaluate adult-supervised off-screen completion and bounded screen time as primary outcomes, while preserving the exact Gate-B activity and required safety guidance through handoff.",
    156: "-\tRecognition must fail gracefully: preserve the original drawing and child description, expose uncertainty, support Gate-A correction, keep all derived media traceable and require distinct adult decisions for meaning, activity/objective and exact story script.",
    157: "-\tCapstone-trial plans for adult account holders: Khám phá (Free), 0 VND, 1 child profile and 10 credits/month; Gia đình, 99,000 VND/month, up to 3 child profiles and 30 pooled household credits/month; Lớp học, 499,000 VND/class/month, one Guide, up to 25 assigned child profiles and 120 pooled class credits/month. One-time top-ups, purchased separately from the monthly allowance: 10 credits/49,000 VND; 30/129,000 VND; 60/239,000 VND. One credit covers one complete adult-approved drawing/story experience, including standard AI outputs and normal activity handoff: reserve at session start, commit after a successful handoff, release on failure/cancellation, and make retries in the same session idempotent. Monthly paid plans renew manually; only backend-verified payment grants the time-bounded entitlement or top-up. Credits are pooled only within the household/class plan and never bypass consent, adult gates, age, safety or authorization.",
}

FORMATTED_SUFFIXES = {
    86: (None, "The prepared environment, sensitive periods, isolation of difficulty and control of error inform how adults present a selected activity and observe learning.", None),
    87: (None, "The ordered progression within each curriculum area informs adult guidance and execution context; it does not filter otherwise eligible topic-and-age discovery results.", None),
    88: (None, "For children under six, reality-oriented, adult-mediated interaction and bounded screen exposure guide the design; digital media remains a brief transition to real materials and supervised work.", None),
    89: (None, "Lowenfeld's progression helps explain why a young child's figures may be schematic rather than photographic and why adults, not image models, provide age context.", None),
    90: (None, "The domain gap between photographic training data and hand-drawn children's artwork motivates sketch-specific evaluation and uncertainty-aware representations.", None),
    91: (None, "Combining image evidence with the child's description can improve grounding, while elevated ASR error on young children's speech motivates adult assistance, transcript correction and confirmation.", None),
    92: (None, "Research on segmentation, skeleton inference and motion retargeting informs source-preserving animation of drawn figures; generated movement remains linked to the original.", None),
    93: ("Topic-and-Age-Grounded Activity Discovery:", "Return every reviewed match for the confirmed topic and exact age; apply catalog/topic/age/safety/supervision exclusions and use confirmed interests for ordering.", None),
    94: (None, "Filter and constrain child-directed generation, validate content before display and retain adult review at meaning, activity/objective and exact-script gates.", None),
    95: (None, "Adult participation changes how young children engage with media and activity, supporting Parent/Guide involvement rather than independent child use.", None),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source_bytes = args.input.read_bytes()
    source_hash = sha256(source_bytes)
    if source_hash != SOURCE_SHA256:
        raise SystemExit(f"Unexpected v1.5 source SHA-256: {source_hash}")

    document = Document(args.input)
    if len(document.paragraphs) != 159 or len(document.tables) != 3:
        raise SystemExit(f"Unexpected source structure: {len(document.paragraphs)} paragraphs, {len(document.tables)} tables")

    for index, text in REPLACEMENTS.items():
        paragraph = document.paragraphs[index]
        if len(paragraph.runs) != 1:
            raise SystemExit(f"Expected one run in paragraph {index}; found {len(paragraph.runs)}")
        paragraph.runs[0].text = text

    for index, (label, suffix, _) in FORMATTED_SUFFIXES.items():
        paragraph = document.paragraphs[index]
        if len(paragraph.runs) != 3:
            raise SystemExit(f"Expected three formatting runs in paragraph {index}; found {len(paragraph.runs)}")
        if label is not None:
            paragraph.runs[1].text = label
        paragraph.runs[2].text = f" {suffix}"

    # Keep the bullet run and the source's text styling on the literature entry.
    if len(document.paragraphs[151].runs) != 2:
        raise SystemExit("Unexpected formatting in related-works paragraph 151")
    document.paragraphs[151].runs[1].text = "Research on educational discovery using confirmed topic and exact age, preference-based ordering, and separately enforced safety/supervision constraints for activity execution."

    # Prevent section labels from being orphaned at the bottom of a page.
    for index in (73, 120, 139):
        document.paragraphs[index].paragraph_format.keep_with_next = True

    if len(document.paragraphs) != 159 or len(document.tables) != 3:
        raise SystemExit("The original form structure changed unexpectedly")
    original = Document(args.input)
    for index in range(3):
        old_table = [[cell.text for cell in row.cells] for row in original.tables[index].rows]
        new_table = [[cell.text for cell in row.cells] for row in document.tables[index].rows]
        if old_table != new_table:
            raise SystemExit(f"Original form table {index} changed")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False, dir=args.output.parent) as tmp:
        temp_path = Path(tmp.name)
    try:
        document.save(temp_path)
        with zipfile.ZipFile(args.input, "r") as source_zip, zipfile.ZipFile(temp_path, "r") as edited_zip:
            edited_xml = edited_zip.read("word/document.xml")
            with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED) as output_zip:
                for item in source_zip.infolist():
                    content = edited_xml if item.filename == "word/document.xml" else source_zip.read(item.filename)
                    output_zip.writestr(item, content)
    finally:
        temp_path.unlink(missing_ok=True)

    with zipfile.ZipFile(args.input, "r") as source_zip, zipfile.ZipFile(args.output, "r") as output_zip:
        if source_zip.namelist() != output_zip.namelist():
            raise SystemExit("DOCX package part list changed")
        changed_parts = [name for name in source_zip.namelist() if source_zip.read(name) != output_zip.read(name)]
        if changed_parts != ["word/document.xml"]:
            raise SystemExit(f"Unexpected DOCX package parts changed: {changed_parts}")

    result = Document(args.output)
    text = "\n".join(paragraph.text for paragraph in result.paragraphs)
    for expected in (
        "0–107 completed months",
        "Gate A confirms meaning only",
        "full active, reviewed set compatible with that topic and exact age",
        "before any image-generation request",
        "40–60 second",
        "complete narration/audio",
        "backend-verified payment",
        "10 credits/month",
        "30 pooled household credits/month",
        "120 pooled class credits/month",
        "held-out data",
        "inter-rater agreement",
    ):
        if expected.casefold() not in text.casefold():
            raise SystemExit(f"Required SRS-based detail missing: {expected}")
    for unwanted in (
        "aged 0-12",
        "subject to approval",
        "must be approved before collection",
        "approval gates",
        "Owner Review Draft",
        "REVIEW DRAFT",
        "provisional hypotheses",
        "waiting for owner approval",
        "SRS",
        "B33",
        "readiness, prior work, sequence and materials do not exclude",
        "hard-rule recommendation",
    ):
        if unwanted.casefold() in text.casefold():
            raise SystemExit(f"Internal or stale wording remains: {unwanted}")

    print(f"Output: {args.output}")
    print(f"Source SHA-256: {source_hash}")
    print(f"Output SHA-256: {sha256(args.output.read_bytes())}")
    print(f"Paragraphs: {len(result.paragraphs)}; tables: {len(result.tables)}")
    print("Changed DOCX package part: word/document.xml")


if __name__ == "__main__":
    main()
