import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, TouchableOpacity, Image, Easing } from 'react-native';
import Svg, { Path, Circle, Rect, G, Ellipse, Line } from 'react-native-svg';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius } from '../theme';

// ==========================================
// 0-A. FLOATING PARTICLES — sparkles/stars float upward (kids love it!)
// ==========================================
const PARTICLE_EMOJIS = ['⭐', '✨', '💫', '🌟', '⚡', '🎈', '🌈', '🦋'];
export const FloatingParticles: React.FC<{ count?: number; style?: object }> = ({ count = 6, style }) => {
  const particles = useRef(
    Array.from({ length: count }, (_, i) => ({
      translateY: new Animated.Value(-20 - i * 5),
      opacity: new Animated.Value(0.7),
      scale: new Animated.Value(0.9),
      left: 8 + (i / count) * 82,
      emoji: PARTICLE_EMOJIS[i % PARTICLE_EMOJIS.length],
      delay: i * 300,
    }))
  ).current;

  useEffect(() => {
    particles.forEach((p) => {
      const loop = () => {
        p.translateY.setValue(0);
        p.opacity.setValue(0.6);
        p.scale.setValue(0.7);
        Animated.parallel([
          Animated.sequence([
            Animated.timing(p.opacity, { toValue: 1, duration: 400, delay: p.delay, useNativeDriver: true }),
            Animated.timing(p.opacity, { toValue: 0, duration: 600, delay: 800, useNativeDriver: true }),
          ]),
          Animated.timing(p.translateY, { toValue: -90, duration: 2000, delay: p.delay, useNativeDriver: true }),
          Animated.sequence([
            Animated.timing(p.scale, { toValue: 1.3, duration: 600, delay: p.delay, useNativeDriver: true }),
            Animated.timing(p.scale, { toValue: 0.6, duration: 1400, delay: 0, useNativeDriver: true }),
          ]),
        ]).start(() => setTimeout(loop, Math.random() * 600 + 200));
      };
      setTimeout(loop, p.delay);
    });
  }, []);

  return (
    <View style={[{ position: 'absolute', width: '100%', height: 100, pointerEvents: 'none' }, style]}>
      {particles.map((p, i) => (
        <Animated.Text
          key={i}
          style={{
            position: 'absolute',
            left: `${p.left}%` as any,
            bottom: 10,
            fontSize: 18,
            transform: [{ translateY: p.translateY }, { scale: p.scale }],
            opacity: p.opacity,
          }}
        >
          {p.emoji}
        </Animated.Text>
      ))}
    </View>
  );
};


// ==========================================
// 0-B. BOUNCE-IN VIEW — staggered entrance animation for children
// ==========================================
export const BounceInView: React.FC<{ delay?: number; children: React.ReactNode; style?: object }> = ({
  delay = 0,
  children,
  style,
}) => {
  const scaleAnim = useRef(new Animated.Value(0.85)).current;
  const opacityAnim = useRef(new Animated.Value(0.7)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.spring(scaleAnim, {
        toValue: 1,
        friction: 5,
        tension: 80,
        delay,
        useNativeDriver: true,
      }),
      Animated.timing(opacityAnim, {
        toValue: 1,
        duration: 350,
        delay,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  return (
    <Animated.View style={[style, { transform: [{ scale: scaleAnim }], opacity: opacityAnim }]}>
      {children}
    </Animated.View>
  );
};


// ==========================================
// 0-C. PULSE GLOW — pulsing scale for CTA buttons
// ==========================================
export const PulseGlow: React.FC<{ children: React.ReactNode; style?: object }> = ({ children, style }) => {
  const glowAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, { toValue: 1.06, duration: 900, useNativeDriver: true }),
        Animated.timing(glowAnim, { toValue: 1, duration: 900, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  return (
    <Animated.View style={[style, { transform: [{ scale: glowAnim }] }]}>
      {children}
    </Animated.View>
  );
};

// ==========================================
// 0-D. SPARKLE RING — decorative rotating emoji stars around an element
// ==========================================
export const SparkleRing: React.FC<{ size?: number }> = ({ size = 90 }) => {
  const rotateAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.timing(rotateAnim, {
        toValue: 1,
        duration: 4000,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    ).start();
  }, []);

  const rotate = rotateAnim.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '360deg'] });
  const stars = ['⭐', '✨', '💫', '🌟', '⭐', '✨'];
  const r = size / 2 - 8;

  return (
    <Animated.View
      style={{ width: size, height: size, position: 'absolute', transform: [{ rotate }] }}
      pointerEvents="none"
    >
      {stars.map((s, i) => {
        const angle = (i / stars.length) * Math.PI * 2;
        const x = size / 2 + r * Math.cos(angle) - 7;
        const y = size / 2 + r * Math.sin(angle) - 7;
        return (
          <Text key={i} style={{ position: 'absolute', left: x, top: y, fontSize: 10 }}>
            {s}
          </Text>
        );
      })}
    </Animated.View>
  );
};



// ==========================================
// 1. BRAND LOGO
// ==========================================
export const LogoSketch2Life: React.FC<{ size?: 'sm' | 'md' | 'lg'; showTagline?: boolean }> = ({
  size = 'md',
  showTagline = true,
}) => {
  const fontSizes = { sm: 22, md: 32, lg: 38 };
  const fs = fontSizes[size];

  return (
    <View style={styles.logoContainer}>
      <View style={styles.logoRow}>
        <Text style={[styles.logoText, { fontSize: fs, color: '#38BDF8' }]}>Sketch</Text>
        <Text style={[styles.logoText, { fontSize: fs * 1.15, color: '#FBBF24', transform: [{ rotate: '-4deg' }] }]}>2</Text>
        <Text style={[styles.logoText, { fontSize: fs, color: '#FB7185' }]}>Life</Text>
      </View>
      {showTagline && (
        <Text style={styles.logoTagline}>Biến nét vẽ thành những câu chuyện diệu kỳ</Text>
      )}
    </View>
  );
};

// ==========================================
// 2. SPLASH HERO: EXACT GIRL + DINO + DOODLES (Screen 1)
// ==========================================
export const SplashHeroIllustration: React.FC<{ height?: number }> = ({ height = 280 }) => {
  const floatAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(floatAnim, {
          toValue: -6,
          duration: 1800,
          useNativeDriver: true,
        }),
        Animated.timing(floatAnim, {
          toValue: 0,
          duration: 1800,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, []);

  return (
    <Animated.View
      style={{
        width: '100%',
        height,
        alignItems: 'center',
        justifyContent: 'center',
        transform: [{ translateY: floatAnim }],
      }}
    >
      <Image
        source={require('../../assets/images/splash_hero.png')}
        style={{ width: '100%', height: '100%', resizeMode: 'contain' }}
      />
    </Animated.View>
  );
};

// ==========================================
// 3. ONBOARDING HERO: EXACT GIRL + DINO HUG (Screen 2)
// ==========================================
export const OnboardingHeroIllustration: React.FC<{ height?: number }> = ({ height = 180 }) => {
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.03,
          duration: 1500,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1500,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, []);

  return (
    <Animated.View
      style={{
        width: '100%',
        height,
        alignItems: 'center',
        justifyContent: 'center',
        transform: [{ scale: pulseAnim }],
      }}
    >
      <Image
        source={require('../../assets/images/onboarding_hero.png')}
        style={{ width: '100%', height: '100%', resizeMode: 'contain' }}
      />
    </Animated.View>
  );
};

// ==========================================
// 4. VOICE GIRL: EXACT SINGING GIRL + MIC (Screen 6) with crisp speech bubble
// ==========================================
export const VoiceGirlMicIllustration: React.FC<{ height?: number }> = ({ height = 160 }) => {
  const breatheAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(breatheAnim, {
          toValue: 1.025,
          duration: 1200,
          useNativeDriver: true,
        }),
        Animated.timing(breatheAnim, {
          toValue: 1,
          duration: 1200,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, []);

  return (
    <Animated.View
      style={{
        width: '100%',
        height,
        alignItems: 'center',
        justifyContent: 'center',
        transform: [{ scale: breatheAnim }],
        position: 'relative',
      }}
    >
      <Image
        source={require('../../assets/images/voice_girl.png')}
        style={{ width: height * 1.1, height, resizeMode: 'contain' }}
      />
      {/* Native speech bubble matching Image 1 Screen 6 */}
      <View style={styles.voiceSpeechBubble}>
        <Text style={styles.voiceSpeechText}>{"Hãy kể\nthật thoải mái\nnhé!"}</Text>
        <View style={styles.voiceSpeechTail} />
      </View>
    </Animated.View>
  );
};

// ==========================================
// 5. CAT DRAWING: EXACT RAINBOW CAT ARTWORK (Screen 5) with speech bubble
// ==========================================
export const CatDrawingArtwork: React.FC<{ height?: number }> = ({ height = 180 }) => (
  <View style={[styles.artworkCard, { height, backgroundColor: '#FEF9C3', overflow: 'visible' }]}>
    <Image
      source={require('../../assets/images/photo_cat_paper.png')}
      style={{ width: '100%', height: '100%', resizeMode: 'contain', borderRadius: 12 }}
    />
    {/* Speech bubble in top-right corner matching reference mockup */}
    <View style={styles.catSpeechBubble}>
      <Text style={styles.catSpeechText}>{"Tuyệt vời!\nHãy để vũ trụ\ntưởng tượng\nbắt đầu!"}</Text>
      {/* Bubble tail pointing down-left */}
      <View style={styles.catSpeechTail} />
    </View>
  </View>
);

// ==========================================
// 6. RAINBOW FISH ARTWORK (Screen 3)
// ==========================================
export const RainbowFishArtwork: React.FC<{ height?: number }> = ({ height = 90 }) => (
  <View style={[styles.artworkCard, { height, backgroundColor: '#38BDF8', overflow: 'hidden' }]}>
    <Image
      source={require('../../assets/images/photo_rainbow_fish.png')}
      style={{ width: '100%', height: '100%', resizeMode: 'cover' }}
    />
    <View style={styles.miniPlayBtn}>
      <Ionicons name="play" size={14} color="#3B82F6" />
    </View>
  </View>
);

// ==========================================
// 7. STORY ROBOT ARTWORK (Screen 3) — with high-res illustration and play button
// ==========================================
export const StoryRobotArtwork: React.FC<{ height?: number }> = ({ height = 90 }) => (
  <View style={[styles.artworkCard, { height, backgroundColor: '#A7F3D0', overflow: 'hidden' }]}>
    <Image
      source={require('../../assets/images/story_robot.png')}
      style={{ width: '100%', height: '100%', resizeMode: 'cover' }}
    />
    <View style={styles.miniPlayBtn}>
      <Ionicons name="play" size={14} color="#3B82F6" />
    </View>
  </View>
);

// ==========================================
// 8. CRAFT BUTTERFLY ARTWORK (Screen 11)
// ==========================================
export const CraftButterflyArtwork: React.FC<{ height?: number }> = ({ height = 150 }) => (
  <View style={[styles.artworkCard, { height, backgroundColor: '#FFFBEB', overflow: 'hidden' }]}>
    <Image
      source={require('../../assets/images/photo_craft_butterfly.png')}
      style={{ width: '100%', height: '100%', resizeMode: 'cover' }}
    />
  </View>
);

// ==========================================
// 9. ROBOT AI MASCOT: HOLDING DRAWING (Screen 7)
// ==========================================
export const RobotAiIllustration: React.FC<{ height?: number }> = ({ height = 180 }) => {
  const floatAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(floatAnim, {
          toValue: -8,
          duration: 1600,
          useNativeDriver: true,
        }),
        Animated.timing(floatAnim, {
          toValue: 0,
          duration: 1600,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, []);

  return (
    <Animated.View
      style={{
        width: '100%',
        height,
        alignItems: 'center',
        justifyContent: 'center',
        transform: [{ translateY: floatAnim }],
      }}
    >
      <Image
        source={require('../../assets/images/robot_ai.png')}
        style={{ width: '100%', height: '100%', resizeMode: 'contain' }}
      />
    </Animated.View>
  );
};

// ==========================================
// 10. ANIMATED MEADOW SCENE (Screen 9 & 10)
// ==========================================
export const AnimatedMeadowScene: React.FC<{
  isPlaying?: boolean;
  onTogglePlay?: () => void;
  showPlayButton?: boolean;
  onPlayPress?: () => void;
  height?: number;
}> = ({ isPlaying = true, onTogglePlay, showPlayButton, onPlayPress, height = 220 }) => {
  const handlePress = onPlayPress || onTogglePlay;
  const shouldShowPlay = showPlayButton !== undefined ? showPlayButton : !isPlaying;

  return (
    <TouchableOpacity
      activeOpacity={0.95}
      onPress={handlePress}
      style={[styles.artworkCard, { height, backgroundColor: '#BAE6FD', overflow: 'hidden' }]}
    >
      <Image
        source={require('../../assets/images/video_scene_only.png')}
        style={{ width: '100%', height: '100%', resizeMode: 'cover' }}
      />
      {shouldShowPlay && (
        <View style={styles.playButton}>
          <Ionicons name="play" size={28} color="#2563EB" />
        </View>
      )}
    </TouchableOpacity>
  );
};

// ==========================================
// 11. PLANT SPROUT CARD — 100% SVG vector, no blurry PNG
// ==========================================
export const PlantSproutCard: React.FC<{ size?: number; height?: number }> = ({ size, height = 70 }) => {
  const bounceAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(bounceAnim, { toValue: 1.05, duration: 1000, useNativeDriver: true }),
        Animated.timing(bounceAnim, { toValue: 1, duration: 1000, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  const w = size || 80;
  return (
    <Animated.View style={{ width: w, height: w, alignItems: 'center', justifyContent: 'center', transform: [{ scale: bounceAnim }] }}>
      <Svg width={w} height={w} viewBox="0 0 80 80" fill="none">
        {/* Pot body */}
        <Rect x={22} y={50} width={36} height={24} rx={6} fill="#EA580C" />
        <Rect x={18} y={46} width={44} height={10} rx={4} fill="#F97316" />
        {/* Soil */}
        <Ellipse cx={40} cy={54} rx={14} ry={4} fill="#7C3AED" opacity={0.3} />
        <Ellipse cx={40} cy={53} rx={14} ry={3} fill="#78350F" />
        {/* Stem */}
        <Path d="M40 50V28" stroke="#16A34A" strokeWidth={3.5} strokeLinecap="round" />
        {/* Left leaf */}
        <Path d="M40 38Q30 32 28 22Q38 26 40 38Z" fill="#22C55E" />
        {/* Right leaf */}
        <Path d="M40 34Q50 28 52 18Q42 22 40 34Z" fill="#4ADE80" />
        {/* Top bud */}
        <Circle cx={40} cy={26} r={6} fill="#34D399" />
        <Circle cx={40} cy={22} r={4} fill="#6EE7B7" />
        {/* Sparkle dot on bud */}
        <Circle cx={46} cy={18} r={3} fill="#FDE047" />
        <Circle cx={50} cy={14} r={2} fill="#FEF08A" />
      </Svg>
    </Animated.View>
  );
};

// ==========================================
// 11b. NATURE DIARY CARD — 100% SVG vector, no blurry PNG
// ==========================================
export const NatureDiaryCard: React.FC<{ size?: number; height?: number }> = ({ size, height = 70 }) => {
  const floatAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(floatAnim, { toValue: -4, duration: 1200, useNativeDriver: true }),
        Animated.timing(floatAnim, { toValue: 0, duration: 1200, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  const w = size || 80;
  return (
    <Animated.View style={{ width: w, height: w, alignItems: 'center', justifyContent: 'center', transform: [{ translateY: floatAnim }] }}>
      <Svg width={w} height={w} viewBox="0 0 80 80" fill="none">
        {/* Notebook base */}
        <Rect x={12} y={10} width={50} height={62} rx={6} fill="#E0F2FE" stroke="#38BDF8" strokeWidth={2} />
        {/* Spine */}
        <Rect x={12} y={10} width={10} height={62} rx={4} fill="#38BDF8" />
        {/* Page lines */}
        <Path d="M28 24H56" stroke="#BAE6FD" strokeWidth={1.5} strokeLinecap="round" />
        <Path d="M28 32H56" stroke="#BAE6FD" strokeWidth={1.5} strokeLinecap="round" />
        <Path d="M28 40H56" stroke="#BAE6FD" strokeWidth={1.5} strokeLinecap="round" />
        {/* Sun doodle */}
        <Circle cx={36} cy={54} r={6} fill="#FBBF24" />
        <Path d="M36 44V47M36 61V64M26 54H29M43 54H46M29 47L31 49M41 59L43 61M29 61L31 59M41 47L43 49" stroke="#F59E0B" strokeWidth={1.5} strokeLinecap="round" />
        {/* Flower doodle */}
        <Circle cx={52} cy={52} r={3.5} fill="#FB7185" />
        <Circle cx={48} cy={49} r={2.5} fill="#FDA4AF" />
        <Circle cx={56} cy={49} r={2.5} fill="#FDA4AF" />
        <Circle cx={48} cy={55} r={2.5} fill="#FDA4AF" />
        <Circle cx={56} cy={55} r={2.5} fill="#FDA4AF" />
        <Circle cx={52} cy={52} r={2} fill="#FBBF24" />
        {/* Ring bindings */}
        <Circle cx={22} cy={20} r={2.5} fill="#FFFFFF" stroke="#BAE6FD" strokeWidth={1.5} />
        <Circle cx={22} cy={34} r={2.5} fill="#FFFFFF" stroke="#BAE6FD" strokeWidth={1.5} />
        <Circle cx={22} cy={48} r={2.5} fill="#FFFFFF" stroke="#BAE6FD" strokeWidth={1.5} />
        <Circle cx={22} cy={62} r={2.5} fill="#FFFFFF" stroke="#BAE6FD" strokeWidth={1.5} />
      </Svg>
    </Animated.View>
  );
};



// ==========================================
// 12. CRISP VECTOR SVGS FOR ICONS & AVATARS
// ==========================================
export const CuteStarIconSvg: React.FC<{ size?: number }> = ({ size = 26 }) => (
  <Svg width={size} height={size} viewBox="0 0 64 64" fill="none">
    {/* 5-pointed rounded friendly star */}
    <Path
      d="M32 5C33.2 5 34.5 6.4 35.2 8.5L41.2 19.8C41.8 21 43 21.9 44.4 22.1L56.8 23.9C59.5 24.3 60.5 27.7 58.6 29.6L49.5 38.3C48.5 39.3 48 40.8 48.3 42.2L50.4 54.5C50.9 57.2 48 59.3 45.5 58L34.5 52.1C33.2 51.4 31.8 51.4 30.5 52.1L19.5 58C17 59.3 14.1 57.2 14.6 54.5L16.7 42.2C17 40.8 16.5 39.3 15.5 38.3L6.4 29.6C4.5 27.7 5.5 24.3 8.2 23.9L20.6 22.1C22 21.9 23.2 21 23.8 19.8L29.8 8.5C30.5 6.4 31.8 5 32 5Z"
      fill="#FBBF24"
      stroke="#F59E0B"
      strokeWidth={2}
      strokeLinejoin="round"
      strokeLinecap="round"
    />
    {/* Soft inner highlight layer */}
    <Path
      d="M32 9L37 19.5C37.8 21.2 39.5 22.4 41.5 22.7L52.5 24.3L44.5 32C43.2 33.3 42.5 35.2 42.8 37.1L44.7 48L35.5 43.1C33.7 42.1 31.3 42.1 29.5 43.1L20.3 48L22.2 37.1C22.5 35.2 21.8 33.3 20.5 32L12.5 24.3L23.5 22.7C25.5 22.4 27.2 21.2 28 19.5L32 9Z"
      fill="#FDE047"
    />
    {/* Two happy eyes */}
    <Circle cx={27} cy={34} r={2.8} fill="#78350F" />
    <Circle cx={26.2} cy={33} r={1} fill="#FFFFFF" />
    <Circle cx={37} cy={34} r={2.8} fill="#78350F" />
    <Circle cx={36.2} cy={33} r={1} fill="#FFFFFF" />
    {/* Cute smiling mouth */}
    <Path d="M29 38.5Q32 42 35 38.5" stroke="#78350F" strokeWidth={2.2} strokeLinecap="round" />
    {/* Rosy blushing cheeks */}
    <Circle cx={23} cy={37} r={2.4} fill="#FB7185" opacity={0.7} />
    <Circle cx={41} cy={37} r={2.4} fill="#FB7185" opacity={0.7} />
  </Svg>
);

export const SunIconSvg: React.FC<{ size?: number }> = ({ size = 36 }) => (
  <Svg width={size} height={size} viewBox="0 0 64 64" fill="none">
    {/* 8 Golden Rays */}
    <Path
      d="M32 4V12M32 52V60M4 32H12M52 32H60M12.22 12.22L17.88 17.88M46.12 46.12L51.78 51.78M12.22 51.78L17.88 46.12M46.12 17.88L51.78 12.22"
      stroke="#F59E0B"
      strokeWidth={4.5}
      strokeLinecap="round"
    />
    {/* Sun Body */}
    <Circle cx={32} cy={32} r={17} fill="#FBBF24" />
    <Circle cx={32} cy={32} r={14.5} fill="#FDE047" />
    {/* Cute smiling face */}
    <Circle cx={27} cy={30} r={2.2} fill="#78350F" />
    <Circle cx={37} cy={30} r={2.2} fill="#78350F" />
    {/* Rosy cheeks */}
    <Circle cx={23} cy={34} r={2.5} fill="#F87171" opacity={0.7} />
    <Circle cx={41} cy={34} r={2.5} fill="#F87171" opacity={0.7} />
    {/* Gentle smile */}
    <Path d="M28 35C29.5 38 34.5 38 36 35" stroke="#78350F" strokeWidth={2.2} strokeLinecap="round" />
  </Svg>
);

export const ButterflyIconSvg: React.FC<{ size?: number }> = ({ size = 36 }) => (
  <Svg width={size} height={size} viewBox="0 0 64 64" fill="none">
    {/* Antennae */}
    <Path d="M30 18Q23 10 18 13" stroke="#6D28D9" strokeWidth={2} strokeLinecap="round" />
    <Circle cx={17} cy={13} r={2} fill="#EC4899" />
    <Path d="M34 18Q41 10 46 13" stroke="#6D28D9" strokeWidth={2} strokeLinecap="round" />
    <Circle cx={47} cy={13} r={2} fill="#EC4899" />
    {/* Left Top Wing */}
    <Path d="M31 30C19 14 3 20 7 35C9 41 23 41 31 33Z" fill="#38BDF8" />
    <Circle cx={18} cy={27} r={4} fill="#FDE047" />
    {/* Right Top Wing */}
    <Path d="M33 30C45 14 61 20 57 35C55 41 41 41 33 33Z" fill="#38BDF8" />
    <Circle cx={46} cy={27} r={4} fill="#FDE047" />
    {/* Left Bottom Wing */}
    <Path d="M31 33C17 35 13 49 20 54C27 58 31 46 31 37Z" fill="#F43F5E" />
    <Circle cx={23} cy={45} r={2.8} fill="#FEF08A" />
    {/* Right Bottom Wing */}
    <Path d="M33 33C47 35 51 49 44 54C37 58 33 46 33 37Z" fill="#F43F5E" />
    <Circle cx={41} cy={45} r={2.8} fill="#FEF08A" />
    {/* Body & Head */}
    <Rect x={30} y={22} width={4} height={24} rx={2} fill="#7C3AED" />
    <Circle cx={32} cy={20} r={3.5} fill="#6D28D9" />
    {/* Smiling face on butterfly */}
    <Circle cx={31} cy={19.5} r={0.7} fill="#FFFFFF" />
    <Circle cx={33} cy={19.5} r={0.7} fill="#FFFFFF" />
  </Svg>
);

export const FlowerIconSvg: React.FC<{ size?: number }> = ({ size = 36 }) => (
  <Svg width={size} height={size} viewBox="0 0 64 64" fill="none">
    {/* Stem */}
    <Path d="M32 38V58" stroke="#16A34A" strokeWidth={3.5} strokeLinecap="round" />
    {/* Leaves */}
    <Path d="M32 48Q43 45 42 39Q34 43 32 48Z" fill="#22C55E" />
    <Path d="M32 52Q21 50 22 44Q30 46 32 52Z" fill="#22C55E" />
    {/* 5 Coral Petals */}
    <Circle cx={32} cy={18} r={9.5} fill="#FB7185" />
    <Circle cx={43} cy={26} r={9.5} fill="#FB7185" />
    <Circle cx={39} cy={38} r={9.5} fill="#FB7185" />
    <Circle cx={25} cy={38} r={9.5} fill="#FB7185" />
    <Circle cx={21} cy={26} r={9.5} fill="#FB7185" />
    {/* Center */}
    <Circle cx={32} cy={29} r={8.5} fill="#FBBF24" />
    {/* Cute face in center */}
    <Circle cx={29} cy={28} r={1.2} fill="#78350F" />
    <Circle cx={35} cy={28} r={1.2} fill="#78350F" />
    <Path d="M30 31Q32 33 34 31" stroke="#78350F" strokeWidth={1.4} strokeLinecap="round" />
  </Svg>
);

export const GrassIconSvg: React.FC<{ size?: number }> = ({ size = 36 }) => (
  <Svg width={size} height={size} viewBox="0 0 64 64" fill="none">
    {/* Base mound */}
    <Ellipse cx={32} cy={54} rx={24} ry={5} fill="#DCFCE7" />
    {/* Grass blades */}
    <Path d="M14 54Q18 36 24 24Q22 38 20 54Z" fill="#16A34A" />
    <Path d="M22 54Q26 28 32 16Q30 34 27 54Z" fill="#22C55E" />
    <Path d="M29 54Q34 22 42 18Q37 36 34 54Z" fill="#15803D" />
    <Path d="M35 54Q42 32 48 26Q44 42 41 54Z" fill="#4ADE80" />
    <Path d="M42 54Q47 40 52 34Q48 46 46 54Z" fill="#16A34A" />
    {/* Tiny flower in grass */}
    <Circle cx={20} cy={38} r={3} fill="#FDE047" />
    <Circle cx={20} cy={38} r={1.2} fill="#F59E0B" />
  </Svg>
);

export const MomAvatarSvg: React.FC<{ size?: number }> = ({ size = 32 }) => (
  <Svg width={size} height={size} viewBox="0 0 64 64" fill="none">
    {/* Background Circle */}
    <Circle cx={32} cy={32} r={31} fill="#EEF2FF" stroke="#C7D2FE" strokeWidth={2} />
    {/* Hair Back */}
    <Path d="M16 34C14 20 22 8 32 8C42 8 50 20 48 34C48 44 46 48 44 50H20C18 48 16 44 16 34Z" fill="#374151" />
    {/* Shoulders & Clothes */}
    <Path d="M12 62C12 52 20 46 32 46C44 46 52 52 52 62V64H12V62Z" fill="#818CF8" />
    <Path d="M26 46L32 54L38 46Z" fill="#C7D2FE" />
    {/* Neck */}
    <Rect x={28} y={38} width={8} height={10} rx={2} fill="#FED7AA" />
    {/* Face */}
    <Ellipse cx={32} cy={30} rx={13} ry={14} fill="#FFEDD5" />
    {/* Hair Front / Bangs */}
    <Path d="M18 26C20 16 26 13 32 13C38 13 44 16 46 26C42 22 36 21 32 24C28 21 22 22 18 26Z" fill="#1F2937" />
    <Path d="M16 28C16 38 19 44 21 44C19 40 18 34 19 28Z" fill="#1F2937" />
    <Path d="M48 28C48 38 45 44 43 44C45 40 46 34 45 28Z" fill="#1F2937" />
    {/* Eyes (warm smile curved) */}
    <Path d="M25 29C26 27.5 28 27.5 29 29" stroke="#1F2937" strokeWidth={1.8} strokeLinecap="round" />
    <Path d="M35 29C36 27.5 38 27.5 39 29" stroke="#1F2937" strokeWidth={1.8} strokeLinecap="round" />
    {/* Cheeks */}
    <Circle cx={24} cy={33} r={2.5} fill="#FDA4AF" opacity={0.7} />
    <Circle cx={40} cy={33} r={2.5} fill="#FDA4AF" opacity={0.7} />
    {/* Smile */}
    <Path d="M28 35C29.5 38 34.5 38 36 35" stroke="#E11D48" strokeWidth={1.8} strokeLinecap="round" />
  </Svg>
);

export const AnAvatarSvg: React.FC<{ size?: number }> = ({ size = 54 }) => (
  <Svg width={size} height={size} viewBox="0 0 64 64" fill="none">
    {/* Background Circle */}
    <Circle cx={32} cy={32} r={31} fill="#FEF08A" stroke="#FDE047" strokeWidth={2} />
    {/* Pigtails / Hair Back */}
    <Circle cx={14} cy={30} r={8} fill="#451A03" />
    <Circle cx={50} cy={30} r={8} fill="#451A03" />
    {/* Hair ties (red) */}
    <Circle cx={18} cy={30} r={3} fill="#EF4444" />
    <Circle cx={46} cy={30} r={3} fill="#EF4444" />
    {/* Clothes (Yellow top + blue overalls) */}
    <Path d="M14 62C14 50 21 44 32 44C43 44 50 50 50 62V64H14V62Z" fill="#FBBF24" />
    <Path d="M20 52H24V64H20V52Z" fill="#3B82F6" />
    <Path d="M40 52H44V64H40V52Z" fill="#3B82F6" />
    <Path d="M22 60H42V64H22V60Z" fill="#3B82F6" />
    {/* Neck */}
    <Rect x={28} y={37} width={8} height={9} rx={2} fill="#FED7AA" />
    {/* Face */}
    <Circle cx={32} cy={30} r={14} fill="#FFEDD5" />
    {/* Bangs */}
    <Path d="M18 25C22 17 42 17 46 25C43 20 37 19 32 22C27 19 21 20 18 25Z" fill="#451A03" />
    {/* Cute Big Sparkling Eyes */}
    <Circle cx={26} cy={29} r={2.8} fill="#1F2937" />
    <Circle cx={25.2} cy={28} r={1} fill="#FFFFFF" />
    <Circle cx={38} cy={29} r={2.8} fill="#1F2937" />
    <Circle cx={37.2} cy={28} r={1} fill="#FFFFFF" />
    {/* Rosy Cheeks */}
    <Circle cx={22} cy={33} r={3} fill="#FB7185" opacity={0.7} />
    <Circle cx={42} cy={33} r={3} fill="#FB7185" opacity={0.7} />
    {/* Big Happy Smile */}
    <Path d="M27 34C28.5 39 35.5 39 37 34Z" fill="#DC2626" />
  </Svg>
);

export const BaoAvatarSvg: React.FC<{ size?: number }> = ({ size = 54 }) => (
  <Svg width={size} height={size} viewBox="0 0 64 64" fill="none">
    {/* Background Circle */}
    <Circle cx={32} cy={32} r={31} fill="#E0F2FE" stroke="#BAE6FD" strokeWidth={2} />
    {/* Hair Back */}
    <Circle cx={32} cy={28} r={16} fill="#292524" />
    {/* Spiky hair tops */}
    <Path d="M24 16L28 12L32 15L36 11L40 16" stroke="#292524" strokeWidth={4} strokeLinecap="round" />
    {/* Clothes (Teal T-shirt) */}
    <Path d="M14 62C14 50 21 44 32 44C43 44 50 50 50 62V64H14V62Z" fill="#0D9488" />
    {/* Neck */}
    <Rect x={28} y={37} width={8} height={9} rx={2} fill="#FED7AA" />
    {/* Face */}
    <Circle cx={32} cy={30} r={13.5} fill="#FFEDD5" />
    {/* Boy Bangs */}
    <Path d="M20 22L24 25L28 22L32 25L36 21L40 24L44 21" stroke="#292524" strokeWidth={3} strokeLinecap="round" />
    {/* Cheerful Eyes */}
    <Circle cx={26} cy={29} r={2.5} fill="#1F2937" />
    <Circle cx={25.3} cy={28.2} r={0.9} fill="#FFFFFF" />
    <Circle cx={38} cy={29} r={2.5} fill="#1F2937" />
    <Circle cx={37.3} cy={28.2} r={0.9} fill="#FFFFFF" />
    {/* Rosy Cheeks */}
    <Circle cx={22} cy={33} r={2.5} fill="#FB7185" opacity={0.6} />
    <Circle cx={42} cy={33} r={2.5} fill="#FB7185" opacity={0.6} />
    {/* Friendly Smile */}
    <Path d="M27 34C28.5 38 35.5 38 37 34" stroke="#78350F" strokeWidth={2} strokeLinecap="round" />
  </Svg>
);

export const MaterialPaperSvg: React.FC<{ size?: number }> = ({ size = 36 }) => (
  <Svg width={size} height={size} viewBox="0 0 64 64" fill="none">
    {/* Sheet 1 (Cyan) */}
    <Rect x={10} y={16} width={34} height={40} rx={4} transform="rotate(-10 10 16)" fill="#38BDF8" />
    {/* Sheet 2 (Yellow) */}
    <Rect x={18} y={12} width={34} height={40} rx={4} transform="rotate(6 18 12)" fill="#FBBF24" />
    {/* Sheet 3 (Coral Pink top sheet) */}
    <Rect x={16} y={14} width={32} height={38} rx={4} fill="#FB7185" stroke="#FFFFFF" strokeWidth={2} />
    {/* Decorative fold/corner */}
    <Path d="M36 14L48 26H36V14Z" fill="#F43F5E" />
    {/* White sparkles */}
    <Circle cx={26} cy={30} r={2} fill="#FFFFFF" opacity={0.8} />
    <Circle cx={34} cy={38} r={1.5} fill="#FFFFFF" opacity={0.8} />
  </Svg>
);

export const MaterialScissorsSvg: React.FC<{ size?: number }> = ({ size = 36 }) => (
  <Svg width={size} height={size} viewBox="0 0 64 64" fill="none">
    {/* Crossed silver blades */}
    <Path d="M20 12L34 32L46 48" stroke="#94A3B8" strokeWidth={6} strokeLinecap="round" />
    <Path d="M44 12L30 32L18 48" stroke="#CBD5E1" strokeWidth={6} strokeLinecap="round" />
    {/* Pivot screw */}
    <Circle cx={32} cy={30} r={3.5} fill="#F59E0B" stroke="#B45309" strokeWidth={1} />
    {/* Rounded safe blade tips */}
    <Circle cx={20} cy={12} r={3} fill="#94A3B8" />
    <Circle cx={44} cy={12} r={3} fill="#CBD5E1" />
    {/* Red/Coral finger rings */}
    <Circle cx={20} cy={48} r={9} stroke="#EF4444" strokeWidth={4.5} fill="#FEE2E2" />
    <Circle cx={44} cy={48} r={9} stroke="#EF4444" strokeWidth={4.5} fill="#FEE2E2" />
  </Svg>
);

export const MaterialCrayonsSvg: React.FC<{ size?: number }> = ({ size = 36 }) => (
  <Svg width={size} height={size} viewBox="0 0 64 64" fill="none">
    {/* Crayon 1: Blue */}
    <G transform="rotate(-15 20 40)">
      <Path d="M16 16L20 8L24 16V54H16V16Z" fill="#3B82F6" />
      <Rect x={16} y={20} width={8} height={26} fill="#93C5FD" stroke="#1D4ED8" strokeWidth={0.8} />
      <Path d="M16 32H24" stroke="#1D4ED8" strokeWidth={1.5} strokeDasharray="1 2" />
    </G>
    {/* Crayon 2: Yellow (Center) */}
    <Path d="M28 14L32 6L36 14V56H28V14Z" fill="#EAB308" />
    <Rect x={28} y={18} width={8} height={28} fill="#FEF08A" stroke="#CA8A04" strokeWidth={0.8} />
    <Path d="M28 32H36" stroke="#CA8A04" strokeWidth={1.5} strokeDasharray="1 2" />
    {/* Crayon 3: Red */}
    <G transform="rotate(15 44 40)">
      <Path d="M40 16L44 8L48 16V54H40V16Z" fill="#EF4444" />
      <Rect x={40} y={20} width={8} height={26} fill="#FCA5A5" stroke="#B91C1C" strokeWidth={0.8} />
      <Path d="M40 32H48" stroke="#B91C1C" strokeWidth={1.5} strokeDasharray="1 2" />
    </G>
  </Svg>
);

export const MaterialGlueSvg: React.FC<{ size?: number }> = ({ size = 36 }) => (
  <Svg width={size} height={size} viewBox="0 0 64 64" fill="none">
    {/* Glue Bottle Body */}
    <Rect x={20} y={26} width={24} height={32} rx={6} fill="#F8FAFC" stroke="#CBD5E1" strokeWidth={2} />
    {/* Blue Label */}
    <Rect x={22} y={32} width={20} height={18} rx={3} fill="#38BDF8" />
    <Path d="M25 40H39" stroke="#FFFFFF" strokeWidth={2} strokeLinecap="round" />
    <Circle cx={32} cy={44} r={2} fill="#FFFFFF" />
    {/* Neck & Orange Cap */}
    <Rect x={27} y={18} width={10} height={8} fill="#EA580C" />
    <Path d="M28 18L32 10L36 18H28Z" fill="#F97316" />
    {/* Glue drop */}
    <Path d="M48 20C48 24 44 28 44 28C44 28 40 24 40 20C40 18 42 16 44 16C46 16 48 18 48 20Z" fill="#38BDF8" opacity={0.85} />
  </Svg>
);

// ==========================================
// 13. MATERIAL ICONS WRAPPER (Screen 12)
// ==========================================
export const MaterialIconSvg: React.FC<{ type: 'paper' | 'scissors' | 'crayon' | 'glue'; size?: number }> = ({
  type,
  size = 38,
}) => {
  if (type === 'paper') return <MaterialPaperSvg size={size} />;
  if (type === 'scissors') return <MaterialScissorsSvg size={size} />;
  if (type === 'crayon') return <MaterialCrayonsSvg size={size} />;
  return <MaterialGlueSvg size={size} />;
};

// ==========================================
// 14. ENTITY ICONS (Screen 8)
// ==========================================
export const EntityIconImage: React.FC<{ type: 'butterfly' | 'flower' | 'sun' | 'grass'; size?: number }> = ({
  type,
  size = 38,
}) => {
  if (type === 'butterfly') return <ButterflyIconSvg size={size} />;
  if (type === 'flower') return <FlowerIconSvg size={size} />;
  if (type === 'sun') return <SunIconSvg size={size} />;
  return <GrassIconSvg size={size} />;
};

// ==========================================
// 15. AVATAR IMAGES (Profile, Dashboard, Feedback)
// ==========================================
export const ChildAvatarImage: React.FC<{ childName: string; size?: number }> = ({ childName, size = 54 }) => {
  const isAn = childName.toLowerCase().includes('an');
  return isAn ? <AnAvatarSvg size={size} /> : <BaoAvatarSvg size={size} />;
};

export const MomAvatarImage: React.FC<{ size?: number }> = ({ size = 28 }) => (
  <MomAvatarSvg size={size} />
);

export const GirlFeedbackAvatarImage: React.FC<{ size?: number }> = ({ size = 38 }) => (
  <AnAvatarSvg size={size} />
);

// ==========================================
// 16. PLAYFUL 3D/5D MICRO-ANIMATIONS FOR KIDS
// ==========================================

// 16-A. FLAPPING BUTTERFLY — 3D wing flap using scaleX + float
export const FlappingButterflySvg: React.FC<{ size?: number }> = ({ size = 38 }) => {
  const flapAnim = useRef(new Animated.Value(1)).current;
  const floatAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(flapAnim, { toValue: 0.35, duration: 240, useNativeDriver: true }),
        Animated.timing(flapAnim, { toValue: 1, duration: 240, useNativeDriver: true }),
      ])
    ).start();

    Animated.loop(
      Animated.sequence([
        Animated.timing(floatAnim, { toValue: -4, duration: 800, useNativeDriver: true }),
        Animated.timing(floatAnim, { toValue: 4, duration: 800, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  return (
    <Animated.View
      style={{
        transform: [{ translateY: floatAnim }, { scaleX: flapAnim }],
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <ButterflyIconSvg size={size} />
    </Animated.View>
  );
};

// 16-B. SPINNING SUN — 360-deg ray rotation + breathing scale
export const SpinningSunSvg: React.FC<{ size?: number }> = ({ size = 38 }) => {
  const spinAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.loop(
      Animated.timing(spinAnim, {
        toValue: 1,
        duration: 8000,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    ).start();

    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.08, duration: 1200, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 1200, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  const spin = spinAnim.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '360deg'] });

  return (
    <Animated.View
      style={{
        transform: [{ rotate: spin }, { scale: pulseAnim }],
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <SunIconSvg size={size} />
    </Animated.View>
  );
};

// 16-C. SWAYING FLOWER — gentle breeze dance
export const SwayingFlowerSvg: React.FC<{ size?: number }> = ({ size = 38 }) => {
  const swayAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(swayAnim, { toValue: 1, duration: 1400, useNativeDriver: true }),
        Animated.timing(swayAnim, { toValue: -1, duration: 1400, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  const sway = swayAnim.interpolate({ inputRange: [-1, 1], outputRange: ['-8deg', '8deg'] });

  return (
    <Animated.View
      style={{
        transform: [{ rotate: sway }],
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <FlowerIconSvg size={size} />
    </Animated.View>
  );
};

// 16-D. RIPPLING GRASS — elastic grass blade wobble
export const RipplingGrassSvg: React.FC<{ size?: number }> = ({ size = 38 }) => {
  const rippleAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(rippleAnim, { toValue: 1.08, duration: 900, useNativeDriver: true }),
        Animated.timing(rippleAnim, { toValue: 0.95, duration: 900, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  return (
    <Animated.View
      style={{
        transform: [{ scaleY: rippleAnim }],
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <GrassIconSvg size={size} />
    </Animated.View>
  );
};

// 16-E. MAGIC SCAN BEAM — sweeping futuristic AI laser beam across artwork
export const MagicScanBeam: React.FC<{ containerHeight?: number }> = ({ containerHeight = 140 }) => {
  const scanAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(scanAnim, { toValue: 1, duration: 2200, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(scanAnim, { toValue: 0, duration: 2200, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    ).start();
  }, []);

  const translateY = scanAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [4, containerHeight - 12],
  });

  return (
    <Animated.View
      pointerEvents="none"
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: 8,
        transform: [{ translateY }],
        zIndex: 10,
        flexDirection: 'row',
        alignItems: 'center',
      }}
    >
      <View
        style={{
          flex: 1,
          height: 3,
          backgroundColor: '#38BDF8',
          shadowColor: '#38BDF8',
          shadowOffset: { width: 0, height: 0 },
          shadowOpacity: 0.9,
          shadowRadius: 6,
          elevation: 5,
        }}
      />
      <View
        style={{
          width: 14,
          height: 14,
          borderRadius: 7,
          backgroundColor: '#67E8F9',
          borderWidth: 2,
          borderColor: '#FFFFFF',
          marginHorizontal: -7,
          shadowColor: '#38BDF8',
          shadowOffset: { width: 0, height: 0 },
          shadowOpacity: 1,
          shadowRadius: 8,
          elevation: 6,
        }}
      />
      <View
        style={{
          flex: 1,
          height: 3,
          backgroundColor: '#818CF8',
          shadowColor: '#818CF8',
          shadowOffset: { width: 0, height: 0 },
          shadowOpacity: 0.9,
          shadowRadius: 6,
          elevation: 5,
        }}
      />
    </Animated.View>
  );
};

// 16-F. LIVING AUDIO EQUALIZER — multi-frequency real-time dancing waveform
export const LivingAudioEqualizer: React.FC<{ isPlaying?: boolean }> = ({ isPlaying = false }) => {
  const BAR_CONFIGS = [
    { baseH: 14, minH: 6, maxH: 26, duration: 420 },
    { baseH: 24, minH: 8, maxH: 34, duration: 320 },
    { baseH: 36, minH: 10, maxH: 42, duration: 510 },
    { baseH: 18, minH: 6, maxH: 28, duration: 380 },
    { baseH: 30, minH: 8, maxH: 40, duration: 440 },
    { baseH: 42, minH: 12, maxH: 46, duration: 360 },
    { baseH: 26, minH: 8, maxH: 36, duration: 480 },
    { baseH: 16, minH: 6, maxH: 26, duration: 310 },
    { baseH: 34, minH: 10, maxH: 42, duration: 520 },
    { baseH: 40, minH: 12, maxH: 46, duration: 390 },
    { baseH: 28, minH: 8, maxH: 38, duration: 460 },
    { baseH: 14, minH: 6, maxH: 24, duration: 330 },
    { baseH: 22, minH: 8, maxH: 32, duration: 410 },
    { baseH: 10, minH: 4, maxH: 18, duration: 370 },
  ];

  const anims = useRef(BAR_CONFIGS.map(() => new Animated.Value(0.4))).current;

  useEffect(() => {
    if (!isPlaying) {
      anims.forEach((anim) => anim.setValue(0.3));
      return;
    }

    const loops = anims.map((anim, i) => {
      const cfg = BAR_CONFIGS[i];
      const animation = Animated.loop(
        Animated.sequence([
          Animated.timing(anim, { toValue: 1, duration: cfg.duration, useNativeDriver: false }),
          Animated.timing(anim, { toValue: 0.15, duration: cfg.duration * 0.9, useNativeDriver: false }),
        ])
      );
      animation.start();
      return animation;
    });

    return () => {
      loops.forEach((l) => l.stop());
    };
  }, [isPlaying]);

  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 2.5, height: 34, paddingHorizontal: 4 }}>
      {BAR_CONFIGS.map((cfg, idx) => {
        const height = anims[idx].interpolate({
          inputRange: [0, 1],
          outputRange: [cfg.minH, cfg.maxH],
        });
        const bg = idx % 3 === 0 ? '#0284C7' : idx % 3 === 1 ? '#38BDF8' : '#818CF8';
        return (
          <Animated.View
            key={idx}
            style={{
              width: 3.2,
              height: isPlaying ? height : cfg.baseH * 0.55,
              backgroundColor: bg,
              borderRadius: 1.6,
            }}
          />
        );
      })}
    </View>
  );
};

// 16-G. JELLY BOUNCE VIEW — springy squish & pop on press
export const JellyBounceView: React.FC<{
  children: React.ReactNode;
  onPress?: () => void;
  style?: any;
  containerStyle?: any;
  activeOpacity?: number;
}> = ({ children, onPress, style, containerStyle, activeOpacity = 0.85 }) => {
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const handlePressIn = () => {
    Animated.spring(scaleAnim, {
      toValue: 0.92,
      friction: 4,
      tension: 100,
      useNativeDriver: true,
    }).start();
  };

  const handlePressOut = () => {
    Animated.sequence([
      Animated.spring(scaleAnim, {
        toValue: 1.08,
        friction: 3,
        tension: 120,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        friction: 4,
        tension: 100,
        useNativeDriver: true,
      }),
    ]).start();
  };

  return (
    <TouchableOpacity
      activeOpacity={activeOpacity}
      onPress={onPress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      style={containerStyle}
    >
      <Animated.View style={[style, { transform: [{ scale: scaleAnim }] }]}>
        {children}
      </Animated.View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  logoContainer: {
    alignItems: 'center',
    marginVertical: 4,
  },
  logoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  logoText: {
    fontWeight: '900',
    letterSpacing: -0.5,
  },
  logoTagline: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.textSoft,
    marginTop: 4,
    textAlign: 'center',
  },
  artworkCard: {
    width: '100%',
    borderRadius: radius.lg,
    overflow: 'hidden',
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
  },
  miniPlayBtn: {
    position: 'absolute',
    bottom: 8,
    right: 8,
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.92)',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.15,
    shadowRadius: 2,
    elevation: 2,
  },
  playButton: {
    position: 'absolute',
    width: 58,
    height: 58,
    borderRadius: 29,
    backgroundColor: 'rgba(255, 255, 255, 0.94)',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.25,
    shadowRadius: 10,
    elevation: 6,
    borderWidth: 3,
    borderColor: colors.white,
  },
  catSpeechBubble: {
    position: 'absolute',
    top: -12,
    right: -8,
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
    paddingHorizontal: 10,
    paddingVertical: 7,
    maxWidth: 130,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 4,
    elevation: 3,
    zIndex: 10,
  },
  catSpeechText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#1E40AF',
    textAlign: 'center',
    lineHeight: 14,
  },
  catSpeechTail: {
    position: 'absolute',
    bottom: -8,
    left: 16,
    width: 0,
    height: 0,
    borderLeftWidth: 8,
    borderRightWidth: 0,
    borderTopWidth: 8,
    borderLeftColor: 'transparent',
    borderRightColor: 'transparent',
    borderTopColor: '#FFFFFF',
  },
  voiceSpeechBubble: {
    position: 'absolute',
    top: 10,
    right: 8,
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: '#BAE6FD',
    paddingHorizontal: 10,
    paddingVertical: 6,
    maxWidth: 110,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    zIndex: 10,
  },
  voiceSpeechText: {
    fontSize: 9.5,
    fontWeight: '700',
    color: '#0369A1',
    textAlign: 'center',
    lineHeight: 13,
  },
  voiceSpeechTail: {
    position: 'absolute',
    bottom: -6,
    left: 14,
    width: 0,
    height: 0,
    borderLeftWidth: 6,
    borderRightWidth: 0,
    borderTopWidth: 6,
    borderLeftColor: 'transparent',
    borderRightColor: 'transparent',
    borderTopColor: '#FFFFFF',
  },
});
