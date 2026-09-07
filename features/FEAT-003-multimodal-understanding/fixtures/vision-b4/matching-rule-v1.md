# vision-b4-matching-rule-v1

This is the canonical B4 matching-rule text. Its SHA-256 is referenced by the held-out manifest
and ground truth before any B4 model output is inspected.

1. Score only a schema-mapped result. A schema-invalid, model/runtime, or input failure receives
   no semantic-quality score.
2. Normalize candidate and ground-truth labels/predicates by Unicode NFC, case-folding, trimming,
   replacing hyphens with spaces, and collapsing whitespace. Do not use synonym expansion,
   stemming, model-assisted judging, aliases added after authoring, or other transformations.
3. For entities, actions, relations, and themes, build a bipartite graph whose edges join only
   items in the same collection with exactly equal normalized label/predicate values. Select a
   maximum-cardinality matching. If multiple maximum matchings exist, select the one induced by
   ascending ground-truth ID and then ascending predicted observation ID.
4. A matched action receives credit only when each non-null actor/object endpoint resolves to the
   corresponding matched ground-truth entity. A null action endpoint receives credit only when the
   corresponding ground-truth endpoint is null.
5. A matched relation receives credit only when subject/object references resolve to the
   corresponding matched ground-truth entity or action. A matched theme receives credit only when
   every evidence reference resolves to a matched authored entity, action, or relation.
6. Coverage is matched ground-truth items divided by ground-truth item count. A fixture with zero
   ground-truth items for a collection is `NOT_MEASURED` for that fixture's coverage and excluded
   from that collection's aggregate coverage denominator.
7. Accuracy is matched predicted items divided by predicted item count. A fixture with zero
   predictions for a collection is `NOT_MEASURED` for that fixture's accuracy. A nonzero predicted
   count with zero matches has accuracy `0`.
8. Confidence is not scored. Extra unmatched predictions remain in the accuracy denominator and
   unmatched ground-truth items remain in the coverage denominator.
9. Ambiguous regions report count/rate only. Their accuracy is `NOT_MEASURED` because this Phase B
   contract has no geometry or evidence-target ground truth for them.
10. Lossless complete-fence-unwrap recovery rate is reported separately as recovered runs divided
    by runs whose raw output arrived fenced. Only the safe aggregate count/rate persists; raw
    provider output never persists.
