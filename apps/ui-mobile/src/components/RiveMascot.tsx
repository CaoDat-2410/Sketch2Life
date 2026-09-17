import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  TouchableOpacity,
  ViewStyle,
  Image,
} from 'react-native';
import { colors, radius, shadows } from '../theme';

interface RiveMascotProps {
  type?: 'robot' | 'dino' | 'girl' | 'butterfly';
  size?: number;
  bubbleText?: string;
  holdingArt?: boolean;
  onPress?: () => void;
  style?: ViewStyle;
}

export const RiveMascot: React.FC<RiveMascotProps> = ({
  type = 'robot',
  size = 140,
  bubbleText,
  holdingArt = false,
  onPress,
  style,
}) => {
  const floatAnim = useRef(new Animated.Value(0)).current;
  const breathAnim = useRef(new Animated.Value(1)).current;
  const bounceAnim = useRef(new Animated.Value(1)).current;

  // 1. Idle Floating & Breathing Loop
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.parallel([
          Animated.timing(floatAnim, {
            toValue: -8,
            duration: 1500,
            useNativeDriver: true,
          }),
          Animated.timing(breathAnim, {
            toValue: 1.04,
            duration: 1500,
            useNativeDriver: true,
          }),
        ]),
        Animated.parallel([
          Animated.timing(floatAnim, {
            toValue: 0,
            duration: 1500,
            useNativeDriver: true,
          }),
          Animated.timing(breathAnim, {
            toValue: 1,
            duration: 1500,
            useNativeDriver: true,
          }),
        ]),
      ])
    ).start();
  }, []);

  // 2. Interactive Tap Bounce
  const handleTap = () => {
    Animated.sequence([
      Animated.timing(bounceAnim, {
        toValue: 1.15,
        duration: 120,
        useNativeDriver: true,
      }),
      Animated.spring(bounceAnim, {
        toValue: 1,
        friction: 3,
        tension: 40,
        useNativeDriver: true,
      }),
    ]).start();

    if (onPress) onPress();
  };

  const getMascotSource = () => {
    switch (type) {
      case 'robot':
        return require('../../assets/images/robot_ai.png');
      case 'dino':
        return require('../../assets/images/onboarding_hero.png');
      case 'girl':
        return require('../../assets/images/voice_girl.png');
      case 'butterfly':
        return require('../../assets/images/detail_hero_butterfly.png');
      default:
        return require('../../assets/images/robot_ai.png');
    }
  };

  return (
    <View style={[styles.container, style]}>
      {/* Interactive Speech Bubble */}
      {bubbleText && (
        <View style={styles.bubbleWrapper}>
          <View style={styles.bubble}>
            <Text style={styles.bubbleText}>{bubbleText}</Text>
          </View>
          <View style={styles.bubblePointer} />
        </View>
      )}

      {/* Interactive Mascot Body with 3D/5D Bounce & Float */}
      <TouchableOpacity activeOpacity={0.9} onPress={handleTap}>
        <Animated.View
          style={{
            transform: [
              { translateY: floatAnim },
              { scale: bounceAnim },
              { scaleY: breathAnim },
            ],
          }}
        >
          <Image
            source={getMascotSource()}
            style={{ width: size, height: size, resizeMode: 'contain' }}
          />
        </Animated.View>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  bubbleWrapper: {
    position: 'absolute',
    top: -46,
    zIndex: 10,
    alignItems: 'center',
  },
  bubble: {
    backgroundColor: colors.white,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: radius.md,
    borderWidth: 2,
    borderColor: colors.yellowDeep,
    ...shadows.soft,
  },
  bubbleText: {
    fontSize: 12,
    fontWeight: '800',
    color: colors.textBody,
  },
  bubblePointer: {
    width: 0,
    height: 0,
    borderLeftWidth: 6,
    borderRightWidth: 6,
    borderTopWidth: 6,
    borderStyle: 'solid',
    backgroundColor: 'transparent',
    borderLeftColor: 'transparent',
    borderRightColor: 'transparent',
    borderTopColor: colors.yellowDeep,
  },
});
