# FEAT-099 research, seventh pass: fitting the video to the child (2026-11-27)

## 1. The question

Knowledge and video should fit the child's age, interests and notes. What does the product use today, what is
reasonable to build, and what data may be used?

## 2. What is used today (code read)

| Input | Where it goes | Effect on the video |
|---|---|---|
| Age in months | story model | 36–71: 5 scenes, 25 words a scene, 5 facts; 72–107: 6, 32, 6; 108–120: 7, 32, 7 (`domain/learning_script.py`) |
| Interests: one free-text field (up to 2000 characters) | reduced to at most 8 tags of an 11-tag list (`learning_request.py`) | the prompt says: setting or analogy only |
| Dislikes, fears, how the child watches best, what they asked about, what was already taught | **not collected for the story, or not used** | none |

- The writing rules are the same for a 3-year-old and a 10-year-old. The age is passed as a number; apart from the
  counts above no rule uses it (`learning_story.py` `_facts_prompt`, `_script_prompt`).
- Facts have the same three kinds at every age: what it is, parts, use.
- Knowledge cards: 40 cards, 241 facts; 217 start at 36 months, 24 at 72, **none at 108**. A 10-year-old mostly hears
  the facts written for a 3-year-old.
- The parent profile holds `display_name`, `age_months`, `interests_summary` only. The SRS also names observations,
  achievements, outside experiences, source notes (BR-19, FR-C-05/06) and restricted support needs (BR-20, FR-C-07).
- A separate activity-discovery contract has dislikes and learning supports as fixed IDs
  (`contracts/schemas/child_learning_profile.py`); the story and video path does not use it.

### 2.1 The interest filter is wrong

`evidence/interest_tags_probe.py`, result `evidence/interest_tags.json`, twelve invented sentences:

| Note | Tags found | Problem |
|---|---|---|
| mê ô tô, xe cẩu và máy xúc | sky_and_weather | "máy" read as "mây" (accents removed) |
| tìm hiểu vũ trụ và phi hành gia | colors | "tìm" read as "tím"; space missing |
| đồ chơi xếp hình | colors, building | "đồ" read as "đỏ" |
| đi mua sắm cùng mẹ | water | "mua" read as "mưa" |
| thích vẽ, thích hát | none | a comma or full stop next to a word blocks the match |
| khủng long; đá bóng; công chúa và lâu đài | none | no such words in the list |
| sợ bóng tối, không thích tiếng to | none | dislikes have no path |
| khó tập trung lâu | none | viewing needs have no path |

Cause (code read): `_fold` removes accents but keeps punctuation, and the match looks for the word between spaces.

## 3. What research says

Read through search summaries unless marked; the papers themselves were mostly not read.

| Finding | Source | How far it applies |
|---|---|---|
| Interest-based personalisation raises interest (g 0.55) and retention (g 0.48), pooled over 34 publications | [Lin et al. 2024](https://www.researchgate.net/publication/383152259_The_Personalized_Learning_by_Interest_Effect_on_Interest_Cognitive_Load_Retention_and_Transfer_A_Meta-Analysis), summary only | students in general, not shown for ages 3–10 |
| Adapting to the learner's level helped more than linking to interests only | [Major et al. 2021](https://bera-journals.onlinelibrary.wiley.com/doi/10.1111/bjet.13116), summary only | school-age, low and middle income countries |
| Interesting but irrelevant additions hurt learning a little (g −0.16, 50 studies) | meta-analysis quoted in a search summary; original paper not identified ([overview](https://en.wikipedia.org/wiki/Seductive_details)) | mostly older learners |
| In one of two studies with young children such additions lowered performance | [Colliot 2024](https://onlinelibrary.wiley.com/doi/abs/10.1111/jcal.12879), summary only | origami task; second study found no harm |
| Marking additions as side topics reduced the harm | [Wesenberg et al. 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12879520/), abstract and method read | **adults** (mean 25): not evidence for children |
| Preschool viewers answer a screen character's direct question when it pauses | [Blue's Clues research, via summary](https://en.wikipedia.org/wiki/Blue%27s_Clues) | ages 3–5; original study not read |
| Vietnamese preschool teaching: counting within 5 at 3–4, within 10 at 5–6 | school and preschool pages ([3–4](https://sakuraschools.edu.vn/nghe-lam-cha-me/lam-quen-voi-toan-cho-tre-3-4-tuoi/), [5](https://mnviethung.hanoi.edu.vn/chuong-trinh-hoc-cua-be/day-tre-5-tuoi-hoc-toan-theo-chuong-trinh-giao-duc-mam-non-day-tre-mam-non-hoc/ctmb/12444/394237)) | teacher material, not the official programme; 4–5 is inconsistent |

Not found: reliable figures for speech rate, sentence length or attention span by age for narrated video.

## 4. Data rules (not legal advice; needs a legal check)

| Point | Source and quality |
|---|---|
| Law 91/2025/QH15 and Decree 356/2025/ND-CP in force from 2026-01-01 | [law-firm and legal-news summaries](https://english.luatvietnam.vn/legal-updates/the-latest-law-on-personal-data-protection-and-the-guiding-documents-892-106778-article.html) |
| The legal representative acts for a child; disclosing private-life information of a child aged 7 or more needs the child's and the representative's consent | search summary of article 24; official text not read ([Công báo](https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2025/6/45578/57730-1-2025971-97291-2025-qh15.pdf)) |
| Health status and private-life information are sensitive data; the person must be told so when consent is asked | [Decree 356 article 4 and 6, unofficial English translation](https://english.luatvietnam.vn/decree-no-356-2025-nd-cp-dated-december-31-2025-of-the-government-detailing-a-number-of-articles-and-measures-for-the-implementation-of-the-law-on-p-422896-doc1.html) |
| No pre-ticked or unclear consent | search summary of the decree |
| Processing on servers outside Vietnam has its own assessment duty | unverified summary (decree articles 17–18) |

Whether the app's current sending of age and interest tags to a cloud GPU falls under the last row is **not checked**.

## 5. Reading

1. **Age decides what is taught and how it is shown.** It is the strongest lever and today barely used.
2. **Interest decides the example, never the fact**, and must sit inside the fact being shown, not beside it.
3. **Notes become a few fixed choices an adult ticks**: what the child is curious about, what to leave out, how to
   present. Free text about a child does not go to a model (ADR-0027, BR-18/20/21).
4. **History avoids repeats**: the next video about the same subject tells something new.
5. A wrong guess is worse than none: the app suggests choices, the adult decides, and sees what was used.
