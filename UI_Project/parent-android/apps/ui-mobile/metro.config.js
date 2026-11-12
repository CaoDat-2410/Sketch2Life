const path = require('node:path');
const fs = require('node:fs');
const {getDefaultConfig} = require('expo/metro-config');

const appRoot = __dirname;
const workspaceRoot = path.resolve(appRoot, '../..');
const pnpmVirtualStore = path.join(workspaceRoot, 'node_modules', '.pnpm');
const lexicalAppNodeModules = path.join(appRoot, 'node_modules');
const appNodeModules = fs.realpathSync(lexicalAppNodeModules);
// Expo otherwise promotes the Metro server root to the monorepo root, which
// makes its relative entry resolver look for this app's index.ts in the wrong
// directory. This app already declares its pnpm and shared-package roots below.
process.env.EXPO_NO_METRO_WORKSPACE_ROOT = '1';
const config = getDefaultConfig(appRoot);
// Leave CPU capacity for the emulator and local API instead of spawning one
// transform worker for every host core during a cold build.
config.maxWorkers = 4;

// Keep the native dev-client's `index` entry rooted in this app. The previous
// config watched the entire pnpm virtual store, which made Metro discover the
// sibling apps/mobile React Native 0.87 package while bundling this Expo 52 app
// (which must stay on React Native 0.76.9).
// Metro indexes dependency files by their physical paths. Resolve junctions as
// well as symlinks so an isolated checkout can reuse the installed store.
config.watchFolders = [
  pnpmVirtualStore,
  path.join(workspaceRoot, 'packages', 'art-renderer'),
  // A junction can place app dependencies outside Metro's project root. Watch
  // that app's dependency links too, without watching sibling applications.
  ...(appNodeModules === lexicalAppNodeModules ? [] : [appNodeModules]),
].map((folder) => fs.realpathSync(folder));
config.resolver.disableHierarchicalLookup = true;
config.resolver.nodeModulesPaths = [
  appNodeModules,
  ...fs.readdirSync(pnpmVirtualStore, {withFileTypes: true})
    .filter((entry) => entry.isDirectory() && !entry.name.startsWith('.'))
    .map((entry) => path.join(pnpmVirtualStore, entry.name, 'node_modules')),
].filter((folder) => fs.existsSync(folder))
  .map((folder) => fs.realpathSync(folder));

module.exports = config;
