import React, { useState } from 'react';
import { parentModule } from './src/parent/ParentModule';
import ParentExpoApp from './src/parent/presentation/ParentExpoApp';
import SplashScreen from './src/splash/SplashScreen';

/** Application composition root: wire adapters into the presentation shell once. */
export default function App(): React.JSX.Element {
  const [splashVisible, setSplashVisible] = useState(true);

  if (splashVisible) {
    return <SplashScreen onFinished={() => setSplashVisible(false)} />;
  }

  return <ParentExpoApp application={parentModule} />;
}
