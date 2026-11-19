import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  AccessibilityInfo,
  Animated,
  Easing,
  Image,
  ImageBackground,
  StatusBar,
  StyleSheet,
  View,
  useWindowDimensions,
} from 'react-native';

type Props = {
  onFinished: () => void;
};

type SparkleSpec = {
  top?: `${number}%`;
  bottom?: `${number}%`;
  left?: `${number}%`;
  right?: `${number}%`;
  color: string;
  size: number;
};

const backgroundSource = require('../../assets/splash/background.png');
const logoSource = require('../../assets/splash/logo.png');
const pencilSource = require('../../assets/splash/pencil.png');

const sparkleConfig: readonly SparkleSpec[] = [
  { top: '35%', left: '17%', color: '#FFFDFD', size: 18 },
  { top: '44%', right: '15%', color: '#FFF6C7', size: 16 },
  { top: '28%', right: '27%', color: '#FFFDFD', size: 14 },
  { bottom: '25%', left: '22%', color: '#FFF6C7', size: 15 },
] as const;

export default function SplashScreen({ onFinished }: Props): React.JSX.Element {
  const { width, height } = useWindowDimensions();
  const [assetsReady, setAssetsReady] = useState(false);
  const mountedRef = useRef(true);
  const loadedAssetsRef = useRef(new Set<string>());
  const screenOpacity = useRef(new Animated.Value(1)).current;
  const pencilOpacity = useRef(new Animated.Value(0)).current;
  const pencilOffset = useRef(new Animated.Value(Math.min(height * 0.28, 240))).current;
  const pencilRotation = useRef(new Animated.Value(-10)).current;
  const pencilScale = useRef(new Animated.Value(0.88)).current;
  const logoOpacity = useRef(new Animated.Value(0)).current;
  const logoScale = useRef(new Animated.Value(0.8)).current;
  const sparkleValues = useMemo(
    () => sparkleConfig.map(() => ({ opacity: new Animated.Value(0), scale: new Animated.Value(0.25) })),
    [],
  );
  const markAssetLoaded = useCallback((assetKey: string): void => {
    if (loadedAssetsRef.current.has(assetKey)) return;

    loadedAssetsRef.current.add(assetKey);
    if (loadedAssetsRef.current.size === 3) setAssetsReady(true);
  }, []);

  const logoWidth = Math.min(width * 0.79, 336);
  const logoHeight = logoWidth * (724 / 2172);
  const pencilHeight = Math.min(height * 0.5, width * 0.96);
  const pencilWidth = pencilHeight * (1086 / 1448);
  const logoTop = Math.max(72, Math.min(115, height * 0.115));
  const pencilTop = height * 0.32;
  // The artwork's visible character mass sits left of the PNG canvas center
  // because the backpack occupies the left side, so use an optical center.
  const pencilCenterX = width / 2 + pencilWidth * 0.042;

  useEffect(() => {
    if (!assetsReady) return undefined;

    mountedRef.current = true;
    let reduceMotionSubscription: { remove: () => void } | undefined;
    let finishTimer: ReturnType<typeof setTimeout> | undefined;

    const finish = (): void => {
      if (mountedRef.current) onFinished();
    };

    const showStillAndFinish = (): void => {
      pencilOpacity.setValue(1);
      pencilOffset.setValue(0);
      pencilRotation.setValue(3);
      pencilScale.setValue(1);
      logoOpacity.setValue(1);
      logoScale.setValue(1);
      sparkleValues.forEach(({ opacity, scale }) => {
        opacity.setValue(0.9);
        scale.setValue(1);
      });
      finishTimer = setTimeout(finish, 700);
    };

    const runTimeline = (reduceMotion: boolean): void => {
      if (reduceMotion) {
        showStillAndFinish();
        return;
      }

      const pencilEntry = Animated.parallel([
        Animated.timing(pencilOpacity, {
          toValue: 1,
          duration: 120,
          useNativeDriver: true,
        }),
        Animated.sequence([
          Animated.timing(pencilOffset, {
            toValue: -18,
            duration: 680,
            easing: Easing.out(Easing.cubic),
            useNativeDriver: true,
          }),
          Animated.timing(pencilOffset, {
            toValue: 0,
            duration: 150,
            easing: Easing.out(Easing.quad),
            useNativeDriver: true,
          }),
        ]),
        Animated.sequence([
          Animated.timing(pencilRotation, {
            toValue: 3,
            duration: 760,
            easing: Easing.out(Easing.cubic),
            useNativeDriver: true,
          }),
        ]),
        Animated.sequence([
          Animated.timing(pencilScale, {
            toValue: 1.02,
            duration: 650,
            easing: Easing.out(Easing.back(1.2)),
            useNativeDriver: true,
          }),
          Animated.timing(pencilScale, {
            toValue: 1,
            duration: 170,
            easing: Easing.out(Easing.quad),
            useNativeDriver: true,
          }),
        ]),
      ]);

      const logoEntry = Animated.sequence([
        Animated.delay(340),
        Animated.parallel([
          Animated.timing(logoOpacity, {
            toValue: 1,
            duration: 480,
            easing: Easing.out(Easing.quad),
            useNativeDriver: true,
          }),
          Animated.spring(logoScale, {
            toValue: 1,
            friction: 7,
            tension: 58,
            useNativeDriver: true,
          }),
        ]),
      ]);

      const sparkleEntry = Animated.sequence([
        Animated.delay(680),
        Animated.stagger(
          55,
          sparkleValues.map(({ opacity, scale }) => Animated.parallel([
            Animated.timing(opacity, {
              toValue: 0.9,
              duration: 220,
              easing: Easing.out(Easing.back(2)),
              useNativeDriver: true,
            }),
            Animated.spring(scale, {
              toValue: 1,
              friction: 5,
              tension: 85,
              useNativeDriver: true,
            }),
          ])),
        ),
      ]);

      Animated.parallel([pencilEntry, logoEntry, sparkleEntry]).start(() => {
        if (!mountedRef.current) return;

        Animated.sequence([
          Animated.timing(pencilOffset, {
            toValue: -8,
            duration: 220,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
          Animated.timing(pencilOffset, {
            toValue: 0,
            duration: 220,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
          Animated.timing(pencilOffset, {
            toValue: -5,
            duration: 170,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
          Animated.timing(pencilOffset, {
            toValue: 0,
            duration: 170,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
          Animated.timing(screenOpacity, {
            toValue: 0,
            duration: 260,
            easing: Easing.in(Easing.quad),
            useNativeDriver: true,
          }),
        ]).start(({ finished }) => {
          if (finished) finish();
        });
      });
    };

    AccessibilityInfo.isReduceMotionEnabled().then(runTimeline);
    reduceMotionSubscription = AccessibilityInfo.addEventListener('reduceMotionChanged', (enabled) => {
      if (enabled) showStillAndFinish();
    });

    return () => {
      mountedRef.current = false;
      if (finishTimer) clearTimeout(finishTimer);
      reduceMotionSubscription?.remove();
      screenOpacity.stopAnimation();
      pencilOpacity.stopAnimation();
      pencilOffset.stopAnimation();
      pencilRotation.stopAnimation();
      pencilScale.stopAnimation();
      logoOpacity.stopAnimation();
      logoScale.stopAnimation();
      sparkleValues.forEach(({ opacity, scale }) => {
        opacity.stopAnimation();
        scale.stopAnimation();
      });
    };
  }, [assetsReady, onFinished, pencilOpacity, pencilOffset, pencilRotation, pencilScale, screenOpacity, sparkleValues, logoOpacity, logoScale]);

  return (
    <Animated.View accessibilityLabel="Đang mở Sketch2Life" accessibilityRole="progressbar" style={[styles.screen, { opacity: screenOpacity }]}>
      <StatusBar hidden />
      <ImageBackground
        source={backgroundSource}
        resizeMode="cover"
        style={styles.background}
        onLoadEnd={() => markAssetLoaded('background')}
      >
        <Animated.View
          accessibilityLabel="Logo Sketch2Life"
          accessibilityRole="image"
          style={[styles.logo, { width: logoWidth, height: logoHeight, top: logoTop, left: width / 2, opacity: logoOpacity, transform: [{ translateX: -logoWidth / 2 }, { scale: logoScale }] }]}
        >
          <Image
            source={logoSource}
            resizeMode="contain"
            onLoadEnd={() => markAssetLoaded('logo')}
            style={styles.logoImage}
          />
        </Animated.View>

        <Animated.Image
          accessibilityLabel="Nhân vật bút chì Sketch2Life"
          source={pencilSource}
          resizeMode="contain"
          onLoadEnd={() => markAssetLoaded('pencil')}
          style={[styles.pencil, { width: pencilWidth, height: pencilHeight, top: pencilTop, left: pencilCenterX, opacity: pencilOpacity, transform: [{ translateX: -pencilWidth / 2 }, { translateY: pencilOffset }, { rotate: pencilRotation.interpolate({ inputRange: [-10, 0, 3], outputRange: ['-10deg', '0deg', '3deg'] }) }, { scale: pencilScale }] }]}
        />

        {sparkleConfig.map((sparkle, index) => (
          <Animated.View
            key={`${sparkle.top ?? sparkle.bottom}-${sparkle.left ?? sparkle.right}`}
            pointerEvents="none"
            style={[styles.sparkle, {
              top: sparkle.top,
              bottom: sparkle.bottom,
              left: sparkle.left,
              right: sparkle.right,
              width: sparkle.size,
              height: sparkle.size,
              opacity: sparkleValues[index].opacity,
              transform: [{ scale: sparkleValues[index].scale }, { rotate: '45deg' }],
            }]}
          >
            <View style={[styles.sparkleRay, { backgroundColor: sparkle.color }]} />
            <View style={[styles.sparkleRay, styles.sparkleRayHorizontal, { backgroundColor: sparkle.color }]} />
          </Animated.View>
        ))}
      </ImageBackground>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#F6E8FF' },
  background: { flex: 1, width: '100%', height: '100%', overflow: 'hidden' },
  logo: { position: 'absolute', zIndex: 2 },
  logoImage: { width: '100%', height: '100%' },
  pencil: { position: 'absolute', zIndex: 3, transformOrigin: '50% 68%' },
  sparkle: { position: 'absolute', zIndex: 4, width: 18, height: 18, alignItems: 'center', justifyContent: 'center' },
  sparkleRay: { position: 'absolute', width: 3, height: '100%', borderRadius: 2 },
  sparkleRayHorizontal: { width: '100%', height: 3 },
});
