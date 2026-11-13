# M2 Integration Merge Resolution Ledger — 2026-11-13

## DECISIONS.md byte-preserving resolution

- Integration source: 8bf5f0afacedc1e1d406c272279fcfe3a7fd44a9, 175,536 bytes, SHA-256 F57A4ECABE0C4981B0DC5FEDF00729F42D2E83BF30DCDAE0416100A126905056.
- M2 source: 77cf761d8b5bc474310f48c1996451e9e4c985c0, 184,622 bytes, SHA-256 E6199F504B5DF2EB4B375996F951D5C19E6690D319E4BF1BD47279CB0066E39D.
- Both source files have identical bytes through zero-based offset 174,235, immediately after D-188.
- Preserved the entire M2 file, including D-189 through D-193, as the result prefix. Appended the exact integration-only range [174235:175536] (1,301 bytes; SHA-256 F6C06F9570B81A1C42F363121C559C3708EC9B19AD10674E38151C369BD2574B), containing the Rev67 section and its repeated D-172 row.
- Result: 185,923 bytes; SHA-256 42B8B47F44A324DD1C5FE32B15165261F740BABA1AE4A273DA34336E70B50021. Byte checks confirmed the complete M2 source is an exact prefix and the appended suffix exactly equals the integration source range. No decision row was added.

For the later merge commit message, retain this resolution description: M2 DECISIONS.md bytes (184,622 B, SHA-256 E6199F504B5DF2EB4B375996F951D5C19E6690D319E4BF1BD47279CB0066E39D) followed by exact integration suffix [174235:175536] (1,301 B), resulting in 185,923 B / SHA-256 42B8B47F44A324DD1C5FE32B15165261F740BABA1AE4A273DA34336E70B50021.
