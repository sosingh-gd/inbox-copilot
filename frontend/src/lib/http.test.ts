import { describe, expect, it } from 'vitest';
import { ApiError, errorMessage, unwrap } from './http';

const response = (status: number) => new Response(null, { status });

describe('unwrap', () => {
  it('returns data for successful responses', async () => {
    await expect(
      unwrap(Promise.resolve({ data: { ok: true }, response: response(200) })),
    ).resolves.toEqual({ ok: true });
  });

  it('throws ApiError carrying the Problem Details code and field errors', async () => {
    const problem = {
      type: 'about:blank',
      title: 'Unprocessable Content',
      status: 422,
      code: 'validation_error',
      detail: 'Request validation failed',
      errors: [{ field: 'content', message: 'Too short', code: 'string_too_short' }],
    };

    const error = await unwrap(Promise.resolve({ error: problem, response: response(422) })).catch(
      (e: unknown) => e,
    );

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 422, code: 'validation_error' });
    expect((error as ApiError).fieldErrors[0]?.field).toBe('content');
    expect(errorMessage(error)).toBe('Request validation failed');
  });
});

describe('ApiError.fromResponse', () => {
  it('falls back to an http_ code when the body is not JSON', async () => {
    const error = await ApiError.fromResponse(
      new Response('<html>Bad gateway</html>', { status: 502 }),
    );

    expect(error.code).toBe('http_502');
  });
});
