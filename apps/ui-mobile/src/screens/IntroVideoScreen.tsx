import React, { useCallback, useEffect, useState } from 'react';
import { Platform, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { ResizeMode, Video } from 'expo-av';
import { StatusBar } from 'expo-status-bar';

type IntroVideoScreenProps = {
  onFinished: () => void;
};

const VIDEO_SOURCE = require('../../assets/videos/intro.mp4');
// Metro's development server exposes binary assets through this endpoint;
// the production web export replaces the require() with its hashed dist URL.
const DEV_WEB_VIDEO_SOURCE = '/assets/?unstable_path=.%2Fassets%2Fvideos%2Fintro.mp4';
const WEB_VIDEO_SOURCE =
  typeof __DEV__ !== 'undefined' && __DEV__
    ? DEV_WEB_VIDEO_SOURCE
    : VIDEO_SOURCE;

/**
 * The branded startup video is intentionally kept outside the Parent SRS
 * navigation stack. It is a one-shot gate: once playback ends, the app opens
 * the existing Login screen and the video is not replayed during that mount.
 */
export const IntroVideoScreen: React.FC<IntroVideoScreenProps> = ({ onFinished }) => {
  const [isReady, setIsReady] = useState(false);
  const [playbackError, setPlaybackError] = useState<string | null>(null);
  const [hasFinished, setHasFinished] = useState(false);

  const finish = useCallback(() => {
    if (hasFinished) return;
    setHasFinished(true);
    onFinished();
  }, [hasFinished, onFinished]);

  // expo-av's web adapter does not reliably emit `didJustFinish` for every
  // browser/MP4 combination. The supplied intro is 1.23s, so this bounded
  // fallback keeps the startup gate from getting stuck on its last frame.
  useEffect(() => {
    const fallbackTimer = setTimeout(finish, 2200);
    return () => clearTimeout(fallbackTimer);
  }, [finish]);

  const handleStatusUpdate = useCallback((status: any) => {
    if (!status.isLoaded) {
      if (status.error) setPlaybackError('Không thể phát video giới thiệu.');
      return;
    }
    setIsReady(true);
    if (status.didJustFinish) finish();
  }, [finish]);

  const handleWebVideoReady = useCallback((event: any) => {
    setIsReady(true);
    const element = event.currentTarget as HTMLVideoElement;
    // Explicitly call play after metadata is available. This covers browsers
    // that ignore the initial autoPlay attribute during React hydration.
    element.muted = true;
    const playPromise = element.play?.();
    if (playPromise?.catch) playPromise.catch(() => undefined);
  }, []);

  return (
    <View style={styles.page}>
      <StatusBar style="light" hidden />

      <View style={styles.appContainer}>
        <View style={[styles.phoneFrame, Platform.OS !== 'web' && styles.phoneFrameNative]}>
          {!playbackError && (
            Platform.OS === 'web' ? (
              // expo-av's web adapter can remain on the first HEVC frame in
              // some browsers. A native HTML video element gives the web
              // preview reliable autoplay and frame rendering.
              React.createElement('video', {
                src: WEB_VIDEO_SOURCE,
                style: styles.webVideo,
                autoPlay: true,
                muted: true,
                playsInline: true,
                preload: 'auto',
                onLoadedMetadata: handleWebVideoReady,
                onLoadedData: handleWebVideoReady,
                onCanPlay: handleWebVideoReady,
                onEnded: finish,
                onError: () => setPlaybackError('Không thể phát video giới thiệu.'),
                'aria-label': 'Video giới thiệu Sketch2Life',
              })
            ) : (
              <Video
                source={VIDEO_SOURCE}
                style={styles.video}
                resizeMode={ResizeMode.COVER}
                shouldPlay
                isLooping={false}
                useNativeControls={false}
                onPlaybackStatusUpdate={handleStatusUpdate}
                onError={(message) => setPlaybackError(message || 'Không thể phát video giới thiệu.')}
                accessibilityLabel="Video giới thiệu Sketch2Life"
              />
            )
          )}

          {!isReady && !playbackError && <View style={styles.loadingScrim} />}

          {playbackError && (
            <View style={styles.fallback}>
              <Text style={styles.fallbackBrand}>Sketch2Life</Text>
              <Text style={styles.fallbackTitle}>Biến tranh vẽ của con thành câu chuyện sống động</Text>
              <Text style={styles.fallbackBody}>{playbackError}</Text>
              <TouchableOpacity onPress={finish} style={styles.continueButton} activeOpacity={0.86}>
                <Text style={styles.continueText}>Vào ứng dụng</Text>
              </TouchableOpacity>
            </View>
          )}

          {Platform.OS === 'web' && (
            <View pointerEvents="none" style={styles.homeBarContainer}>
              <View style={styles.homeBarIndicator} />
            </View>
          )}
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  page: {
    flex: 1,
    backgroundColor: '#0F172A',
    overflow: 'hidden',
  },
  appContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: Platform.OS === 'web' ? 14 : 0,
  },
  phoneFrame: {
    flex: 1,
    width: '100%',
    maxWidth: 416,
    maxHeight: Platform.OS === 'web' ? 844 : undefined,
    backgroundColor: '#071426',
    borderRadius: Platform.OS === 'web' ? 44 : 0,
    overflow: 'hidden',
    borderWidth: Platform.OS === 'web' ? 10 : 0,
    borderColor: '#1E293B',
    shadowColor: '#000000',
    shadowOpacity: 0.24,
    shadowRadius: 20,
    shadowOffset: { width: 0, height: 10 },
    elevation: 8,
    position: 'relative',
  },
  phoneFrameNative: {
    maxWidth: '100%',
    maxHeight: '100%',
    borderRadius: 0,
    borderWidth: 0,
  },
  video: {
    ...StyleSheet.absoluteFillObject,
  },
  webVideo: {
    ...StyleSheet.absoluteFillObject,
    width: '100%',
    height: '100%',
  } as any,
  loadingScrim: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#071426',
  },
  fallback: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  fallbackBrand: {
    color: '#FFFFFF',
    fontSize: 34,
    fontWeight: '900',
    letterSpacing: -1,
  },
  fallbackTitle: {
    marginTop: 16,
    maxWidth: 320,
    color: '#E6F2FF',
    fontSize: 17,
    lineHeight: 24,
    fontWeight: '700',
    textAlign: 'center',
  },
  fallbackBody: {
    marginTop: 12,
    color: '#B9C7D9',
    fontSize: 14,
    textAlign: 'center',
  },
  continueButton: {
    marginTop: 24,
    paddingHorizontal: 24,
    paddingVertical: 13,
    borderRadius: 999,
    backgroundColor: '#2388FF',
  },
  continueText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '800',
  },
  homeBarContainer: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 7,
    alignItems: 'center',
  },
  homeBarIndicator: {
    width: 108,
    height: 4,
    borderRadius: 999,
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
  },
});
