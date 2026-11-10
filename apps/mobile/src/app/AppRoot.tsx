import {useState} from 'react';
import {Pressable, SafeAreaView, StyleSheet, Text, View} from 'react-native';

import {createDemoAppDependencies} from './composition/dependencies';
import {ParentFlowScreen} from '../features/parent-flow/ParentFlowScreen';
import {FixtureFlowScreen} from '../features/fixture/FixtureFlowScreen';

const dependencies = createDemoAppDependencies();

/** Local Parent demo composition; replace the workflow adapter when API is approved. */
export function AppRoot(): React.JSX.Element {
  const [showFixtureLab, setShowFixtureLab] = useState(false);

  if (showFixtureLab) {
    return <SafeAreaView style={styles.fixtureShell}>
      <View style={styles.fixtureToolbar}>
        <Text style={styles.fixtureTitle}>Fixture lab riêng</Text>
        <Pressable accessibilityRole="button" onPress={() => setShowFixtureLab(false)} style={styles.returnButton}>
          <Text style={styles.returnButtonText}>Về Parent demo</Text>
        </Pressable>
      </View>
      <View style={styles.fixtureContent}><FixtureFlowScreen /></View>
    </SafeAreaView>;
  }

  return <ParentFlowScreen workflow={dependencies.parentWorkflow} onOpenFixtureLab={() => setShowFixtureLab(true)} />;
}

const styles = StyleSheet.create({
  fixtureShell: {flex: 1, backgroundColor: '#F5F7FC'},
  fixtureToolbar: {minHeight: 52, paddingHorizontal: 16, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center'},
  fixtureTitle: {fontSize: 13, fontWeight: '800', color: '#263653'},
  returnButton: {minHeight: 44, justifyContent: 'center', paddingHorizontal: 12},
  returnButtonText: {fontSize: 13, fontWeight: '700', color: '#315FEA'},
  fixtureContent: {flex: 1},
});
