import {AppRegistry} from 'react-native';

import {AppRoot} from './src/app/AppRoot';
import {name as appName} from './app.json';

AppRegistry.registerComponent(appName, () => AppRoot);
