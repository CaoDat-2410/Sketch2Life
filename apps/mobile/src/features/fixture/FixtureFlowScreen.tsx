import React, {useReducer, useState} from 'react';
import {
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import {
  FIXTURE_CONTRACTS,
  createInitialFixtureFlow,
  reduceFixtureFlow,
  type FixtureFlowStep,
} from './fixtureFlow';
import {requestLiveUnderstanding} from '../../infrastructure/api/liveUnderstanding';

type StepDefinition = Readonly<{key: FixtureFlowStep; label: string}>;

const defaultBackendBaseUrl =
  (globalThis as typeof globalThis & {__SKETCH2LIFE_BACKEND_URL__?: string})
    .__SKETCH2LIFE_BACKEND_URL__ ?? 'http://10.0.2.2:8000';

const steps: readonly StepDefinition[] = [
  {key: 'capture', label: 'Capture'},
  {key: 'gate-a', label: 'Gate A'},
  {key: 'gate-b', label: 'Gate B'},
  {key: 'experience', label: 'Experience'},
  {key: 'handoff', label: 'Activity'},
  {key: 'feedback', label: 'Feedback'},
];

export function FixtureFlowScreen(): React.JSX.Element {
  const [state, dispatch] = useReducer(
    reduceFixtureFlow,
    undefined,
    createInitialFixtureFlow,
  );
  const [liveError, setLiveError] = useState<string | null>(null);
  const currentStepIndex = steps.findIndex((step) => step.key === state.step);

  async function handleLiveAi(): Promise<void> {
    setLiveError(null);
    dispatch({type: 'START_LIVE_AI'});
    try {
      const result = await requestLiveUnderstanding({
        baseUrl: defaultBackendBaseUrl,
        sessionId: FIXTURE_CONTRACTS.sessionId,
        expectedSessionVersion: state.sessionVersion,
        fixtureId: 'integration-fixture-v1',
      });
      dispatch({type: 'LIVE_AI_SUCCEEDED', label: result.proposal_label});
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Live backend request failed';
      setLiveError(message);
      dispatch({type: 'LIVE_AI_FAILED', message});
    }
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.header}>
          <View>
            <Text style={styles.eyebrow}>SKETCH2LIFE · FIXTURE LAB</Text>
            <Text style={styles.title}>A small idea can move</Text>
            <Text style={styles.subtitle}>
              Full-flow UI test with deterministic AI contracts
            </Text>
          </View>
          <View style={styles.statusPill}>
            <Text style={styles.statusPillText}>{state.aiMode === 'live-backend' ? 'BACKEND' : 'FIXTURE'}</Text>
          </View>
        </View>

        <View style={styles.progressCard}>
          <Text style={styles.sectionLabel}>SUPERVISED SESSION</Text>
          <Text style={styles.sessionId}>{FIXTURE_CONTRACTS.sessionId}</Text>
          <View style={styles.progressRow}>
            {steps.map((step, index) => (
              <View key={step.key} style={styles.progressItem}>
                <View
                  style={[
                    styles.progressDot,
                    index <= currentStepIndex && styles.progressDotActive,
                  ]}
                >
                  <Text style={styles.progressDotText}>{index + 1}</Text>
                </View>
                <Text
                  style={[
                    styles.progressLabel,
                    index <= currentStepIndex && styles.progressLabelActive,
                  ]}
                >
                  {step.label}
                </Text>
              </View>
            ))}
          </View>
        </View>

        <View style={styles.contractBanner}>
          <Text style={styles.contractTitle}>AI proposal boundary</Text>
          <Text style={styles.contractText}>
            P2 contract v{FIXTURE_CONTRACTS.contractVersion} · no provider URL,
            token, or child data
          </Text>
        </View>

        {state.step === 'capture' && (
          <CaptureStep
            aiStatus={state.aiStatus}
            error={liveError ?? state.aiError}
            onRunAi={() => dispatch({type: 'RUN_FIXTURE_AI'})}
            onRunLiveAi={handleLiveAi}
          />
        )}
        {state.step === 'gate-a' && (
          <GateAStep
            mode={state.aiMode}
            proposalLabel={state.proposalLabel}
            onConfirm={() => dispatch({type: 'CONFIRM_GATE_A'})}
          />
        )}
        {state.step === 'gate-b' && (
          <GateBStep onApprove={() => dispatch({type: 'APPROVE_GATE_B'})} />
        )}
        {state.step === 'experience' && (
          <ExperienceStep
            mediaStatus={state.mediaStatus}
            onPlay={() => dispatch({type: 'PLAY_EXPERIENCE'})}
            onFallback={() => dispatch({type: 'SIMULATE_MEDIA_FALLBACK'})}
          />
        )}
        {state.step === 'handoff' && (
          <HandoffStep onStart={() => dispatch({type: 'START_ACTIVITY'})} />
        )}
        {state.step === 'feedback' && (
          <FeedbackStep onSubmit={() => dispatch({type: 'SUBMIT_FEEDBACK'})} />
        )}
        {state.step === 'complete' && (
          <CompleteStep onReset={() => dispatch({type: 'RESET'})} />
        )}

        <View style={styles.footerRow}>
          <Text style={styles.footerText}>
            Session v{state.sessionVersion} · P1 identity locked
          </Text>
          <Text style={styles.footerText}>Renderer: {state.rendererStatus}</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function CaptureStep({
  aiStatus,
  error,
  onRunAi,
  onRunLiveAi,
}: Readonly<{
  aiStatus: 'idle' | 'loading' | 'ready' | 'error';
  error: string | null;
  onRunAi: () => void;
  onRunLiveAi: () => void;
}>): React.JSX.Element {
  const liveLoading = aiStatus === 'loading';
  return (
    <View style={styles.card}>
      <Text style={styles.stepKicker}>STEP 1 · CAPTURE</Text>
      <Text style={styles.cardTitle}>Start with the child’s original idea</Text>
      <Text style={styles.bodyText}>
        The source drawing and narration stay immutable while the AI proposes an
        interpretation for an adult to review.
      </Text>
      <DrawingPreview />
      <View style={styles.metaRow}>
        <Text style={styles.metaLabel}>DRAWING</Text>
        <Text style={styles.metaValue}>{FIXTURE_CONTRACTS.sourceArtifactId}</Text>
      </View>
      <View style={styles.metaRow}>
        <Text style={styles.metaLabel}>NARRATION</Text>
        <Text style={styles.metaValue}>fixture-narration.wav</Text>
      </View>
      {error !== null && (
        <View style={styles.errorNotice}>
          <Text style={styles.errorTitle}>Live backend unavailable</Text>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}
      <PrimaryButton testID="fixture-run-ai" label="Ask the fixture AI" onPress={onRunAi} />
      <SecondaryButton
        testID="live-run-ai"
        label={liveLoading ? 'Waiting for live backend…' : 'Try live backend (synthetic fixture)'}
        onPress={onRunLiveAi}
      />
      <Text style={styles.helperText}>
        The live button calls the Sketch2Life backend only. The backend owns the
        provider credential and still stops at Gate A.
      </Text>
    </View>
  );
}

function GateAStep({
  mode,
  proposalLabel,
  onConfirm,
}: Readonly<{
  mode: 'fixture' | 'live-backend';
  proposalLabel: string | null;
  onConfirm: () => void;
}>): React.JSX.Element {
  const label = proposalLabel ?? 'unresolved';
  return (
    <View style={styles.card}>
      <Text style={styles.stepKicker}>STEP 2 · GATE A</Text>
      <Text style={styles.cardTitle}>Does this look like {label}?</Text>
      <Text style={styles.bodyText}>
        P2 fused narration and vision into a proposal. The adult confirms meaning
        before P1 receives it.
      </Text>
      <View style={styles.aiResult}>
        <View style={styles.aiIcon}><Text style={styles.aiIconText}>✦</Text></View>
        <View style={styles.aiCopy}>
          <Text style={styles.aiLabel}>{mode === 'live-backend' ? 'LIVE PROPOSAL' : 'FIXTURE PROPOSAL'}</Text>
          <Text style={styles.aiValue}>{label}</Text>
          <Text style={styles.aiConfidence}>
            {mode === 'live-backend' ? 'Validated by backend contract · Gate A required' : '94% fixture agreement · ASR + vision'}
          </Text>
        </View>
      </View>
      <View style={styles.notice}>
        <Text style={styles.noticeText}>Gate A is required before activity selection.</Text>
      </View>
      <PrimaryButton testID="fixture-confirm-gate-a" label="Confirm meaning" onPress={onConfirm} />
    </View>
  );
}
function GateBStep({onApprove}: Readonly<{onApprove: () => void}>): React.JSX.Element {
  return (
    <View style={styles.card}>
      <Text style={styles.stepKicker}>STEP 3 · GATE B</Text>
      <Text style={styles.cardTitle}>Choose a safe next activity</Text>
      <Text style={styles.bodyText}>
        P1 applies readiness, materials, and supervision rules before the adult
        approves the activity/objective pair.
      </Text>
      <View style={styles.activityCard}>
        <View style={styles.activityBadge}><Text style={styles.activityBadgeText}>P1</Text></View>
        <View style={styles.aiCopy}>
          <Text style={styles.activityTitle}>Movement coordination</Text>
          <Text style={styles.activityMeta}>
            {FIXTURE_CONTRACTS.activityId} v{FIXTURE_CONTRACTS.activityVersion}
          </Text>
          <Text style={styles.activityMeta}>
            {FIXTURE_CONTRACTS.objectiveId} v{FIXTURE_CONTRACTS.objectiveVersion}
          </Text>
        </View>
      </View>
      <View style={styles.checkRow}><Text style={styles.checkMark}>✓</Text><Text style={styles.checkText}>Direct supervision available</Text></View>
      <View style={styles.checkRow}><Text style={styles.checkMark}>✓</Text><Text style={styles.checkText}>Required material is available</Text></View>
      <PrimaryButton testID="fixture-approve-gate-b" label="Approve this activity" onPress={onApprove} />
    </View>
  );
}

type ExperienceStepProps = Readonly<{
  mediaStatus: 'pending' | 'cache-hit' | 'fallback';
  onPlay: () => void;
  onFallback: () => void;
}>;

function ExperienceStep({mediaStatus, onPlay, onFallback}: ExperienceStepProps): React.JSX.Element {
  const isFallback = mediaStatus === 'fallback';
  return (
    <View style={styles.card}>
      <Text style={styles.stepKicker}>STEP 4 · EXPERIENCE</Text>
      <Text style={styles.cardTitle}>Watch the original idea come alive</Text>
      <Text style={styles.bodyText}>
        The Pixi bridge keeps the whole drawing intact and plays a bounded reveal.
      </Text>
      <DrawingPreview playing />
      <View style={[styles.mediaStatus, isFallback && styles.mediaStatusFallback]}>
        <Text style={styles.mediaStatusTitle}>{isFallback ? 'Safe fallback ready' : 'Learning media ready'}</Text>
        <Text style={styles.mediaStatusText}>
          {isFallback
            ? 'AI media was unavailable. The approved off-screen activity remains available.'
            : 'P4 cache HIT · renderer plan integration-butterfly-reveal'}
        </Text>
      </View>
      <PrimaryButton testID="fixture-play-experience" label="Play drawing reveal" onPress={onPlay} />
      {!isFallback && (
        <SecondaryButton testID="fixture-simulate-fallback" label="Simulate AI media fallback" onPress={onFallback} />
      )}
    </View>
  );
}

function HandoffStep({onStart}: Readonly<{onStart: () => void}>): React.JSX.Element {
  return (
    <View style={styles.card}>
      <Text style={styles.stepKicker}>STEP 5 · ACTIVITY HANDOFF</Text>
      <Text style={styles.cardTitle}>Now try it together</Text>
      <Text style={styles.bodyText}>
        The digital experience hands off to a supervised Montessori activity with
        the same P1 identity.
      </Text>
      <View style={styles.handoffCard}>
        <Text style={styles.handoffIcon}>◎</Text>
        <Text style={styles.activityTitle}>Movement coordination</Text>
        <Text style={styles.activityMeta}>Place two safe objects and move like a butterfly.</Text>
      </View>
      <PrimaryButton testID="fixture-start-activity" label="Start activity" onPress={onStart} />
    </View>
  );
}

function FeedbackStep({onSubmit}: Readonly<{onSubmit: () => void}>): React.JSX.Element {
  return (
    <View style={styles.card}>
      <Text style={styles.stepKicker}>STEP 6 · FEEDBACK</Text>
      <Text style={styles.cardTitle}>How did the activity go?</Text>
      <Text style={styles.bodyText}>This fixture records adult feedback after handoff.</Text>
      <View style={styles.ratingRow}>
        {['1', '2', '3', '4', '5'].map((rating) => (
          <View key={rating} style={styles.rating}><Text style={styles.ratingText}>{rating}</Text></View>
        ))}
      </View>
      <PrimaryButton testID="fixture-submit-feedback" label="Save feedback" onPress={onSubmit} />
    </View>
  );
}

function CompleteStep({onReset}: Readonly<{onReset: () => void}>): React.JSX.Element {
  return (
    <View style={styles.card}>
      <View style={styles.completeIcon}><Text style={styles.completeIconText}>✓</Text></View>
      <Text style={styles.cardTitle}>Fixture flow complete</Text>
      <Text style={styles.bodyText}>
        Capture, AI review, both gates, Pixi playback, activity handoff, and feedback
        all completed with versioned fixture contracts.
      </Text>
      <SecondaryButton testID="fixture-reset" label="Run it again" onPress={onReset} />
    </View>
  );
}

function DrawingPreview({playing = false}: Readonly<{playing?: boolean}>): React.JSX.Element {
  return (
    <View style={[styles.drawingPreview, playing && styles.drawingPreviewPlaying]}>
      <View style={styles.sun}><Text style={styles.sunText}>✦</Text></View>
      <View style={styles.wingLeft} />
      <View style={styles.wingRight} />
      <View style={styles.butterflyBody} />
      <View style={styles.drawingGround} />
      <Text style={styles.drawingCaption}>{playing ? 'DRAW_REVEAL · 2.0s' : 'ORIGINAL WHOLE DRAWING'}</Text>
    </View>
  );
}

function PrimaryButton({testID, label, onPress}: Readonly<{testID: string; label: string; onPress: () => void}>): React.JSX.Element {
  return <Pressable testID={testID} accessibilityRole="button" style={styles.primaryButton} onPress={onPress}><Text style={styles.primaryButtonText}>{label}</Text></Pressable>;
}

function SecondaryButton({testID, label, onPress}: Readonly<{testID: string; label: string; onPress: () => void}>): React.JSX.Element {
  return <Pressable testID={testID} accessibilityRole="button" style={styles.secondaryButton} onPress={onPress}><Text style={styles.secondaryButtonText}>{label}</Text></Pressable>;
}

const styles = StyleSheet.create({
  safeArea: {flex: 1, backgroundColor: '#F7F3EC'},
  container: {padding: 20, gap: 16, paddingBottom: 36},
  header: {flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start'},
  eyebrow: {color: '#A56538', fontSize: 11, fontWeight: '800', letterSpacing: 1.6},
  title: {color: '#25231F', fontSize: 30, fontWeight: '800', marginTop: 8, letterSpacing: -0.8},
  subtitle: {color: '#6E685F', fontSize: 14, marginTop: 5},
  statusPill: {backgroundColor: '#E1F1E8', borderRadius: 20, paddingHorizontal: 12, paddingVertical: 7},
  statusPillText: {color: '#2B7550', fontSize: 10, fontWeight: '800', letterSpacing: 1},
  progressCard: {backgroundColor: '#FFFDF9', borderRadius: 20, padding: 16, borderWidth: 1, borderColor: '#E9E0D3'},
  sectionLabel: {color: '#A56538', fontSize: 10, fontWeight: '800', letterSpacing: 1.2},
  sessionId: {color: '#3D3932', fontSize: 13, marginTop: 5, fontFamily: 'monospace'},
  progressRow: {flexDirection: 'row', justifyContent: 'space-between', marginTop: 16},
  progressItem: {alignItems: 'center', gap: 5, flex: 1},
  progressDot: {width: 27, height: 27, borderRadius: 14, backgroundColor: '#E8E1D8', alignItems: 'center', justifyContent: 'center'},
  progressDotActive: {backgroundColor: '#C9794B'},
  progressDotText: {color: '#FFFDF9', fontSize: 11, fontWeight: '800'},
  progressLabel: {color: '#9C9489', fontSize: 9, fontWeight: '700'},
  progressLabelActive: {color: '#6F4B36'},
  contractBanner: {backgroundColor: '#252F42', borderRadius: 16, padding: 16},
  contractTitle: {color: '#F5D7A8', fontSize: 14, fontWeight: '800'},
  contractText: {color: '#D0D8E4', fontSize: 12, lineHeight: 18, marginTop: 5},
  card: {backgroundColor: '#FFFDF9', borderRadius: 24, padding: 20, borderWidth: 1, borderColor: '#E9E0D3', gap: 14},
  stepKicker: {color: '#A56538', fontSize: 10, fontWeight: '800', letterSpacing: 1.3},
  cardTitle: {color: '#25231F', fontSize: 24, lineHeight: 29, fontWeight: '800', letterSpacing: -0.4},
  bodyText: {color: '#6E685F', fontSize: 14, lineHeight: 21},
  drawingPreview: {height: 190, borderRadius: 18, backgroundColor: '#F1E7D4', overflow: 'hidden', position: 'relative', alignItems: 'center', justifyContent: 'center'},
  drawingPreviewPlaying: {backgroundColor: '#E6F0EC'},
  sun: {position: 'absolute', top: 19, right: 28},
  sunText: {fontSize: 27, color: '#D99150'},
  wingLeft: {width: 72, height: 92, borderRadius: 45, backgroundColor: '#D18A66', position: 'absolute', left: '24%', transform: [{rotate: '-18deg'}], opacity: 0.9},
  wingRight: {width: 72, height: 92, borderRadius: 45, backgroundColor: '#E2AE6F', position: 'absolute', right: '24%', transform: [{rotate: '18deg'}], opacity: 0.9},
  butterflyBody: {width: 16, height: 98, borderRadius: 10, backgroundColor: '#4E5D50', position: 'absolute'},
  drawingGround: {height: 7, width: '72%', borderRadius: 8, backgroundColor: '#7C9A7F', position: 'absolute', bottom: 36},
  drawingCaption: {position: 'absolute', bottom: 12, color: '#6C614F', fontSize: 10, fontWeight: '800', letterSpacing: 1},
  metaRow: {flexDirection: 'row', justifyContent: 'space-between', borderBottomWidth: 1, borderBottomColor: '#EFE7DB', paddingBottom: 9},
  metaLabel: {color: '#9C9489', fontSize: 10, fontWeight: '800', letterSpacing: 1},
  metaValue: {color: '#4D473F', fontSize: 12, fontFamily: 'monospace'},
  primaryButton: {backgroundColor: '#C9794B', borderRadius: 14, paddingVertical: 15, alignItems: 'center', marginTop: 3},
  primaryButtonText: {color: '#FFFDF9', fontSize: 15, fontWeight: '800'},
  secondaryButton: {borderWidth: 1, borderColor: '#C9794B', borderRadius: 14, paddingVertical: 13, alignItems: 'center'},
  secondaryButtonText: {color: '#A55E37', fontSize: 14, fontWeight: '800'},
  aiResult: {flexDirection: 'row', alignItems: 'center', backgroundColor: '#F4EEE3', borderRadius: 17, padding: 15, gap: 13},
  aiIcon: {width: 42, height: 42, borderRadius: 21, backgroundColor: '#C9794B', alignItems: 'center', justifyContent: 'center'},
  aiIconText: {color: '#FFFDF9', fontSize: 23},
  aiCopy: {flex: 1, gap: 3},
  aiLabel: {color: '#A56538', fontSize: 10, fontWeight: '800', letterSpacing: 1},
  aiValue: {color: '#25231F', fontSize: 22, fontWeight: '800'},
  aiConfidence: {color: '#6E685F', fontSize: 12},
  notice: {backgroundColor: '#FFF4DB', borderRadius: 12, padding: 12},
  noticeText: {color: '#7B5B20', fontSize: 12, fontWeight: '700'},
  activityCard: {flexDirection: 'row', backgroundColor: '#E8F0EA', borderRadius: 17, padding: 16, gap: 13, alignItems: 'center'},
  activityBadge: {width: 43, height: 43, borderRadius: 14, backgroundColor: '#5E8066', alignItems: 'center', justifyContent: 'center'},
  activityBadgeText: {color: '#FFFDF9', fontWeight: '900', fontSize: 15},
  activityTitle: {color: '#2E4434', fontSize: 17, fontWeight: '800'},
  activityMeta: {color: '#57705C', fontSize: 11, marginTop: 3, fontFamily: 'monospace'},
  checkRow: {flexDirection: 'row', gap: 9, alignItems: 'center'},
  checkMark: {color: '#3E8A60', fontSize: 18, fontWeight: '900'},
  checkText: {color: '#5F5A52', fontSize: 13},
  mediaStatus: {backgroundColor: '#E8F0EA', borderRadius: 14, padding: 13},
  mediaStatusFallback: {backgroundColor: '#FFF0DC'},
  mediaStatusTitle: {color: '#365D43', fontSize: 14, fontWeight: '800'},
  mediaStatusText: {color: '#5D6E61', fontSize: 12, lineHeight: 18, marginTop: 4},
  handoffCard: {backgroundColor: '#F4EEE3', borderRadius: 17, padding: 17},
  handoffIcon: {color: '#C9794B', fontSize: 30, marginBottom: 7},
  ratingRow: {flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 10},
  rating: {width: 45, height: 45, borderRadius: 23, borderWidth: 1, borderColor: '#E0D3C2', alignItems: 'center', justifyContent: 'center'},
  ratingText: {color: '#A56538', fontWeight: '800', fontSize: 15},
  completeIcon: {width: 64, height: 64, borderRadius: 32, backgroundColor: '#5E8066', alignItems: 'center', justifyContent: 'center'},
  completeIconText: {color: '#FFFDF9', fontSize: 34, fontWeight: '700'},
  footerRow: {flexDirection: 'row', justifyContent: 'space-between'},
  footerText: {color: '#9C9489', fontSize: 10, fontWeight: '700'},
  helperText: {color: '#8A8278', fontSize: 11, lineHeight: 16},
  errorNotice: {backgroundColor: '#FDE9E5', borderRadius: 12, padding: 12},
  errorTitle: {color: '#9B4037', fontSize: 13, fontWeight: '800'},
  errorText: {color: '#875750', fontSize: 12, lineHeight: 17, marginTop: 4},
});



