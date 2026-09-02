# Phase 4 - Generation brief and provider adapter

## Responsibility

`GenerationBriefCompiler` turns one learning objective into the bounded `GenerationBrief` input contract for a video provider. `GenerationProvider` is the provider-neutral interface. `MockGenerator` exercises that interface without downloading a model or requiring a GPU.

## Flow

```text
LearningObjective
  -> GenerationBrief
  -> GenerationProvider.generate()
  -> GeneratedVideo metadata
```

The provider receives exactly one objective identity/version and a bounded duration of 5-10 seconds. The output records the provider and provenance so the later Wan2.2 implementation can be substituted without changing the resolver or pipeline.

## Why mock first

- Contract and pipeline tests remain fast and reproducible.
- Cache and generation behavior can be tested without GPU cost.
- Wan2.2-specific failures stay inside its adapter.
- The mock returns metadata only; real MP4 integrity belongs to the FFmpeg phase.

## Provider substitution

```text
MockGenerator.generate(brief)
Wan2Generator.generate(brief)
                 ↓
       GeneratedVideo
```

Both providers implement the same `GenerationProvider` protocol.
