import { describe, expect, it, vi } from 'vitest';
import type { AuthTokenPort } from '../src/parent/application/ports/ParentPorts';
import { readMainActivityV1, readVideoPanel } from '../src/parent/application/parentPhaseB';
import type { ParentStoryRunV1 } from '../src/parent/domain/types';
import { ParentApi } from '../src/parent/infrastructure/http/ParentApi';
import { VideoScreen } from '../src/parent/presentation/screens/VideoScreen';

vi.mock('react', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react')>();
  return {
    ...actual,
    useEffect: () => undefined,
    useState: (initial: unknown) => [initial, () => undefined],
  };
});

vi.mock('react-native', () => ({
  ActivityIndicator: 'ActivityIndicator',
  Platform: { OS: 'ios' },
  Pressable: 'Pressable',
  StyleSheet: { create: (styles: unknown) => styles },
  Text: 'Text',
  TouchableOpacity: 'TouchableOpacity',
  View: 'View',
}));

vi.mock('expo-av', () => ({ ResizeMode: { CONTAIN: 'contain' }, Video: 'Video' }));
vi.mock('expo-file-system', () => ({ documentDirectory: null }));
vi.mock('@expo/vector-icons', () => ({ Ionicons: 'Ionicons' }));
vi.mock('../src/parent/infrastructure/config', () => ({ parentConfig: { apiBaseUrl: 'https://api.example.test' } }));
vi.mock('../src/parent/presentation/components/ui', () => ({
  Card: 'Card',
  ConfirmButton: 'ConfirmButton',
  Notice: 'Notice',
  PrimaryButton: 'PrimaryButton',
  ScreenFrame: 'ScreenFrame',
  SecondaryButton: 'SecondaryButton',
  SectionTitle: 'SectionTitle',
  palette: {
    creativeBorder: '#ddd',
    creativeInk: '#222',
    creativeLavender: '#eee',
    creativeMuted: '#666',
    creativePrimary: '#55f',
    white: '#fff',
  },
}));

const catalogActivity = {
  activity_ref: { lesson_id: 'lesson-1', version_id: 'version-1', content_sha256: 'a'.repeat(64), activity_index: 0 },
  title: 'Catalog activity', objective: 'Objective', materials_text: 'Materials', preparation_text: 'Preparation',
  instructions_text: 'Instructions', observation_notes: 'Observation', safety_notes: 'Safety', activity_kind: 'indoor',
  source: 'PUBLIC', lesson_title: 'Lesson title', lesson_topic: 'Topic',
};

const aiDraftActivity = {
  activity_ref: null,
  title: 'AI draft activity', objective: 'Draft objective', materials_text: 'Materials', preparation_text: 'Preparation',
  instructions_text: 'Instructions', observation_notes: 'Observation', safety_notes: 'Safety', activity_kind: 'mixed',
  source: 'AI_DRAFT', lesson_title: '', lesson_topic: '',
};

function apiWithRunResponse(storyRun: Record<string, unknown>) {
  const auth: AuthTokenPort = { getIdToken: async () => 'synthetic-token' };
  const fetcher = async () => new Response(JSON.stringify({ request_id: 'run-read', story_run: storyRun }), { status: 200 });
  return new ParentApi(auth, fetcher as typeof fetch, 'https://api.example.test');
}

function renderedStrings(node: unknown): string[] {
  if (typeof node === 'string' || typeof node === 'number') return [String(node)];
  if (Array.isArray(node)) return node.flatMap(renderedStrings);
  if (typeof node !== 'object' || node === null || !('props' in node)) return [];
  return renderedStrings((node as { props: { children?: unknown } }).props.children);
}

describe('Parent AI_DRAFT projection reader', () => {
  it('keeps AI_DRAFT main activities with null references in the live run reader and preserves Phase A runs', async () => {
    const run = {
      run_id: 'synthetic-run',
      main_activity: { state: 'SELECTED', selected: aiDraftActivity, selected_at: '2026-11-25T00:00:00Z' },
    };
    const result = await apiWithRunResponse(run).getStoryRunV1('synthetic-run');

    expect('story_run' in result && result.story_run.main_activity).toMatchObject({
      state: 'SELECTED', selected: { source: 'AI_DRAFT', activity_ref: null },
    });

    const phaseARun = await apiWithRunResponse({ run_id: 'synthetic-run' }).getStoryRunV1('synthetic-run');
    expect('story_run' in phaseARun && phaseARun.story_run.main_activity).toBeUndefined();
  });

  it('rejects invalid selected projections on the live run read', async () => {
    const invalidRun = {
      run_id: 'synthetic-run',
      main_activity: {
        state: 'SELECTED',
        selected: { ...aiDraftActivity, activity_ref: catalogActivity.activity_ref },
        selected_at: '2026-11-25T00:00:00Z',
      },
    };

    await expect(apiWithRunResponse(invalidRun).getStoryRunV1('synthetic-run'))
      .rejects.toMatchObject({ code: 'INVALID_API_RESPONSE', status: 200 });
    expect(readMainActivityV1({
      state: 'SELECTED', selected: { ...catalogActivity, activity_ref: null }, selected_at: '2026-11-25T00:00:00Z',
    })).toBeNull();
  });

  it('renders the AI main activity after playback with the adult-reviewed AI copy', () => {
    const run = {
      run_id: 'synthetic-run',
      run_state: 'COMPLETED',
      main_activity: { state: 'SELECTED', selected: aiDraftActivity, selected_at: '2026-11-25T00:00:00Z' },
      post_video_activities: [
        { ...catalogActivity, is_main: false },
        { ...catalogActivity, activity_ref: { ...catalogActivity.activity_ref, activity_index: 1 }, title: 'Second catalog activity', is_main: false },
        { ...aiDraftActivity, is_main: true },
      ],
    } as unknown as ParentStoryRunV1;
    const panel = readVideoPanel(run);
    const screen = VideoScreen({
      stepLabel: 'Step', panel, busy: '', error: '', quotaExceeded: false, quotaSummary: null, playback: null, runId: null, activity: null, reason: null, markingUnsuitable: false,
      onReason: () => {}, onRequest: () => {}, onPlay: () => {}, onPlaybackError: () => {},
      onStartUnsuitable: () => {}, onCancelUnsuitable: () => {}, onConfirmUnsuitable: () => {}, onComplete: () => {},
      onBackToStory: () => {}, onOpenHistory: () => {}, onRefresh: () => {}, onOpenQuota: () => {}, onBack: () => {},
    });
    const output = renderedStrings(screen).join(' ');

    expect(panel.postVideoActivities).toHaveLength(3);
    expect(output).toContain('AI draft activity');
    expect(output).toContain('Draft objective');
    expect(output).toContain('Gợi ý AI');
    expect(output).toContain('được người lớn xem lại và chọn làm hoạt động chính');
  });
});
