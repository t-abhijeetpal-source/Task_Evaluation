'use strict';

const { parseArgs, formatResult, run, EXIT } = require('../src/convert');

describe('parseArgs', () => {
  test('parses valid args and uppercases currencies', () => {
    expect(parseArgs(['100', 'usd', 'inr'])).toEqual({ amount: 100, from: 'USD', to: 'INR' });
  });
  test('rejects wrong arg count', () => {
    expect(() => parseArgs(['100', 'USD'])).toThrow(/Usage/);
  });
  test('rejects non-numeric amount', () => {
    expect(() => parseArgs(['abc', 'USD', 'INR'])).toThrow(/number/);
  });
  test('rejects non-positive amount', () => {
    expect(() => parseArgs(['-5', 'USD', 'INR'])).toThrow(/positive/);
  });
});

describe('formatResult', () => {
  test('formats as "<amount> <from> = <converted> <to>"', () => {
    expect(formatResult(100, 'USD', { converted_amount: 8300, to: 'INR' })).toBe(
      '100 USD = 8300 INR'
    );
  });
});

describe('run', () => {
  // --- Test 1: successful API call --------------------------------------
  test('prints the conversion and exits 0 on success', async () => {
    const client = {
      post: jest.fn().mockResolvedValue({ data: { converted_amount: 8300, from: 'USD', to: 'INR' } }),
    };
    const logs = [];
    const code = await run(['100', 'USD', 'INR'], { client, log: (m) => logs.push(m), error: () => {} });
    expect(code).toBe(EXIT.OK);
    expect(logs[0]).toBe('100 USD = 8300 INR');
    expect(client.post).toHaveBeenCalledWith(expect.stringMatching(/\/convert$/), {
      amount: 100,
      from: 'USD',
      to: 'INR',
    });
  });

  // --- Test 2: invalid currency handling (API 400) ----------------------
  test('reports unsupported currency and exits 1', async () => {
    const err = new Error('Request failed with status code 400');
    err.response = { status: 400, data: { error: 'Unsupported currency' } };
    const client = { post: jest.fn().mockRejectedValue(err) };
    const errs = [];
    const code = await run(['100', 'USD', 'GBP'], { client, log: () => {}, error: (m) => errs.push(m) });
    expect(code).toBe(EXIT.SERVER_ERROR);
    expect(errs[0]).toMatch(/Unsupported currency/);
  });

  // --- Test 3: backend unavailable --------------------------------------
  test('reports API unavailable and exits 3 on connection refused', async () => {
    const err = new Error('connect ECONNREFUSED 127.0.0.1:8000');
    err.code = 'ECONNREFUSED';
    err.request = {};
    const client = { post: jest.fn().mockRejectedValue(err) };
    const errs = [];
    const code = await run(['100', 'USD', 'INR'], { client, log: () => {}, error: (m) => errs.push(m) });
    expect(code).toBe(EXIT.API_UNAVAILABLE);
    expect(errs[0]).toMatch(/API unavailable/);
  });

  // --- Test 4: invalid CLI arguments ------------------------------------
  test('reports usage and exits 2 on bad arguments', async () => {
    const errs = [];
    const code = await run(['100', 'USD'], { log: () => {}, error: (m) => errs.push(m) });
    expect(code).toBe(EXIT.BAD_ARGS);
    expect(errs[0]).toMatch(/Usage/);
  });
});
