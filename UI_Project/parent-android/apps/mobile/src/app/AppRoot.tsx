import type {ReactElement} from 'react';

import {ParentWebPreview} from './ParentWebPreview';

/** Loads the existing Parent visual prototype from assets bundled in the Android app. */
export function AppRoot(): ReactElement {
  return <ParentWebPreview />;
}
