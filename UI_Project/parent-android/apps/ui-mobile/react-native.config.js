/**
 * Keep Expo's Android package import aligned with Expo SDK 52 when the
 * workspace is installed with pnpm's isolated node_modules layout.
 */
module.exports = {
  dependencies: {
    expo: {
      platforms: {
        android: {
          packageImportPath: 'import expo.modules.ExpoModulesPackage;',
          packageInstance: 'new ExpoModulesPackage()',
        },
      },
    },
  },
};
