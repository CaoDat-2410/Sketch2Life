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
}

export interface BrowserArtPlayer {
  load(input: unknown): Promise<void>;
  play(): void;
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

  const emit = (event: PlaybackEvent): void => options.onEvent?.(event);

  return {
    async load(input: unknown): Promise<void> {
      timeline?.kill();
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

          const texture = await Assets.load<Texture>(instruction.uri);
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
      lastBenchmark = createRendererBenchmarkSample(plan.planId, startedAt, performance.now(), 0);
    },

    play(): void {
      if (loaded === null) {
        throw new Error('Load an art animation plan before playback.');
      }

      timeline?.kill();
      const playbackStartedAt = performance.now();
      let framesRendered = 0;
      const countFrame = (): void => {
        framesRendered += 1;
      };
      options.app.ticker.add(countFrame);

      const compiledMotions = compileMotionPlan(loaded.plan);
      timeline = gsap.timeline({
        paused: true,
        onComplete: () => {
          options.app.ticker.remove(countFrame);
          lastBenchmark = createRendererBenchmarkSample(
            loaded?.plan.planId ?? 'unknown-plan',
            playbackStartedAt,
            performance.now(),
            framesRendered,
          );
          emit({type: 'PLAYBACK_COMPLETED', planId: loaded?.plan.planId ?? 'unknown-plan'});
        },
      });

      for (const motion of compiledMotions) {
        const sprite = loaded.sprites.get(motion.targetId);
        if (sprite === undefined) {
          options.app.ticker.remove(countFrame);
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
      timeline.play(0);
    },

    destroy(): void {
      timeline?.kill();
      scene.destroy({children: true});
      loaded = null;
    },

    getLastBenchmark(): RendererBenchmarkSample | null {
      return lastBenchmark;
    },
  };
}
