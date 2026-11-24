import { afterEach, describe, expect, it } from 'vitest';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { findWorkspaceEnvPath, readRootEnv } from '../config/rootEnv';

const temporaryRoots: string[] = [];

function createWorkspace(): string {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'sketch2life-env-'));
  temporaryRoots.push(root);
  return root;
}

afterEach(() => {
  for (const root of temporaryRoots.splice(0)) fs.rmSync(root, { recursive: true, force: true });
});

describe('Expo root .env resolution', () => {
  it('finds the CAPSTONE .env above a nested worktree with no separate .env', () => {
    const project = createWorkspace();
    const worktree = path.join(project, '.codex-worktrees', 'fe');
    const app = path.join(worktree, 'apps', 'ui-mobile');
    fs.mkdirSync(app, { recursive: true });
    fs.writeFileSync(path.join(project, 'pnpm-workspace.yaml'), 'packages: []\n');
    fs.writeFileSync(path.join(worktree, 'pnpm-workspace.yaml'), 'packages: []\n');
    fs.writeFileSync(path.join(project, '.env'), 'VITE_FIREBASE_PROJECT_ID=synthetic-project\n');

    expect(findWorkspaceEnvPath(app)).toBe(path.join(project, '.env'));
    expect(readRootEnv(app)).toEqual({ VITE_FIREBASE_PROJECT_ID: 'synthetic-project' });
  });

  it('prefers the nearest workspace .env when a checkout has its own file', () => {
    const project = createWorkspace();
    const worktree = path.join(project, '.codex-worktrees', 'fe');
    const app = path.join(worktree, 'apps', 'ui-mobile');
    fs.mkdirSync(app, { recursive: true });
    fs.writeFileSync(path.join(project, 'pnpm-workspace.yaml'), 'packages: []\n');
    fs.writeFileSync(path.join(project, '.env'), 'VITE_FIREBASE_PROJECT_ID=parent-project\n');
    fs.writeFileSync(path.join(worktree, 'pnpm-workspace.yaml'), 'packages: []\n');
    fs.writeFileSync(path.join(worktree, '.env'), 'VITE_FIREBASE_PROJECT_ID=worktree-project\n');

    expect(readRootEnv(app)).toEqual({ VITE_FIREBASE_PROJECT_ID: 'worktree-project' });
  });

  it('does not load an .env from an ancestor outside a pnpm workspace', () => {
    const parent = createWorkspace();
    const project = path.join(parent, 'project');
    const app = path.join(project, 'apps', 'ui-mobile');
    fs.mkdirSync(app, { recursive: true });
    fs.writeFileSync(path.join(parent, '.env'), 'SHOULD_NOT_LOAD=outside-workspace\n');
    fs.writeFileSync(path.join(project, 'pnpm-workspace.yaml'), 'packages: []\n');

    expect(findWorkspaceEnvPath(app)).toBeNull();
    expect(readRootEnv(app)).toEqual({});
  });
});
