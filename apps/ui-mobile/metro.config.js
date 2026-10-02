const path = require('node:path');
const {getDefaultConfig} = require('expo/metro-config');

const appRoot = __dirname;
const workspaceRoot = path.resolve(appRoot, '../..');
const config = getDefaultConfig(appRoot);

// Keep the native dev-client's `index` entry rooted in this app. Metro still
// needs the pnpm store and the shared renderer package visible through symlinks.
config.watchFolders = [
  path.join(workspaceRoot, 'node_modules', '.pnpm'),
  path.join(workspaceRoot, 'packages', 'art-renderer'),
];
config.resolver.nodeModulesPaths = [
  path.join(appRoot, 'node_modules'),
  path.join(workspaceRoot, 'node_modules'),
];

module.exports = config;
