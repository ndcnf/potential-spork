import { afterEach, describe, expect, it, vi } from 'vitest'

import { api } from '@/services/api'

describe('api service', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('throws the FastAPI detail message when an import request fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 502,
        json: vi.fn().mockResolvedValue({
          detail: 'Source NIFFF indisponible: 404 Client Error',
        }),
      }),
    )

    await expect(api.importCatalog(2025, 'prod')).rejects.toThrow('Source NIFFF indisponible: 404 Client Error')
  })
})
