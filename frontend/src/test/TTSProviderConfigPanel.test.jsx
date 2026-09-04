import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  getConfig: vi.fn(),
  listVoices: vi.fn(),
  updateConfig: vi.fn(),
}));

vi.mock('../api/engines', () => ({
  getTTSProviderConfiguration: mocks.getConfig,
  listTTSProviderVoices: mocks.listVoices,
  updateTTSProviderConfiguration: mocks.updateConfig,
}));

import TTSProviderConfigPanel from '../components/TTSProviderConfigPanel';

const engine = {
  id: 'gemini-tts',
  display_name: 'Google Gemini TTS',
  requires_api_key: true,
  default_voice_id: 'Kore',
  default_model_id: 'gemini-3.1-flash-tts-preview',
  models: [{ id: 'gemini-3.1-flash-tts-preview', name: 'Gemini 3.1 Flash TTS Preview' }],
};

describe('TTSProviderConfigPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getConfig.mockResolvedValue({
      engine_id: 'gemini-tts',
      voice_id: 'Kore',
      model_id: 'gemini-3.1-flash-tts-preview',
      requires_api_key: true,
      credential_configured: false,
      credential_stored: false,
    });
    mocks.listVoices.mockResolvedValue({
      engine_id: 'gemini-tts',
      voices: [
        { id: 'Kore', name: 'Kore' },
        { id: 'Puck', name: 'Puck' },
      ],
    });
    mocks.updateConfig.mockResolvedValue({
      voice_id: 'Puck',
      model_id: 'gemini-3.1-flash-tts-preview',
      credential_configured: true,
    });
  });

  it('saves the key and selected provider voice without exposing the key', async () => {
    render(<TTSProviderConfigPanel engine={engine} onSaved={vi.fn()} />);
    expect(await screen.findByText(/sends your text to its cloud API/i)).toBeInTheDocument();

    fireEvent.change(screen.getByDisplayValue('Kore'), { target: { value: 'Puck' } });
    fireEvent.change(screen.getByLabelText(/api key/i), { target: { value: 'secret-value' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() =>
      expect(mocks.updateConfig).toHaveBeenCalledWith('gemini-tts', {
        voice_id: 'Puck',
        model_id: 'gemini-3.1-flash-tts-preview',
        api_key: 'secret-value',
      }),
    );
    await waitFor(() => expect(screen.queryByDisplayValue('secret-value')).not.toBeInTheDocument());
  });
});
