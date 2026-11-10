const fs = require("node:fs");
const path = require("node:path");

const repositoryRoot = path.resolve(__dirname, "../..");
const rootEnvPath = path.join(repositoryRoot, ".env");
const publicMobileConfigKeys = new Set([
  "VITE_FIREBASE_API_KEY",
  "VITE_FIREBASE_AUTH_DOMAIN",
  "VITE_FIREBASE_PROJECT_ID",
  "VITE_FIREBASE_APP_ID",
  "SKETCH2LIFE_MOBILE_API_BASE_URL",
]);

function readRootEnv() {
  if (!fs.existsSync(rootEnvPath)) return {};
  const values = {};
  for (const line of fs.readFileSync(rootEnvPath, "utf8").split(/\r?\n/)) {
    const match = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$/);
    if (!match || match[2].startsWith("#")) continue;
    let value = match[2];
    if (
      value.length >= 2 &&
      ((value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'")))
    ) {
      value = value.slice(1, -1);
    }
    values[match[1]] = value;
  }
  return values;
}

const rootEnv = readRootEnv();
const publicMobileConfig = Object.fromEntries(
  [...publicMobileConfigKeys].map((key) => [
    key,
    process.env[key] ?? rootEnv[key] ?? "",
  ]),
);

function inlinePublicFirebaseConfig({ types: t }) {
  return {
    name: "inline-root-public-mobile-config",
    visitor: {
      MemberExpression(expressionPath) {
        const node = expressionPath.node;
        if (node.computed || !t.isIdentifier(node.property)) return;
        const envObject = node.object;
        if (
          !t.isMemberExpression(envObject) ||
          envObject.computed ||
          !t.isIdentifier(envObject.object, { name: "process" }) ||
          !t.isIdentifier(envObject.property, { name: "env" })
        ) {
          return;
        }
        const key = node.property.name;
        if (!publicMobileConfigKeys.has(key)) return;
        expressionPath.replaceWith(t.stringLiteral(publicMobileConfig[key]));
      },
    },
  };
}

module.exports = {
  presets: ["module:@react-native/babel-preset"],
  plugins: [inlinePublicFirebaseConfig],
};
