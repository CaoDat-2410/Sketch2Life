import { AppRegistry } from 'react-native';
import App from './App';

// Register directly for the native dev build. This keeps the Android entry
// point deterministic when Expo's dev-tools wrapper is unavailable in the
// generated standalone project.
AppRegistry.registerComponent('main', () => App);
