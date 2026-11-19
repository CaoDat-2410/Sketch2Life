import React, { useState } from 'react';
import { initialWindowMetrics, SafeAreaProvider } from 'react-native-safe-area-context';
import { parentModule } from './src/parent/ParentModule';
import ParentExpoApp from './src/parent/presentation/ParentExpoApp';
import SplashScreen from './src/splash/SplashScreen';

/** Application composition root: wire adapters into the presentation shell once. */
export default function App(): React.JSX.Element {
  const [splashVisible, setSplashVisible] = useState(true);

  return (
    <SafeAreaProvider initialMetrics={initialWindowMetrics}>
      {splashVisible ? (
        <SplashScreen onFinished={() => setSplashVisible(false)} />
      ) : (
        <ParentExpoApp application={parentModule} />
      )}
    </SafeAreaProvider>
  );
}
