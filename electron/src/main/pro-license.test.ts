// @vitest-environment node
import { beforeEach, afterEach, expect, it, vi } from 'vitest';
const mocks = vi.hoisted(() => ({
  read: vi.fn(), write: vi.fn(), rename: vi.fn(), mkdir: vi.fn(), unlink: vi.fn(),
  available: vi.fn(), backend: vi.fn(), encrypt: vi.fn(), decrypt: vi.fn(), fetch: vi.fn(),
}));
vi.mock('electron', () => ({ app: { getPath: () => '/test' }, safeStorage: {
  isEncryptionAvailable: mocks.available, getSelectedStorageBackend: mocks.backend,
  encryptString: mocks.encrypt, decryptString: mocks.decrypt,
} }));
vi.mock('node:fs/promises', () => ({ readFile: mocks.read, writeFile: mocks.write, rename: mocks.rename, mkdir: mocks.mkdir, unlink: mocks.unlink }));
import { activateProLicense, deactivateProLicense } from './pro-license';
const key = 'test-license-123456';
const active = { activated: true, instance: { id: 'instance' }, meta: { store_id: 1, product_id: 2, variant_id: 3 }, license_key: { status: 'active', expires_at: null } };
beforeEach(() => {
  vi.resetAllMocks();
  vi.stubGlobal('__PRO_STORE_ID__', '1'); vi.stubGlobal('__PRO_PRODUCT_ID__', '2');
  vi.stubGlobal('__PRO_YEARLY_VARIANT_ID__', '3'); vi.stubGlobal('__PRO_LIFETIME_VARIANT_ID__', '4');
  vi.stubGlobal('fetch', mocks.fetch);
  mocks.read.mockRejectedValue(new Error('ENOENT'));
  mocks.fetch.mockResolvedValue({ ok: true, json: async () => active });
  mocks.available.mockReturnValue(true); mocks.backend.mockReturnValue('gnome_libsecret');
  mocks.encrypt.mockReturnValue(Buffer.from('encrypted'));
});
afterEach(() => vi.unstubAllGlobals());
it.each([false, true])('refuses plaintext storage before consuming an activation (encryption=%s)', async (available) => {
  mocks.available.mockReturnValue(available); mocks.backend.mockReturnValue('basic_text');
  expect(await activateProLicense(key)).toMatchObject({ active: false, error: 'storage' });
  expect(mocks.write).not.toHaveBeenCalled();
  expect(mocks.fetch).not.toHaveBeenCalled();
});
it('persists only encrypted license material', async () => {
  expect(await activateProLicense(key)).toMatchObject({ active: true });
  expect(mocks.encrypt).toHaveBeenCalledWith(JSON.stringify({ key, instanceId: 'instance' }));
  expect(mocks.write.mock.calls[0][1]).not.toContain(key);
  expect(JSON.parse(mocks.write.mock.calls[0][1])).toEqual({
    encryptedPayload: Buffer.from('encrypted').toString('base64'),
  });
});
it('decrypts the complete stored payload', async () => {
  mocks.read.mockResolvedValue(JSON.stringify({
    encryptedPayload: Buffer.from('encrypted').toString('base64'),
  }));
  mocks.decrypt.mockReturnValue(JSON.stringify({ key, instanceId: 'instance' }));
  mocks.fetch.mockResolvedValue({ ok: true, json: async () => ({ deactivated: true }) });
  expect(await deactivateProLicense()).toMatchObject({ active: false });
  expect(mocks.decrypt).toHaveBeenCalledWith(Buffer.from('encrypted'));
  const [url, init] = mocks.fetch.mock.calls[0];
  expect(url).toBe('https://api.lemonsqueezy.com/v1/licenses/deactivate');
  expect(init.body.toString()).toBe('license_key=test-license-123456&instance_id=instance');
  expect(mocks.unlink).toHaveBeenCalledWith(expect.stringMatching(/[\\/]test[\\/]pro-license\\.json$/));
});
it('preserves invalid deactivation errors without deleting the local license', async () => {
  mocks.read.mockResolvedValue(JSON.stringify({ fileKey: key, instanceId: 'instance' }));
  mocks.fetch.mockResolvedValue({ ok: false, status: 422 });
  expect(await deactivateProLicense()).toMatchObject({ active: true, error: 'invalid' });
  expect(mocks.unlink).not.toHaveBeenCalled();
});
