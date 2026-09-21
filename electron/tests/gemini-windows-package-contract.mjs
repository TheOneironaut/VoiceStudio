import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import config from '../electron-builder.gemini-windows.config.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const artifactRequested = process.argv.includes('--artifact');

assert.equal(config.appId, 'com.theoneironaut.voicestudio-gemini');
assert.equal(config.productName, 'VoiceStudio Gemini');
assert.equal(config.extraMetadata.voicestudioEdition, 'gemini');
assert.equal(config.win.target[0].target, 'msi');
assert.deepEqual(config.win.target[0].arch, ['x64']);
assert.equal(config.artifactName, 'VoiceStudio-Gemini-Windows-x64.${ext}');
assert.equal(config.publish, null);

const bundledUv = config.extraResources.find((item) => item.to === 'tools/uv.exe');
assert(bundledUv, 'Gemini Electron package includes uv.exe');
assert(existsSync(bundledUv.from), 'Bundled uv.exe exists');

const viteConfig = readFileSync(resolve(root, 'electron.vite.config.ts'), 'utf8');
assert.match(viteConfig, /VOICESTUDIO_EDITION/);
assert.match(viteConfig, /__VOICESTUDIO_EDITION__/);

if (artifactRequested) {
  assert(existsSync(resolve(root, 'release/VoiceStudio-Gemini-Windows-x64.msi')));
  assert(existsSync(resolve(root, 'release/win-unpacked/VoiceStudio Gemini.exe')));
}

console.log(
  'PASS: Gemini Electron Windows identity, uv bundle, updater isolation and MSI artifact',
);
