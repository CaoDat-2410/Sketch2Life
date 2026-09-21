import React from 'react';
import { SafeAreaView, StatusBar, StyleSheet } from 'react-native';

import DemoWorkflowScreen from './src/demo/DemoWorkflowScreen';

export default function App() {
  return (
    <SafeAreaView style={styles.root}>
      <StatusBar barStyle="dark-content" backgroundColor="#F5F7F2" />
      <DemoWorkflowScreen />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#F5F7F2' },
});
