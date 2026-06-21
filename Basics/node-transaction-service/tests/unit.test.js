'use strict';

const logger = require('../src/logger');
const { toCents, fromCents } = require('../src/money');

describe('logger', () => {
  test('info writes a JSON line to stdout with fields', () => {
    const spy = jest.spyOn(process.stdout, 'write').mockImplementation(() => true);
    logger.info('hello', { request_id: 'r1' });
    const line = spy.mock.calls[0][0];
    spy.mockRestore();
    const obj = JSON.parse(line);
    expect(obj).toMatchObject({ level: 'info', msg: 'hello', request_id: 'r1' });
    expect(obj.ts).toBeTruthy();
  });

  test('warn and error write JSON lines to stderr', () => {
    const spy = jest.spyOn(process.stderr, 'write').mockImplementation(() => true);
    logger.warn('careful');
    logger.error('boom', { error: 'kaboom' });
    const levels = spy.mock.calls.map((c) => JSON.parse(c[0]).level);
    spy.mockRestore();
    expect(levels).toEqual(['warn', 'error']);
  });
});

describe('money', () => {
  test('toCents converts 2-dp amounts exactly', () => {
    expect(toCents(0.1)).toBe(10);
    expect(toCents(100.1)).toBe(10010);
    expect(toCents(0.05)).toBe(5);
  });

  test('fromCents round-trips without drift', () => {
    expect(fromCents(toCents(0.1) + toCents(0.2))).toBe(0.3);
    expect(fromCents(10010)).toBe(100.1);
  });
});
