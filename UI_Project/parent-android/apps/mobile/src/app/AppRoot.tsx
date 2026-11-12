import type {ReactElement} from 'react';

import {ParentNavigator} from './navigation/ParentNavigator';

/** Parent UI preview composition; authentication and server-backed actions remain gated. */
export function AppRoot(): ReactElement {
  return <ParentNavigator />;
}
