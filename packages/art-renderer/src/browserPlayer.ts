import {Assets, Container, Graphics, Rectangle, Sprite, Texture, type Application} from 'pixi.js';
import {gsap} from 'gsap';

import {loadChildArtAssetInstructions} from './assets';
import {createRendererBenchmarkSample, type RendererBenchmarkSample} from './benchmark';
import type {
  ArtAnimationPlan,
  PlaybackEvent,
  RendererInteractionPhase,
  SceneExplorationPlan,
  SceneFocusPlan,
  SourceRegion,
  Transform,
} from './contracts';
import {buildPreservingFallbackPlan} from './fallback';
import {compileMotionPlan} from './motion';
import {validateArtAnimationPlan} from './validation';

export interface BrowserArtPlayerOptions {
  readonly app: Application;
  readonly onEvent?: (event: PlaybackEvent) => void;
  readonly loadTexture?: (uri: string, sourceRegion?: SourceRegion) => Promise<Texture>;
  readonly onProgress?: (state: BrowserPlaybackState) => void;
}

export interface BrowserArtPlayerLoadOptions {
  readonly sceneExplorationPlan?: SceneExplorationPlan;
  readonly sceneFocusPlan?: SceneFocusPlan;
}

export interface BrowserPlaybackState {
  readonly positionSeconds: number;
  readonly durationSeconds: number;
  readonly state: 'READY' | 'PLAYING' | 'PAUSED' | 'COMPLETED';
  readonly interactionPhase: RendererInteractionPhase;
}

export interface BrowserArtPlayer {
  load(input: unknown, context?: BrowserArtPlayerLoadOptions): Promise<void>;
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
  readonly context: BrowserArtPlayerLoadOptions;
  readonly sprites: ReadonlyMap<string, Sprite>;
  readonly focusFrames: ReadonlyMap<string, Graphics>;
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
    interactionPhase: 'INTRO_LOADING',
  };
  let interactionPhase: RendererInteractionPhase = 'INTRO_LOADING';
  let lastFocusObjectId: string | null = null;
  let lastFocusAt = 0;

  const emit = (event: PlaybackEvent): void => options.onEvent?.(event);
  const publishProgress = (state: BrowserPlaybackState): void => {
    playbackState = state;
    options.onProgress?.(state);
  };
  const setInteractionPhase = (next: RendererInteractionPhase): void => {
    interactionPhase = next;
    publishProgress({...playbackState, interactionPhase: next});
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
    async load(input: unknown, context: BrowserArtPlayerLoadOptions = {}): Promise<void> {
      stopFrameCounter();
      timeline?.kill();
      timeline = null;
      scene.removeAllListeners();
      scene.removeChildren().forEach((child) => child.destroy());
      lastBenchmark = null;
      interactionPhase = 'INTRO_LOADING';
      lastFocusObjectId = null;
      lastFocusAt = 0;

      let plan = validateArtAnimationPlan(input);
      const fallbackObject = plan.objects.find((object) => object.extractionStatus === 'FALLBACK_REQUIRED');
      if (fallbackObject !== undefined) {
        const fallback = buildPreservingFallbackPlan(plan, 'EXTRACTION_UNAVAILABLE');
        plan = fallback.plan;
        emit({type: 'FALLBACK_APPLIED', planId: plan.planId, reason: fallback.reason});
      }

      const startedAt = performance.now();
      options.app.renderer.resize(plan.stage.width, plan.stage.height);
      scene.eventMode = 'static';
      scene.sortableChildren = true;
      scene.hitArea = new Rectangle(0, 0, plan.stage.width, plan.stage.height);
      scene.on('pointertap', (event) => {
        if (event.target !== scene) return;
        if (interactionPhase !== 'DISCOVERY_READY' && interactionPhase !== 'DISCOVERY_FOCUSED' && interactionPhase !== 'FALLBACK') return;
        emit({type: 'CANVAS_TAPPED', planId: plan.planId});
      });
      const spriteEntries = await Promise.all(
        loadChildArtAssetInstructions(plan).map(async (instruction, targetOrder) => {
          const object = plan.objects.find((candidate) => candidate.id === instruction.objectId);
          if (object === undefined) {
            throw new Error(`Asset instruction has no matching object: ${instruction.objectId}`);
          }

          const texture = options.loadTexture === undefined
            ? await Assets.load<Texture>(instruction.uri)
            : await options.loadTexture(instruction.uri, instruction.sourceRegion);
          const sprite = new Sprite(texture);
          sprite.anchor.set(0.5);
          setTransform(sprite, object.initialTransform, plan);
          if (object.interactive) {
            const focusTarget = context.sceneFocusPlan?.targets.find(
              (target) => `focus-${target.targetRef}` === object.id,
            );
            const hitSlop = focusTarget?.hitSlop ?? 0;
            const localSlopX = (plan.stage.width * hitSlop) / Math.max(sprite.scale.x, 0.01);
            const localSlopY = (plan.stage.height * hitSlop) / Math.max(sprite.scale.y, 0.01);
            sprite.hitArea = new Rectangle(
              -sprite.texture.width / 2 - localSlopX,
              -sprite.texture.height / 2 - localSlopY,
              sprite.texture.width + localSlopX * 2,
              sprite.texture.height + localSlopY * 2,
            );
            sprite.zIndex = (focusTarget?.depthLayer ?? 1) * 1000
              + Math.round((focusTarget?.regionConfidence ?? 0) * 100)
              + targetOrder;
            sprite.eventMode = 'static';
            sprite.cursor = 'pointer';
            sprite.on('pointertap', () => {
              if (interactionPhase !== 'DISCOVERY_READY' && interactionPhase !== 'DISCOVERY_FOCUSED') return;
              const now = performance.now();
              if (lastFocusObjectId === object.id && now - lastFocusAt < 350) return;
              lastFocusObjectId = object.id;
              lastFocusAt = now;
              for (const [frameId, frame] of loaded?.focusFrames ?? []) {
                gsap.to(frame, {
                  alpha: frameId === object.id ? 1 : 0.22,
                  duration: 0.22,
                  overwrite: true,
                });
              }
              setInteractionPhase('DISCOVERY_FOCUSED');
              emit({
                type: 'FOCUS_CHANGED',
                planId: plan.planId,
                objectId: object.id,
              });
              emit({
                type: 'DISCOVERED_ENTITY',
                planId: plan.planId,
                objectId: object.id,
                labelVi: object.label,
              });
            });
          }
          scene.addChild(sprite);
          return [object.id, sprite] as const;
        }),
      );
      const focusFrames = new Map<string, Graphics>();
      for (const target of context.sceneFocusPlan?.targets ?? []) {
        if (target.sourceRegion === undefined) continue;
        const frame = new Graphics()
          .roundRect(
            target.sourceRegion.x * plan.stage.width,
            target.sourceRegion.y * plan.stage.height,
            target.sourceRegion.width * plan.stage.width,
            target.sourceRegion.height * plan.stage.height,
            18,
          )
          .stroke({color: 0x2563eb, width: 4, alpha: 0.92});
        frame.alpha = 0;
        frame.eventMode = 'none';
        frame.zIndex = 3000;
        scene.addChild(frame);
        focusFrames.set(`focus-${target.targetRef}`, frame);
      }

      loaded = {
        plan,
        context,
        sprites: new Map(spriteEntries),
        focusFrames,
        loadedAt: startedAt,
      };
      if (context.sceneFocusPlan?.extractionStatus === 'FALLBACK_REQUIRED') {
        interactionPhase = 'FALLBACK';
      }
      publishProgress({positionSeconds: 0, durationSeconds: 0, state: 'READY', interactionPhase});
      lastBenchmark = createRendererBenchmarkSample(plan.planId, startedAt, performance.now(), 0);
    },

    play(): void {
      if (loaded === null) {
        throw new Error('Load an art animation plan before playback.');
      }

      if (timeline !== null) {
        startFrameCounter();
        timeline.play();
        setInteractionPhase('INTRO_PLAYING');
        publishProgress({
          positionSeconds: timeline.time(),
          durationSeconds: timeline.duration(),
          state: 'PLAYING',
          interactionPhase,
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
            interactionPhase,
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
          const planId = loaded?.plan.planId ?? 'unknown-plan';
          emit({type: 'PLAYBACK_COMPLETED', planId});
          emit({type: 'INTRO_COMPLETED', planId});
          const focusReady = loaded?.context.sceneFocusPlan?.extractionStatus === 'READY';
          if (focusReady) {
            interactionPhase = 'DISCOVERY_READY';
            emit({
              type: 'DISCOVERY_READY',
              planId,
              targetCount: loaded?.context.sceneFocusPlan?.targets.length ?? 0,
            });
          } else {
            interactionPhase = 'FALLBACK';
            emit({type: 'FALLBACK_APPLIED', planId, reason: 'EXTRACTION_UNAVAILABLE'});
          }
          const durationSeconds = timeline?.duration() ?? playbackState.durationSeconds;
          publishProgress({
            positionSeconds: durationSeconds,
            durationSeconds,
            state: 'COMPLETED',
            interactionPhase,
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
            if (loaded.focusFrames.has(motion.targetId)) {
              const frame = loaded.focusFrames.get(motion.targetId);
              if (frame !== undefined) {
                timeline.to(frame, {alpha: 0.9, duration}, '<');
              }
            }
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
        interactionPhase: 'INTRO_PLAYING',
      });
      interactionPhase = 'INTRO_PLAYING';
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
        interactionPhase,
      });
    },

    replay(): void {
      if (timeline === null) {
        throw new Error('Play an art animation plan before replay.');
      }
      emit({type: 'PLAYBACK_STARTED', planId: loaded?.plan.planId ?? 'unknown-plan'});
      startFrameCounter(true);
      interactionPhase = 'INTRO_PLAYING';
      lastFocusObjectId = null;
      lastFocusAt = 0;
      publishProgress({positionSeconds: 0, durationSeconds: timeline.duration(), state: 'PLAYING', interactionPhase});
      timeline.restart();
    },

    seekTo(seconds: number): void {
      if (timeline === null) return;
      const next = clampTime(seconds);
      timeline.time(next, false);
      publishProgress({...playbackState, positionSeconds: next, durationSeconds: timeline.duration(), interactionPhase});
    },

    seekRelative(seconds: number): void {
      if (timeline === null) return;
      const next = clampTime(timeline.time() + seconds);
      timeline.time(next, false);
      publishProgress({...playbackState, positionSeconds: next, durationSeconds: timeline.duration(), interactionPhase});
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
      interactionPhase = 'INTRO_LOADING';
      lastFocusObjectId = null;
      lastFocusAt = 0;
      playbackState = {positionSeconds: 0, durationSeconds: 0, state: 'READY', interactionPhase};
    },

    getLastBenchmark(): RendererBenchmarkSample | null {
      return lastBenchmark;
    },
  };
}
