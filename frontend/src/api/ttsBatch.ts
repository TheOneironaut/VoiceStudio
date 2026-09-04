import { apiJson, apiPost } from './client';

export type TTSBatchStatus =
  | 'queued'
  | 'running'
  | 'paused'
  | 'completed'
  | 'partial'
  | 'failed'
  | 'cancelled';

export interface TTSBatchItem {
  id: string;
  position: number;
  input_text: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  attempt_count: number;
  max_attempts: number;
  error: { code?: string; message?: string } | null;
  output_path: string | null;
  checksum: string | null;
}

export interface TTSBatchJob {
  id: string;
  engine_id: string;
  model_id: string | null;
  voice_id: string | null;
  settings: Record<string, unknown>;
  execution_mode: 'standard' | 'provider_batch';
  status: TTSBatchStatus;
  provider_batch_id: string | null;
  output_path: string | null;
  error: { code?: string; message?: string; count?: number } | null;
  created_at: number;
  updated_at: number;
  finished_at: number | null;
  items: TTSBatchItem[];
  progress: { completed: number; total: number; fraction: number };
}

export async function createTTSBatch(input: {
  engine_id: string;
  model_id?: string;
  voice_id?: string;
  settings?: Record<string, unknown>;
  execution_mode: 'standard' | 'provider_batch';
  items: Array<{ text: string }>;
}): Promise<TTSBatchJob> {
  return apiPost('/tts/batches', input);
}

export async function listTTSBatches(status?: TTSBatchStatus): Promise<TTSBatchJob[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : '';
  return apiJson(`/tts/batches${query}`);
}

export const pauseTTSBatch = (id: string) => apiPost<TTSBatchJob>(`/tts/batches/${id}/pause`, {});
export const resumeTTSBatch = (id: string) => apiPost<TTSBatchJob>(`/tts/batches/${id}/resume`, {});
export const cancelTTSBatch = (id: string) => apiPost<TTSBatchJob>(`/tts/batches/${id}/cancel`, {});
export const retryFailedTTSBatch = (id: string) =>
  apiPost<{ retried: number; job: TTSBatchJob }>(`/tts/batches/${id}/retry-failed`, {});
