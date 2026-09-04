import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  listEngines: vi.fn(),
  listVoices: vi.fn(),
  listBatches: vi.fn(),
  createBatch: vi.fn(),
}));

vi.mock('../api/engines', () => ({
  listEngines: mocks.listEngines,
  listTTSProviderVoices: mocks.listVoices,
}));
vi.mock('../api/ttsBatch', () => ({
  listTTSBatches: mocks.listBatches,
  createTTSBatch: mocks.createBatch,
  pauseTTSBatch: vi.fn(),
  resumeTTSBatch: vi.fn(),
  cancelTTSBatch: vi.fn(),
  retryFailedTTSBatch: vi.fn(),
}));

import TTSBatchPanel from '../components/TTSBatchPanel';

describe('TTSBatchPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.listBatches.mockResolvedValue([]);
    mocks.listVoices.mockResolvedValue({
      engine_id: 'gemini-tts',
      voices: [
        { id: 'Kore', name: 'Kore' },
        { id: 'Puck', name: 'Puck' },
      ],
    });
    mocks.listEngines.mockResolvedValue({
      tts: {
        active: 'gemini-tts',
        backends: [
          {
            id: 'gemini-tts',
            display_name: 'Google Gemini TTS',
            available: true,
            is_local: false,
            supports_provider_batch: true,
            default_model_id: 'gemini-3.1-flash-tts-preview',
            active_model_id: 'gemini-3.1-flash-tts-preview',
            default_voice_id: 'Kore',
            active_voice_id: 'Kore',
            models: [{ id: 'gemini-3.1-flash-tts-preview', name: 'Gemini 3.1 Flash TTS Preview' }],
          },
        ],
      },
    });
    mocks.createBatch.mockResolvedValue({ id: 'job-1' });
  });

  it('creates a provider-neutral batch with pinned Gemini settings', async () => {
    render(<TTSBatchPanel />);
    expect(await screen.findByText('Google Gemini TTS')).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText(/one paragraph per item/i), {
      target: { value: 'First paragraph\n\nSecond paragraph' },
    });
    fireEvent.change(screen.getByDisplayValue('Standard API'), {
      target: { value: 'provider_batch' },
    });
    fireEvent.change(screen.getByDisplayValue('Kore'), { target: { value: 'Puck' } });
    fireEvent.click(screen.getByRole('button', { name: 'Generate batch' }));

    await waitFor(() => expect(mocks.createBatch).toHaveBeenCalledTimes(1));
    expect(mocks.createBatch).toHaveBeenCalledWith(
      expect.objectContaining({
        engine_id: 'gemini-tts',
        model_id: 'gemini-3.1-flash-tts-preview',
        voice_id: 'Puck',
        execution_mode: 'provider_batch',
        items: [{ text: 'First paragraph' }, { text: 'Second paragraph' }],
      }),
    );
  });
});
