import {Application} from 'pixi.js';

import {
  createBrowserArtPlayer,
  type PlaybackEvent,
} from '../src/index';
import butterflyPlan from '../fixtures/butterfly/art_animation_plan.json';
import fallbackPlan from '../fixtures/butterfly/bad-extraction-plan.json';
import butterflyDrawingUrl from '../fixtures/butterfly/drawing.svg';

const stage = document.querySelector<HTMLElement>('#stage');
const eventLog = document.querySelector<HTMLPreElement>('#events');
const playButton = document.querySelector<HTMLButtonElement>('#play');
const fallbackButton = document.querySelector<HTMLButtonElement>('#fallback');

if (stage === null || eventLog === null || playButton === null || fallbackButton === null) {
  throw new Error('Demo host elements are missing.');
}

const app = new Application();
await app.init({width: 800, height: 600, background: '#fffdf6', antialias: true});
stage.append(app.canvas);

const log = (event: PlaybackEvent): void => {
  eventLog.textContent = `${eventLog.textContent ?? ''}${JSON.stringify(event)}\n`;
};

const player = createBrowserArtPlayer({app, onEvent: log});

function withBundledFixtureAsset(plan: unknown): unknown {
  const copy = structuredClone(plan) as {
    objects: Array<{asset: {uri: string}}>;
  };
  for (const object of copy.objects) {
    object.asset.uri = butterflyDrawingUrl;
  }
  return copy;
}

async function loadAndPlay(plan: unknown): Promise<void> {
  try {
    eventLog.textContent = '';
    await player.load(plan);
    player.play();
  } catch (error) {
    eventLog.textContent = `Playback failed: ${String(error)}`;
  }
}

playButton.addEventListener('click', () => void loadAndPlay(withBundledFixtureAsset(butterflyPlan)));
fallbackButton.addEventListener('click', () => void loadAndPlay(withBundledFixtureAsset(fallbackPlan)));

const requestedFixture = new URLSearchParams(window.location.search).get('fixture');
if (requestedFixture === 'normal') {
  void loadAndPlay(withBundledFixtureAsset(butterflyPlan));
}
if (requestedFixture === 'fallback') {
  void loadAndPlay(withBundledFixtureAsset(fallbackPlan));
}
