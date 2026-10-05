const path = require('node:path');
const fs = require('node:fs');
const {getDefaultConfig} = require('expo/metro-config');

const appRoot = __dirname;
const workspaceRoot = path.resolve(appRoot, '../..');
const pnpmVirtualStore = path.join(workspaceRoot, 'node_modules', '.pnpm');
const config = getDefaultConfig(appRoot);

// Keep the native dev-client's `index` entry rooted in this app. The previous
// config watched the entire pnpm virtual store, which made Metro discover the
// sibling apps/mobile React Native 0.87 package while bundling this Expo 52 app
// (which must stay on React Native 0.76.9).
config.watchFolders = [
  pnpmVirtualStore,
  path.join(workspaceRoot, 'packages', 'art-renderer'),
];
config.resolver.disableHierarchicalLookup = true;
config.resolver.nodeModulesPaths = [
  path.join(appRoot, 'node_modules'),
  ...fs.readdirSync(pnpmVirtualStore, {withFileTypes: true})
    .filter((entry) => entry.isDirectory() && !entry.name.startsWith('.'))
    .map((entry) => path.join(pnpmVirtualStore, entry.name, 'node_modules')),
];

module.exports = config;
