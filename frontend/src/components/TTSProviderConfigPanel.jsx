import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Cloud, KeyRound } from 'lucide-react';
import { toast } from 'react-hot-toast';

import {
  getTTSProviderConfiguration,
  listTTSProviderVoices,
  updateTTSProviderConfiguration,
} from '../api/engines';
import { Button, Input, Select } from '../ui';

export default function TTSProviderConfigPanel({ engine, onSaved }) {
  const { t } = useTranslation();
  const [configuration, setConfiguration] = useState(null);
  const [voices, setVoices] = useState([]);
  const [voiceId, setVoiceId] = useState(engine.active_voice_id || engine.default_voice_id || '');
  const [modelId, setModelId] = useState(engine.active_model_id || engine.default_model_id || '');
  const [apiKey, setApiKey] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([getTTSProviderConfiguration(engine.id), listTTSProviderVoices(engine.id)])
      .then(([config, voiceResponse]) => {
        if (cancelled) return;
        setConfiguration(config);
        setVoiceId(config.voice_id || engine.default_voice_id || '');
        setModelId(config.model_id || engine.default_model_id || '');
        setVoices(voiceResponse.voices || []);
      })
      .catch(() => {
        if (!cancelled) setConfiguration({ credential_configured: false });
      });
    return () => {
      cancelled = true;
    };
  }, [
    engine.active_model_id,
    engine.active_voice_id,
    engine.default_model_id,
    engine.default_voice_id,
    engine.id,
  ]);

  async function save() {
    setSaving(true);
    try {
      const update = { voice_id: voiceId, model_id: modelId };
      if (apiKey) update.api_key = apiKey;
      const saved = await updateTTSProviderConfiguration(engine.id, update);
      setConfiguration(saved);
      setApiKey('');
      toast.success(t('app.toast_saved', { path: engine.display_name, name: engine.display_name }));
      await onSaved?.();
    } catch (error) {
      toast.error(t('engines.couldNotLoad', { message: error?.message || String(error) }));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="mt-[4px] max-w-[720px] rounded-[var(--chrome-radius-control)] border border-[color-mix(in_srgb,var(--chrome-accent)_18%,transparent)] bg-[color-mix(in_srgb,var(--chrome-accent)_5%,transparent)] p-[10px]">
      <p className="mb-[8px] flex items-start gap-[6px] text-[11px] text-[color:var(--chrome-fg-muted)]">
        <Cloud size={14} className="mt-[1px] shrink-0 text-[color:var(--chrome-accent)]" />
        {t('engines.cloudProviderNotice', { provider: engine.display_name })}
      </p>
      <div className="grid gap-[8px] sm:grid-cols-3">
        <label className="flex flex-col gap-[3px] text-[11px]">
          <span>{t('stories.voice')}</span>
          <Select size="sm" value={voiceId} onChange={(event) => setVoiceId(event.target.value)}>
            {voices.map((voice) => (
              <option key={voice.id} value={voice.id}>
                {voice.name}
                {voice.description ? ` — ${voice.description}` : ''}
              </option>
            ))}
          </Select>
        </label>
        <label className="flex flex-col gap-[3px] text-[11px]">
          <span>{t('engines.curatedModelLabel')}</span>
          <Select size="sm" value={modelId} onChange={(event) => setModelId(event.target.value)}>
            {(engine.models || []).map((model) => (
              <option key={model.id} value={model.id}>
                {model.name}
              </option>
            ))}
          </Select>
        </label>
        {engine.requires_api_key && (
          <label className="flex flex-col gap-[3px] text-[11px]">
            <span className="flex items-center gap-[4px]">
              <KeyRound size={11} /> {t('settings.llmp_api_key')}
            </span>
            <Input
              size="sm"
              type="password"
              value={apiKey}
              placeholder={
                configuration?.credential_configured ? '••••••••' : t('settings.llmp_key_paste')
              }
              autoComplete="off"
              onChange={(event) => setApiKey(event.target.value)}
            />
          </label>
        )}
      </div>
      <Button size="sm" className="mt-[8px]" disabled={saving} onClick={save}>
        {saving ? t('common.saving') : t('common.save')}
      </Button>
    </section>
  );
}
