const fs = require('node:fs/promises');
const path = require('node:path');
const { withDangerousMod } = require('@expo/config-plugins');

const DEBUG_MANIFEST = [
  '<manifest xmlns:android="http://schemas.android.com/apk/res/android">',
  '  <application android:usesCleartextTraffic="true" />',
  '</manifest>',
  '',
].join('\n');

module.exports = function withDebugCleartextTraffic(config) {
  return withDangerousMod(config, [
    'android',
    async (modConfig) => {
      const appRoot = modConfig.modRequest.platformProjectRoot;
      const manifestPath = path.join(appRoot, 'app', 'src', 'debug', 'AndroidManifest.xml');
      await fs.mkdir(path.dirname(manifestPath), { recursive: true });

      let manifest;
      try {
        manifest = await fs.readFile(manifestPath, 'utf8');
      } catch (error) {
        if (error && typeof error === 'object' && 'code' in error && error.code === 'ENOENT') {
          await fs.writeFile(manifestPath, DEBUG_MANIFEST, 'utf8');
          return modConfig;
        }
        throw error;
      }

      if (/android:usesCleartextTraffic\s*=\s*"true"/.test(manifest)) {
        return modConfig;
      }
      if (/android:usesCleartextTraffic\s*=/.test(manifest)) {
        throw new Error('Debug manifest has an explicit cleartext policy; inspect it before changing it.');
      }
      if (!/<application\b/.test(manifest)) {
        throw new Error('Debug manifest has no application element; refusing to rewrite it.');
      }

      manifest = manifest.replace(
        /<application\b/,
        '<application android:usesCleartextTraffic="true"',
      );
      await fs.writeFile(manifestPath, manifest, 'utf8');
      return modConfig;
    },
  ]);
};
