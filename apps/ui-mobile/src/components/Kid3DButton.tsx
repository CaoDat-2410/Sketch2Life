import React, { useRef } from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  Animated,
  ViewStyle,
  TextStyle,
  View,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, radius, shadows } from '../theme';

interface Kid3DButtonProps {
  title: string;
  onPress: () => void;
  color?: 'blue' | 'green' | 'coral' | 'yellow';
  icon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  style?: ViewStyle;
  textStyle?: TextStyle;
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
}

export const Kid3DButton: React.FC<Kid3DButtonProps> = ({
  title,
  onPress,
  color = 'blue',
  icon,
  rightIcon,
  style,
  textStyle,
  size = 'md',
  disabled = false,
}) => {
  const pressAnim = useRef(new Animated.Value(0)).current;

  const handlePressIn = () => {
    Animated.spring(pressAnim, {
      toValue: 1,
      useNativeDriver: true,
    }).start();
  };

  const handlePressOut = () => {
    Animated.spring(pressAnim, {
      toValue: 0,
      useNativeDriver: true,
    }).start();
  };

  const colorGradients = {
    blue: ['#4FA8FF', '#2563EB'] as const,
    green: ['#34D399', '#059669'] as const,
    coral: ['#FB7185', '#E11D48'] as const,
    yellow: ['#FBBF24', '#D97706'] as const,
  };

  const shadowStyles = {
    blue: shadows.btn3dBlue,
    green: shadows.btn3dGreen,
    coral: shadows.btn3dCoral,
    yellow: {
      borderBottomWidth: 4,
      borderBottomColor: '#B45309',
      shadowColor: '#D97706',
      shadowOffset: { width: 0, height: 6 },
      shadowOpacity: 0.35,
      shadowRadius: 8,
      elevation: 4,
    },
  };

  const sizeStyles = {
    sm: { paddingVertical: 8, paddingHorizontal: 16, fontSize: 13 },
    md: { paddingVertical: 14, paddingHorizontal: 20, fontSize: 15 },
    lg: { paddingVertical: 17, paddingHorizontal: 24, fontSize: 17 },
  };

  const translateY = pressAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0, 3],
  });

  const scale = pressAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [1, 0.98],
  });

  return (
    <Animated.View style={[{ transform: [{ translateY }, { scale }] }, style]}>
      <TouchableOpacity
        accessibilityRole="button"
        accessibilityLabel={title}
        accessibilityState={{ disabled }}
        activeOpacity={0.9}
        disabled={disabled}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        onPress={onPress}
        style={[styles.btnOuter, shadowStyles[color], disabled && { opacity: 0.45 }]}
      >
        <LinearGradient
          colors={colorGradients[color]}
          start={{ x: 0, y: 0 }}
          end={{ x: 0, y: 1 }}
          style={[styles.btnInner, { paddingVertical: sizeStyles[size].paddingVertical, paddingHorizontal: sizeStyles[size].paddingHorizontal }]}
        >
          {icon && <View style={styles.iconContainer}>{icon}</View>}
          <Text style={[styles.btnText, { fontSize: sizeStyles[size].fontSize }, textStyle]}>
            {title}
          </Text>
          {rightIcon && <View style={styles.rightIconContainer}>{rightIcon}</View>}
        </LinearGradient>
      </TouchableOpacity>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  btnOuter: {
    borderRadius: radius.full,
    overflow: 'hidden',
  },
  btnInner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radius.full,
  },
  btnText: {
    color: colors.white,
    fontWeight: '800',
    textAlign: 'center',
    letterSpacing: 0.2,
  },
  iconContainer: {
    marginRight: 8,
  },
  rightIconContainer: {
    marginLeft: 8,
  },
});
