import React from 'react';
import { parentModule } from './src/parent/ParentModule';
import ParentExpoApp from './src/parent/presentation/ParentExpoApp';

/** Application composition root: wire adapters into the presentation shell once. */
export default function App(): React.JSX.Element {
  return <ParentExpoApp application={parentModule} />;
}
