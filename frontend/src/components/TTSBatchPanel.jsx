import { useCallback, useEffect, useMemo, useState } from 'react';
import { Download, Pause, Play, RefreshCw, RotateCcw, Square, WandSparkles } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import toast from 'react-hot-toast';

import { API } from '../api/client';
import { listEngines, listTTSProviderVoices } from '../api/engines';
import {
  cancelTTSBatch,
  createTTSBatch,
  listTTSBatches,
  pauseTTSBatch,
  resumeTTSBatch,
  retryFailedTTSBatch,
} from '../api/ttsBatch';
import { Badge, Button, Input, Panel, Select } from '../ui';

const TONE = {
  queued: 'neutral',
  running: 'brand',
  paused: 'warn',
  completed: 'success',
  partial: 'warn',
  failed: 'danger',
  cancelled: 'neutral',
};

function splitInputs(value) {
  const paragraphs = value
    .split(/\n\s*\n/)
    .map((item) => item.trim())
    .filter(Boolean);
  if (paragraphs.length > 1) return paragraphs;
  return value
    .split(/\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function TTSBatchPanel() {
  const { t } = useTranslation();
  const [engines, setEngines] = useState([]);
  const [engineId, setEngineId] = useState('');
  const [modelId, setModelId] = useState('');
  const [voiceId, setVoiceId] = useState('');
  const [voices, setVoices] = useState([]);
  const [executionMode, setExecutionMode] = useState('standard');
  const [text, setText] = useState('');
  const [instruct, setInstruct] = useState('');
  const [jobs, setJobs] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const selectedEngine = engines.find((engine) => engine.id === engineId) || null;
  const inputs = useMemo(() => splitInputs(text), [text]);

  const reload = useCallback(async () => {
    const [catalogue, batchJobs] = await Promise.all([listEngines(), listTTSBatches()]);
    const available = (catalogue.tts?.backends || []).filter((engine) => engine.available);
    setEngines(available);
    setJobs(batchJobs);
    setEngineId((current) => current || catalogue.tts?.active || available[0]?.id || '');
  }, []);

  useEffect(() => {
    reload().catch(() => {});
  }, [reload]);

  useEffect(() => {
    const engine = engines.find((candidate) => candidate.id === engineId);
    if (!engine) return;
    setModelId(engine.active_model_id || engine.default_model_id || engine.models?.[0]?.id || '');
    setVoiceId(engine.active_voice_id || engine.default_voice_id || '');
    if (!engine.supports_provider_batch) setExecutionMode('standard');
    if (!engine.default_voice_id) {
      setVoices([]);
      return;
    }
    listTTSProviderVoices(engine.id)
      .then((response) => setVoices(response.voices || []))
      .catch(() => setVoices([]));
  }, [engineId, engines]);

  useEffect(() => {
    if (!jobs.some((job) => ['queued', 'running'].includes(job.status))) return undefined;
    const timer = setInterval(() => reload().catch(() => {}), 3000);
    return () => clearInterval(timer);
  }, [jobs, reload]);

  async function create() {
    if (!selectedEngine || !inputs.length) return;
    setSubmitting(true);
    try {
      await createTTSBatch({
        engine_id: selectedEngine.id,
        ...(modelId ? { model_id: modelId } : {}),
        ...(voiceId ? { voice_id: voiceId } : {}),
        execution_mode: executionMode,
        settings: {
          ...(instruct.trim() ? { instruct: instruct.trim() } : {}),
          concurrency: selectedEngine.is_local === false ? 3 : 1,
        },
        items: inputs.map((item) => ({ text: item })),
      });
      setText('');
      toast.success(t('ttsBatch.created', { count: inputs.length }));
      await reload();
    } catch (error) {
      toast.error(error?.message || t('common.error'));
    } finally {
      setSubmitting(false);
    }
  }

  async function act(action, id) {
    try {
      await action(id);
      await reload();
    } catch (error) {
      toast.error(error?.message || t('common.error'));
    }
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-[var(--space-4)]">
      <Panel padding="md" className="grid gap-[var(--space-3)] lg:grid-cols-[1fr_1fr]">
        <div className="flex flex-col gap-[8px]">
          <label className="flex flex-col gap-[4px] text-[12px]">
            <span>{t('ttsBatch.inputs')}</span>
            <textarea
              rows={8}
              value={text}
              onChange={(event) => setText(event.target.value)}
              placeholder={t('ttsBatch.inputPlaceholder')}
              className="min-h-[170px] resize-y rounded-[var(--radius-lg)] border border-transparent bg-[var(--chrome-bg-inset,rgba(255,255,255,0.04))] p-[10px] text-[13px] text-fg outline-none focus:ring-1 focus:ring-[var(--chrome-accent)]"
            />
          </label>
          <span className="font-mono text-[11px] text-fg-muted">
            {t('ttsBatch.itemCount', { count: inputs.length })}
          </span>
        </div>
        <div className="grid content-start gap-[10px] sm:grid-cols-2">
          <label className="flex flex-col gap-[4px] text-[12px]">
            <span>{t('engines.colEngine')}</span>
            <Select value={engineId} onChange={(event) => setEngineId(event.target.value)}>
              {engines.map((engine) => (
                <option key={engine.id} value={engine.id}>
                  {engine.display_name}
                </option>
              ))}
            </Select>
          </label>
          <label className="flex flex-col gap-[4px] text-[12px]">
            <span>{t('ttsBatch.execution')}</span>
            <Select
              value={executionMode}
              onChange={(event) => setExecutionMode(event.target.value)}
            >
              <option value="standard">{t('ttsBatch.standard')}</option>
              {selectedEngine?.supports_provider_batch && (
                <option value="provider_batch">{t('ttsBatch.providerBatch')}</option>
              )}
            </Select>
          </label>
          {selectedEngine?.models?.length > 0 && (
            <label className="flex flex-col gap-[4px] text-[12px]">
              <span>{t('engines.curatedModelLabel')}</span>
              <Select value={modelId} onChange={(event) => setModelId(event.target.value)}>
                {selectedEngine.models.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name}
                  </option>
                ))}
              </Select>
            </label>
          )}
          {voices.length > 0 && (
            <label className="flex flex-col gap-[4px] text-[12px]">
              <span>{t('stories.voice')}</span>
              <Select value={voiceId} onChange={(event) => setVoiceId(event.target.value)}>
                {voices.map((voice) => (
                  <option key={voice.id} value={voice.id}>
                    {voice.name}
                  </option>
                ))}
              </Select>
            </label>
          )}
          <label className="flex flex-col gap-[4px] text-[12px] sm:col-span-2">
            <span>{t('ttsBatch.instructions')}</span>
            <Input value={instruct} onChange={(event) => setInstruct(event.target.value)} />
          </label>
          <Button
            variant="primary"
            className="sm:col-span-2"
            leading={<WandSparkles size={12} />}
            disabled={!inputs.length || !selectedEngine || submitting}
            loading={submitting}
            onClick={create}
          >
            {t('ttsBatch.create')}
          </Button>
        </div>
      </Panel>

      <div className="flex items-center justify-between">
        <h2 className="m-0 text-[14px] font-semibold">{t('ttsBatch.jobs')}</h2>
        <Button size="sm" variant="subtle" leading={<RefreshCw size={11} />} onClick={reload}>
          {t('common.refresh')}
        </Button>
      </div>
      {jobs.length === 0 && (
        <Panel padding="lg" className="text-center text-fg-muted">
          {t('ttsBatch.empty')}
        </Panel>
      )}
      <div className="flex flex-col gap-[8px]">
        {jobs.map((job) => (
          <Panel key={job.id} padding="sm" className="flex flex-wrap items-center gap-[10px]">
            <div className="min-w-[180px] flex-1">
              <div className="flex items-center gap-[6px]">
                <strong>{job.engine_id}</strong>
                <Badge tone={TONE[job.status] || 'neutral'} size="xs">
                  {job.status}
                </Badge>
              </div>
              <div className="mt-[4px] h-[4px] overflow-hidden rounded bg-[var(--chrome-bg-inset,rgba(255,255,255,0.04))]">
                <div
                  className="h-full bg-[var(--chrome-accent)]"
                  style={{ width: `${(job.progress?.fraction || 0) * 100}%` }}
                />
              </div>
              <span className="font-mono text-[10px] text-fg-muted">
                {job.progress?.completed || 0}/{job.progress?.total || 0} ·{' '}
                {job.voice_id || job.model_id || ''}
              </span>
            </div>
            {job.status === 'running' && (
              <Button
                size="sm"
                variant="subtle"
                leading={<Pause size={11} />}
                onClick={() => act(pauseTTSBatch, job.id)}
              >
                {t('common.pause')}
              </Button>
            )}
            {job.status === 'paused' && (
              <Button
                size="sm"
                variant="subtle"
                leading={<Play size={11} />}
                onClick={() => act(resumeTTSBatch, job.id)}
              >
                {t('batch.watch_resume')}
              </Button>
            )}
            {['queued', 'running', 'paused'].includes(job.status) && (
              <Button
                size="sm"
                variant="subtle"
                leading={<Square size={11} />}
                onClick={() => act(cancelTTSBatch, job.id)}
              >
                {t('common.cancel')}
              </Button>
            )}
            {['partial', 'failed'].includes(job.status) && (
              <Button
                size="sm"
                variant="subtle"
                leading={<RotateCcw size={11} />}
                onClick={() => act(retryFailedTTSBatch, job.id)}
              >
                {t('ttsBatch.retryFailed')}
              </Button>
            )}
            {job.output_path && (
              <a
                href={`${API}/audio/${job.output_path}`}
                download
                className="inline-flex h-[28px] items-center gap-[5px] rounded-[var(--radius-lg)] border border-transparent bg-[var(--chrome-bg-inset,rgba(255,255,255,0.04))] px-[9px] text-[11px] text-fg no-underline hover:bg-[var(--chrome-hover-bg)]"
              >
                <Download size={11} /> {t('ttsBatch.download')}
              </a>
            )}
          </Panel>
        ))}
      </div>
    </div>
  );
}
