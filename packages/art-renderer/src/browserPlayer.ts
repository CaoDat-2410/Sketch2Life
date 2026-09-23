import {Assets, Container, Sprite, Texture, type Application} from 'pixi.js';
import {gsap} from 'gsap';

import {loadChildArtAssetInstructions} from './assets';
import {createRendererBenchmarkSample, type RendererBenchmarkSample} from './benchmark';
import type {ArtAnimationPlan, PlaybackEvent, Transform} from './contracts';
import {buildPreservingFallbackPlan} from './fallback';
import {compileMotionPlan} from './motion';
import {validateArtAnimationPlan} from './validation';

export interface BrowserArtPlayerOptions {
  readonly app: Application;
  readonly onEvent?: (event: PlaybackEvent) => void;
  readonly loadTexture?: (uri: string) => Promise<Texture>;
  readonly onProgress?: (state: BrowserPlaybackState) => void;
}

export interface BrowserPlaybackState {
  readonly positionSeconds: number;
  readonly durationSeconds: number;
  readonly state: 'READY' | 'PLAYING' | 'PAUSED' | 'COMPLETED';
}

export interface BrowserArtPlayer {
  load(input: unknown): Promise<void>;
  play(): void;
  pause(): void;
  replay(): void;
  seekTo(seconds: number): void;
  seekRelative(seconds: number): void;
  getPlaybackState(): BrowserPlaybackState;
  destroy(): void;
  getLastBenchmark(): RendererBenchmarkSample | null;
}

interface LoadedPlan {
  readonly plan: ArtAnimationPlan;
  readonly sprites: ReadonlyMap<string, Sprite>;
  readonly loadedAt: number;
}

function setTransform(sprite: Sprite, transform: Transform, plan: ArtAnimationPlan): void {
  sprite.position.set(transform.position.x * plan.stage.width, transform.position.y * plan.stage.height);
  sprite.scale.set(transform.scale);
  sprite.rotation = (transform.rotationDegrees * Math.PI) / 180;
  sprite.alpha = transform.opacity;
}

/**
 * Browser-only standalone player. It accepts an already-created PixiJS
 * application so the demo and the later React Native WebView bridge can own
 * their own canvas lifecycle while sharing the same validated runtime.
 */
export function createBrowserArtPlayer(options: BrowserArtPlayerOptions): BrowserArtPlayer {
  const scene = new Container();
  options.app.stage.addChild(scene);

  let loaded: LoadedPlan | null = null;
  let timeline: gsap.core.Timeline | null = null;
  let lastBenchmark: RendererBenchmarkSample | null = null;
  let frameCounter: (() => void) | null = null;
  let playbackStartedAt = 0;
  let framesRendered = 0;
  let playbackState: BrowserPlaybackState = {
    positionSeconds: 0,
    durationSeconds: 0,
    state: 'READY',
  };

  const emit = (event: PlaybackEvent): void => options.onEvent?.(event);
  const publishProgress = (state: BrowserPlaybackState): void => {
    playbackState = state;
    options.onProgress?.(state);
  };
  const clampTime = (seconds: number): number => Math.min(
    Math.max(Number.isFinite(seconds) ? seconds : 0, 0),
    timeline?.duration() ?? playbackState.durationSeconds,
  );
  const stopFrameCounter = (): void => {
    if (frameCounter === null) return;
    options.app.ticker.remove(frameCounter);
    frameCounter = null;
  };
  const startFrameCounter = (reset = false): void => {
    stopFrameCounter();
    if (reset) {
      playbackStartedAt = performance.now();
      framesRendered = 0;
    }
    frameCounter = () => {
      framesRendered += 1;
    };
    options.app.ticker.add(frameCounter);
  };

  return {
    async load(input: unknown): Promise<void> {
      stopFrameCounter();
      timeline?.kill();
      timeline = null;
      scene.removeChildren();
      lastBenchmark = null;

      let plan = validateArtAnimationPlan(input);
      const fallbackObject = plan.objects.find((object) => object.extractionStatus === 'FALLBACK_REQUIRED');
      if (fallbackObject !== undefined) {
        const fallback = buildPreservingFallbackPlan(plan, 'EXTRACTION_UNAVAILABLE');
        plan = fallback.plan;
        emit({type: 'FALLBACK_APPLIED', planId: plan.planId, reason: fallback.reason});
      }

      const startedAt = performance.now();
      options.app.renderer.resize(plan.stage.width, plan.stage.height);
      const spriteEntries = await Promise.all(
        loadChildArtAssetInstructions(plan).map(async (instruction) => {
          const object = plan.objects.find((candidate) => candidate.id === instruction.objectId);
          if (object === undefined) {
            throw new Error(`Asset instruction has no matching object: ${instruction.objectId}`);
          }

          const texture = options.loadTexture === undefined
            ? await Assets.load<Texture>(instruction.uri)
            : await options.loadTexture(instruction.uri);
          const sprite = new Sprite(texture);
          sprite.anchor.set(0.5);
          setTransform(sprite, object.initialTransform, plan);
          scene.addChild(sprite);
          return [object.id, sprite] as const;
        }),
      );

      loaded = {
        plan,
        sprites: new Map(spriteEntries),
        loadedAt: startedAt,
      };
      publishProgress({positionSeconds: 0, durationSeconds: 0, state: 'READY'});
      lastBenchmark = createRendererBenchmarkSample(plan.planId, startedAt, performance.now(), 0);
    },

    play(): void {
      if (loaded === null) {
        throw new Error('Load an art animation plan before playback.');
      }

      if (timeline !== null) {
        startFrameCounter();
        timeline.play();
        publishProgress({
          positionSeconds: timeline.time(),
          durationSeconds: timeline.duration(),
          state: 'PLAYING',
        });
        return;
      }

      startFrameCounter(true);

      const compiledMotions = compileMotionPlan(loaded.plan);
      timeline = gsap.timeline({
        paused: true,
        onUpdate: () => {
          if (timeline === null) return;
          publishProgress({
            positionSeconds: timeline.time(),
            durationSeconds: timeline.duration(),
            state: timeline.paused() ? 'PAUSED' : 'PLAYING',
          });
        },
        onComplete: () => {
          stopFrameCounter();
          lastBenchmark = createRendererBenchmarkSample(
            loaded?.plan.planId ?? 'unknown-plan',
            playbackStartedAt,
            performance.now(),
            framesRendered,
          );
          emit({type: 'PLAYBACK_COMPLETED', planId: loaded?.plan.planId ?? 'unknown-plan'});
          const durationSeconds = timeline?.duration() ?? playbackState.durationSeconds;
          publishProgress({
            positionSeconds: durationSeconds,
            durationSeconds,
            state: 'COMPLETED',
          });
        },
      });

      for (const motion of compiledMotions) {
        const sprite = loaded.sprites.get(motion.targetId);
        if (sprite === undefined) {
          stopFrameCounter();
          emit({
            type: 'PLAYBACK_FAILED',
            planId: loaded.plan.planId,
            reason: `Unknown sprite target ${motion.targetId}.`,
          });
          throw new Error(`Unknown sprite target ${motion.targetId}.`);
        }

        const duration = motion.durationSeconds;
        switch (motion.kind) {
          case 'DRAW_REVEAL':
            timeline.set(sprite, {alpha: 0}).to(sprite, {alpha: 1, duration});
            break;
          case 'MOVE':
          case 'MOVE_TO':
          case 'FLY':
          case 'JUMP':
            timeline.to(sprite, {
              x: (motion.to?.x ?? 0.5) * loaded.plan.stage.width,
              y: (motion.to?.y ?? 0.5) * loaded.plan.stage.height,
              duration,
              ease: motion.kind === 'JUMP' ? 'power2.out' : 'sine.inOut',
            });
            break;
          case 'SCALE':
            timeline.to(sprite.scale, {x: motion.scale, y: motion.scale, duration, ease: 'sine.inOut'});
            break;
          case 'ROTATE':
            timeline.to(sprite, {
              rotation: ((motion.rotationDegrees ?? 0) * Math.PI) / 180,
              duration,
              ease: 'sine.inOut',
            });
            break;
          case 'FADE':
            timeline.to(sprite, {alpha: motion.opacity, duration});
            break;
        }
      }

      emit({type: 'PLAYBACK_STARTED', planId: loaded.plan.planId});
      publishProgress({
        positionSeconds: 0,
        durationSeconds: timeline.duration(),
        state: 'PLAYING',
      });
      timeline.play(0);
    },

    pause(): void {
      if (timeline === null) return;
      timeline.pause();
      stopFrameCounter();
      publishProgress({
        positionSeconds: timeline.time(),
        durationSeconds: timeline.duration(),
        state: 'PAUSED',
      });
    },

    replay(): void {
      if (timeline === null) {
        throw new Error('Play an art animation plan before replay.');
      }
      emit({type: 'PLAYBACK_STARTED', planId: loaded?.plan.planId ?? 'unknown-plan'});
      startFrameCounter(true);
      publishProgress({positionSeconds: 0, durationSeconds: timeline.duration(), state: 'PLAYING'});
      timeline.restart();
    },

    seekTo(seconds: number): void {
      if (timeline === null) return;
      const next = clampTime(seconds);
      timeline.time(next, false);
      publishProgress({...playbackState, positionSeconds: next, durationSeconds: timeline.duration()});
    },

    seekRelative(seconds: number): void {
      if (timeline === null) return;
      const next = clampTime(timeline.time() + seconds);
      timeline.time(next, false);
      publishProgress({...playbackState, positionSeconds: next, durationSeconds: timeline.duration()});
    },

    getPlaybackState(): BrowserPlaybackState {
      return playbackState;
    },

    destroy(): void {
      stopFrameCounter();
      timeline?.kill();
      timeline = null;
      scene.destroy({children: true});
      loaded = null;
      playbackState = {positionSeconds: 0, durationSeconds: 0, state: 'READY'};
    },

    getLastBenchmark(): RendererBenchmarkSample | null {
      return lastBenchmark;
    },
  };
}
