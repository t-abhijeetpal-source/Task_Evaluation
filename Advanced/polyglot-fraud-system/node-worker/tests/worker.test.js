'use strict';

const { EventEmitter } = require('events');
const {
  callEngine,
  postScore,
  processFile,
  processQueueOnce,
} = require('../src/worker');

// ---------------------------------------------------------------------------
// Helpers — fake spawn / fake child process
// ---------------------------------------------------------------------------

/**
 * Build a fake child process that emits the given stdout/stderr and closes
 * with `exitCode`. Captures whatever is written to stdin.
 */
function makeFakeChild({ stdoutData = '', stderrData = '', exitCode = 0 } = {}) {
  const child = new EventEmitter();
  child.stdin = {
    written: '',
    write(chunk) {
      this.written += chunk;
    },
    end() {},
  };
  child.stdout = new EventEmitter();
  child.stderr = new EventEmitter();

  // Defer emission so listeners are attached first.
  process.nextTick(() => {
    if (stdoutData) child.stdout.emit('data', Buffer.from(stdoutData));
    if (stderrData) child.stderr.emit('data', Buffer.from(stderrData));
    child.emit('close', exitCode);
  });

  return child;
}

/**
 * A spawn that yields children from a queue of configs (one per attempt).
 */
function makeSequencedSpawn(configs) {
  let i = 0;
  const spawn = jest.fn(() => {
    const cfg = configs[Math.min(i, configs.length - 1)];
    i += 1;
    return makeFakeChild(cfg);
  });
  return spawn;
}

const validScore = {
  schema_version: '1.0',
  transaction_id: 'txn_001',
  score: 90,
  risk_level: 'high',
  reasons: ['high_amount', 'foreign_country', 'high_risk_merchant'],
};

const validTxn = {
  schema_version: '1.0',
  transaction_id: 'txn_001',
  user_id: 'user_123',
  amount: 15000,
  country: 'US',
  merchant_category: 'gambling',
  timestamp: '2026-06-17T10:00:00Z',
};

// ---------------------------------------------------------------------------
// callEngine
// ---------------------------------------------------------------------------

describe('callEngine', () => {
  test('resolves parsed score JSON on exit 0', async () => {
    const spawn = makeSequencedSpawn([
      { stdoutData: JSON.stringify(validScore), exitCode: 0 },
    ]);

    const result = await callEngine(JSON.stringify(validTxn), {
      spawn,
      engineBin: '/fake/fraud-engine',
    });

    expect(result).toEqual(validScore);
    expect(spawn).toHaveBeenCalledWith(
      '/fake/fraud-engine',
      [],
      expect.any(Object)
    );
  });

  test('writes the transaction JSON to engine stdin', async () => {
    let captured;
    const spawn = jest.fn(() => {
      const child = makeFakeChild({
        stdoutData: JSON.stringify(validScore),
        exitCode: 0,
      });
      captured = child.stdin;
      return child;
    });

    await callEngine(JSON.stringify(validTxn), { spawn });
    expect(captured.written).toBe(JSON.stringify(validTxn));
  });

  test('rejects on non-zero exit', async () => {
    const spawn = makeSequencedSpawn([
      { stderrData: 'bad input', exitCode: 1 },
    ]);
    await expect(
      callEngine('{bad}', { spawn })
    ).rejects.toThrow(/exited with code 1/);
  });

  test('rejects on unparseable stdout', async () => {
    const spawn = makeSequencedSpawn([
      { stdoutData: 'not json at all', exitCode: 0 },
    ]);
    await expect(
      callEngine(JSON.stringify(validTxn), { spawn })
    ).rejects.toThrow(/failed to parse engine output/);
  });

  test('A5-7: rejects (and kills child) when the engine never closes', async () => {
    // A child that attaches streams but NEVER emits "close" — simulates a hung
    // engine. Without a timeout the Promise would hang forever.
    let killed = false;
    const spawn = jest.fn(() => {
      const child = new EventEmitter();
      child.stdin = { write() {}, end() {} };
      child.stdout = new EventEmitter();
      child.stderr = new EventEmitter();
      child.kill = () => {
        killed = true;
      };
      return child; // no close event, ever
    });

    await expect(
      callEngine(JSON.stringify(validTxn), { spawn, timeoutMs: 20 })
    ).rejects.toThrow(/timed out after 20ms/);
    expect(killed).toBe(true);
  });

  test('A5-10: rejects when engine stdout exceeds the output cap', async () => {
    let killed = false;
    const spawn = jest.fn(() => {
      const child = new EventEmitter();
      child.stdin = { write() {}, end() {} };
      child.stdout = new EventEmitter();
      child.stderr = new EventEmitter();
      child.kill = () => {
        killed = true;
      };
      process.nextTick(() => {
        child.stdout.emit('data', Buffer.from('x'.repeat(50)));
      });
      return child;
    });

    await expect(
      callEngine(JSON.stringify(validTxn), {
        spawn,
        maxOutputBytes: 10,
        timeoutMs: 1000,
      })
    ).rejects.toThrow(/exceeded 10 bytes/);
    expect(killed).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// postScore
// ---------------------------------------------------------------------------

describe('postScore', () => {
  test('posts to the contract URL with the score body', async () => {
    const http = { post: jest.fn().mockResolvedValue({ status: 200 }) };

    await postScore(validScore, { http, apiUrl: 'http://api.test:8000' });

    expect(http.post).toHaveBeenCalledTimes(1);
    const [url, body] = http.post.mock.calls[0];
    expect(url).toBe(
      'http://api.test:8000/internal/transactions/txn_001/score'
    );
    expect(body).toEqual(validScore);
  });

  test('rejects when transaction_id is missing', async () => {
    const http = { post: jest.fn() };
    await expect(postScore({ score: 1 }, { http })).rejects.toThrow(
      /missing transaction_id/
    );
    expect(http.post).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// callEngine retry behaviour (exercised through processFile)
// ---------------------------------------------------------------------------

describe('processFile — engine retry', () => {
  function makeFakeFs(fileContents) {
    return {
      readFile: jest.fn().mockResolvedValue(fileContents),
      rename: jest.fn().mockResolvedValue(undefined),
      mkdir: jest.fn().mockResolvedValue(undefined),
    };
  }

  test('engine fails twice then succeeds -> success', async () => {
    const fs = makeFakeFs(JSON.stringify(validTxn));
    const http = { post: jest.fn().mockResolvedValue({ status: 200 }) };
    const spawn = makeSequencedSpawn([
      { stderrData: 'fail1', exitCode: 1 },
      { stderrData: 'fail2', exitCode: 1 },
      { stdoutData: JSON.stringify(validScore), exitCode: 0 },
    ]);

    const result = await processFile('/queue/txn_001.json', {
      fs,
      spawn,
      http,
      backoffMs: 0,
      queueDir: '/queue',
    });

    expect(result.success).toBe(true);
    expect(spawn).toHaveBeenCalledTimes(3);
    expect(http.post).toHaveBeenCalledTimes(1);
    // moved to processed/
    expect(fs.rename).toHaveBeenCalledWith(
      '/queue/txn_001.json',
      '/queue/processed/txn_001.json'
    );
  });

  test('engine always fails -> rejects after 3 attempts, moved to failed/', async () => {
    const fs = makeFakeFs(JSON.stringify(validTxn));
    const http = { post: jest.fn() };
    const spawn = makeSequencedSpawn([
      { stderrData: 'boom', exitCode: 1 },
    ]);

    const result = await processFile('/queue/txn_001.json', {
      fs,
      spawn,
      http,
      backoffMs: 0,
      queueDir: '/queue',
    });

    expect(result.success).toBe(false);
    expect(spawn).toHaveBeenCalledTimes(3);
    expect(http.post).not.toHaveBeenCalled();
    expect(fs.rename).toHaveBeenCalledWith(
      '/queue/txn_001.json',
      '/queue/failed/txn_001.json'
    );
  });
});

// ---------------------------------------------------------------------------
// processFile — happy path & malformed handling
// ---------------------------------------------------------------------------

describe('processFile', () => {
  test('happy path: scores, posts, moves to processed/', async () => {
    const fs = {
      readFile: jest.fn().mockResolvedValue(JSON.stringify(validTxn)),
      rename: jest.fn().mockResolvedValue(undefined),
      mkdir: jest.fn().mockResolvedValue(undefined),
    };
    const http = { post: jest.fn().mockResolvedValue({ status: 200 }) };
    const spawn = makeSequencedSpawn([
      { stdoutData: JSON.stringify(validScore), exitCode: 0 },
    ]);

    const result = await processFile('/queue/txn_001.json', {
      fs,
      spawn,
      http,
      backoffMs: 0,
      queueDir: '/queue',
    });

    expect(result.success).toBe(true);
    expect(result.transaction_id).toBe('txn_001');
    const [url, body] = http.post.mock.calls[0];
    expect(url).toContain('/internal/transactions/txn_001/score');
    expect(body).toEqual(validScore);
    expect(fs.rename).toHaveBeenCalledWith(
      '/queue/txn_001.json',
      '/queue/processed/txn_001.json'
    );
  });

  test('malformed engine output is handled (failed, no crash)', async () => {
    const fs = {
      readFile: jest.fn().mockResolvedValue(JSON.stringify(validTxn)),
      rename: jest.fn().mockResolvedValue(undefined),
      mkdir: jest.fn().mockResolvedValue(undefined),
    };
    const http = { post: jest.fn() };
    const spawn = makeSequencedSpawn([
      { stdoutData: '<<<garbage not json>>>', exitCode: 0 },
    ]);

    const result = await processFile('/queue/txn_001.json', {
      fs,
      spawn,
      http,
      backoffMs: 0,
      queueDir: '/queue',
    });

    expect(result.success).toBe(false);
    expect(result.error).toMatch(/failed to parse engine output/);
    expect(http.post).not.toHaveBeenCalled();
    expect(fs.rename).toHaveBeenCalledWith(
      '/queue/txn_001.json',
      '/queue/failed/txn_001.json'
    );
  });

  test('malformed transaction file is handled (failed, no crash)', async () => {
    const fs = {
      readFile: jest.fn().mockResolvedValue('{ not valid json'),
      rename: jest.fn().mockResolvedValue(undefined),
      mkdir: jest.fn().mockResolvedValue(undefined),
    };
    const http = { post: jest.fn() };
    const spawn = jest.fn();

    const result = await processFile('/queue/bad.json', {
      fs,
      spawn,
      http,
      backoffMs: 0,
      queueDir: '/queue',
    });

    expect(result.success).toBe(false);
    expect(spawn).not.toHaveBeenCalled();
    expect(fs.rename).toHaveBeenCalledWith(
      '/queue/bad.json',
      '/queue/failed/bad.json'
    );
  });
});

// ---------------------------------------------------------------------------
// processQueueOnce
// ---------------------------------------------------------------------------

describe('processQueueOnce', () => {
  test('returns a {processed, failed} summary across files', async () => {
    const fs = {
      readdir: jest
        .fn()
        .mockResolvedValue(['txn_001.json', 'txn_002.json', 'note.txt']),
      readFile: jest.fn().mockResolvedValue(JSON.stringify(validTxn)),
      rename: jest.fn().mockResolvedValue(undefined),
      mkdir: jest.fn().mockResolvedValue(undefined),
    };
    const http = { post: jest.fn().mockResolvedValue({ status: 200 }) };
    const spawn = makeSequencedSpawn([
      { stdoutData: JSON.stringify(validScore), exitCode: 0 },
    ]);

    const summary = await processQueueOnce({
      fs,
      spawn,
      http,
      backoffMs: 0,
      queueDir: '/queue',
    });

    // Only the two .json files are processed; note.txt is skipped.
    expect(summary).toEqual({ processed: 2, failed: 0 });
    expect(fs.readFile).toHaveBeenCalledTimes(2);
  });
});
