import type {ReactElement} from 'react';

import {FixtureFlowScreen} from '../features/fixture/FixtureFlowScreen';

/** Fixture-only composition root until the approved backend client is wired. */
export function AppRoot(): ReactElement {
  return <FixtureFlowScreen />;
}
