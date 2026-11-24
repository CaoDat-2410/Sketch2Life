const fs = require('node:fs');
const path = require('node:path');

function findWorkspaceEnvPath(startDirectory) {
  let directory = path.resolve(startDirectory);

  while (true) {
    const workspaceMarker = path.join(directory, 'pnpm-workspace.yaml');
    if (fs.existsSync(workspaceMarker)) {
      const envPath = path.join(directory, '.env');
      if (fs.existsSync(envPath)) return envPath;
    }

    const parent = path.dirname(directory);
    if (parent === directory) return null;
    directory = parent;
  }
}

function readRootEnv(startDirectory) {
  const envPath = findWorkspaceEnvPath(startDirectory);
  if (!envPath) return {};

  const values = {};
  for (const line of fs.readFileSync(envPath, 'utf8').split(/\r?\n/)) {
    const match = line.match(/^\s*(?:export\s+)?([A-Z0-9_]+)\s*=\s*(.*?)\s*$/);
    if (!match || match[1].startsWith('#')) continue;

    let value = match[2];
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    values[match[1]] = value;
  }
  return values;
}

module.exports = { findWorkspaceEnvPath, readRootEnv };
