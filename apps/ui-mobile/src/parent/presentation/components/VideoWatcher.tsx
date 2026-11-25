import React, { useEffect, useRef } from 'react';
import type { ParentStoryRunV1 } from '../../domain/types';
import { videoBecameReady, videoChipModel, videoFailedNow } from '../../application/videoWait';
import { ensureVideoNotificationPermission, notifyVideo } from '../../infrastructure/device/videoNotifier';
import { VideoStatusChip } from './VideoStatusChip';

type Props = { run: ParentStoryRunV1 | null; onVideoStep: boolean; onOpenVideo: () => void; onPoll: () => void };

const POLL_MS = 15_000;

/**
 * Watches the run the controller already polls (no request of its own): shows the floating chip while a video is made
 * elsewhere in the app and sends one local notification when it becomes ready or fails.
 */
export function VideoWatcher({ run, onVideoStep, onOpenVideo, onPoll }: Props): React.JSX.Element | null {
  const previous = useRef<ParentStoryRunV1 | null>(null);
  const asked = useRef(false);
  const inFlight = run?.video?.state === 'QUEUED' || run?.video?.state === 'GENERATING' || run?.video?.state === 'ACCEPTED';

  useEffect(() => {
    if (inFlight && !asked.current) {
      asked.current = true;
      void ensureVideoNotificationPermission();
    }
  }, [inFlight]);

  useEffect(() => {
    if (!inFlight || onVideoStep) return undefined;
    const timer = setInterval(onPoll, POLL_MS);
    return () => clearInterval(timer);
  }, [inFlight, onVideoStep, onPoll]);

  useEffect(() => {
    if (videoBecameReady(previous.current, run)) void notifyVideo('ready');
    else if (videoFailedNow(previous.current, run)) void notifyVideo('failed');
    previous.current = run;
  }, [run]);

  const chip = videoChipModel(run, onVideoStep);
  return chip.visible ? <VideoStatusChip text={chip.text} badge={chip.badge} onPress={onOpenVideo} /> : null;
}
