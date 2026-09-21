import base from './electron-builder.config.mjs';

/** @type {import('electron-builder').Configuration} */
export default {
  ...base,
  appId: 'com.theoneironaut.voicestudio-gemini',
  productName: 'VoiceStudio Gemini',
  artifactName: 'VoiceStudio-Gemini-Windows-x64.${ext}',
  extraMetadata: {
    ...base.extraMetadata,
    name: 'voicestudio-gemini',
    productName: 'VoiceStudio Gemini',
    voicestudioEdition: 'gemini',
  },
  win: {
    ...base.win,
    target: [{ target: 'msi', arch: ['x64'] }],
  },
  msi: {
    oneClick: true,
    perMachine: false,
    runAfterFinish: false,
    createDesktopShortcut: true,
    createStartMenuShortcut: true,
    shortcutName: 'VoiceStudio Gemini',
  },
  // This fork publishes a rolling installer without compatible updater
  // manifests. The compiled Gemini edition also disables upstream feeds.
  publish: null,
};
