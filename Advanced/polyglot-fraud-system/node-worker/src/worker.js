'use strict';

/**
 * A3 — Fraud Processing Worker (Node.js)
 *
 * Reads transaction files from QUEUE_DIR, scores each one by spawning the
 * Rust fraud-engine (txn JSON on stdin -> score JSON on stdout), posts the
 * score back to FastAPI, and moves the queue file to processed/ or failed/.
 *
 * Built to /A3/CONTRACT.md (v1.0). All side-effecting collaborators
 * (spawn, http, fs) are injectable via a `deps` object so the unit tests in
 * tests/worker.test.js can run without a real engine binary or HTTP server.
 */

const fsDefault = require('fs');
const pathDefault = require('path');
const { spawn: spawnDefault } = require('child_process');
const axiosDefault = require('axios');

// ---------------------------------------------------------------------------
// Configuration (env with contract defaults)
// ---------------------------------------------------------------------------

const config = {
  API_URL: process.env.API_URL || 'http://localhost:8000',
  QUEUE_DIR: process.env.QUEUE_DIR || './queue',
  ENGINE_BIN:
    process.env.ENGINE_BIN || '../rust-engine/target/release/fraud-engine',
  INTERNAL_TOKEN: process.env.A3_INTERNAL_TOKEN || null,
  MAX_ATTEMPTS: 3,
  BACKOFF_MS: 100,
  POLL_INTERVAL_MS: 2000,
};

// ---------------------------------------------------------------------------
// Structured JSON logging
// ---------------------------------------------------------------------------

/**
 * Emit a single structured JSON log line.
 * @param {string} level   - info | warn | error
 * @param {string} msg     - short message
 * @param {object} [fields] - extra fields (transaction_id, attempt, ...)
 */
function log(level, msg, fields = {}) {
  const entry = {
    ts: new Date().toISOString(),
    level,
    msg,
    ...fields,
  };
  // stdout for info, stderr for warn/error
  const line = JSON.stringify(entry);
  if (level === 'error' || level === 'warn') {
    process.stderr.write(line + '\n');
  } else {
    process.stdout.write(line + '\n');
  }
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// ---------------------------------------------------------------------------
// callEngine — spawn the Rust engine, feed txn JSON on stdin, parse stdout
// ---------------------------------------------------------------------------

/**
 * Spawn ENGINE_BIN, write `txnJsonString` to its stdin, collect stdout, and
 * resolve the parsed score-result JSON. Rejects on non-zero exit, spawn
 * error, or unparseable stdout.
 *
 * @param {string} txnJsonString - a single transaction as a JSON string
 * @param {object} [deps]
 * @param {Function} [deps.spawn]     - child_process.spawn replacement
 * @param {string}   [deps.engineBin] - path to the engine binary
 * @returns {Promise<object>} parsed ScoreResult
 */
function callEngine(txnJsonString, deps = {}) {
  const spawn = deps.spawn || spawnDefault;
  const engineBin = deps.engineBin || config.ENGINE_BIN;

  return new Promise((resolve, reject) => {
    let child;
    try {
      child = spawn(engineBin, [], { stdio: ['pipe', 'pipe', 'pipe'] });
    } catch (err) {
      reject(new Error(`failed to spawn engine: ${err.message}`));
      return;
    }

    let stdout = '';
    let stderr = '';
    let settled = false;

    const fail = (err) => {
      if (settled) return;
      settled = true;
      reject(err);
    };

    if (child.stdout) {
      child.stdout.on('data', (d) => {
        stdout += d.toString();
      });
    }
    if (child.stderr) {
      child.stderr.on('data', (d) => {
        stderr += d.toString();
      });
    }

    child.on('error', (err) => {
      fail(new Error(`engine spawn error: ${err.message}`));
    });

    child.on('close', (code) => {
      if (settled) return;
      if (code !== 0) {
        fail(
          new Error(
            `engine exited with code ${code}: ${stderr.trim() || '(no stderr)'}`
          )
        );
        return;
      }
      let parsed;
      try {
        parsed = JSON.parse(stdout);
      } catch (err) {
        fail(
          new Error(
            `failed to parse engine output as JSON: ${err.message}; ` +
              `raw=${JSON.stringify(stdout)}`
          )
        );
        return;
      }
      settled = true;
      resolve(parsed);
    });

    // Feed the transaction on stdin.
    try {
      if (child.stdin) {
        child.stdin.write(txnJsonString);
        child.stdin.end();
      }
    } catch (err) {
      fail(new Error(`failed to write to engine stdin: ${err.message}`));
    }
  });
}

// ---------------------------------------------------------------------------
// postScore — POST the score result back to FastAPI
// ---------------------------------------------------------------------------

/**
 * POST a score result to FastAPI's internal scoring endpoint.
 *
 * @param {object} scoreResult - ScoreResult JSON (must include transaction_id)
 * @param {object} [deps]
 * @param {object} [deps.http]   - axios-like client (must expose .post)
 * @param {string} [deps.apiUrl] - base API URL
 * @returns {Promise<object>} the http response
 */
function postScore(scoreResult, deps = {}) {
  const http = deps.http || axiosDefault;
  const apiUrl = deps.apiUrl || config.API_URL;

  if (!scoreResult || !scoreResult.transaction_id) {
    return Promise.reject(
      new Error('postScore: scoreResult missing transaction_id')
    );
  }

  const id = scoreResult.transaction_id;
  const url = `${apiUrl}/internal/transactions/${id}/score`;
  const headers = { 'Content-Type': 'application/json' };
  const token = deps.internalToken != null ? deps.internalToken : config.INTERNAL_TOKEN;
  if (token) {
    headers['X-Internal-Token'] = token;
  }
  return http.post(url, scoreResult, { headers });
}

// ---------------------------------------------------------------------------
// processFile — read + score + post + move
// ---------------------------------------------------------------------------

/**
 * Process a single queue file end to end:
 *   read+parse -> callEngine (retry up to MAX_ATTEMPTS w/ backoff) -> postScore
 *   -> move to processed/ on success, failed/ after exhausting retries.
 *
 * @param {string} filePath - absolute or relative path to the queue file
 * @param {object} [deps]    - injectable collaborators (see callEngine/postScore)
 * @param {object} [deps.fs]   - fs replacement (promises-style or sync subset)
 * @param {object} [deps.path] - path replacement
 * @returns {Promise<{success: boolean, transaction_id: ?string, error?: string}>}
 */
async function processFile(filePath, deps = {}) {
  const fs = deps.fs || fsDefault.promises;
  const path = deps.path || pathDefault;
  const queueDir = deps.queueDir || config.QUEUE_DIR;
  const maxAttempts = deps.maxAttempts || config.MAX_ATTEMPTS;
  const backoffMs = deps.backoffMs != null ? deps.backoffMs : config.BACKOFF_MS;
  const wait = deps.sleep || sleep;

  const fileName = path.basename(filePath);
  let txnJsonString;
  let txn;
  let transactionId = null;

  // 1) Read + parse the transaction file.
  try {
    txnJsonString = await fs.readFile(filePath, 'utf8');
    txn = JSON.parse(txnJsonString);
    transactionId = txn.transaction_id || null;
  } catch (err) {
    log('error', 'failed to read/parse queue file', {
      transaction_id: transactionId,
      file: fileName,
      error: err.message,
    });
    await moveFile(filePath, queueDir, 'failed', { fs, path });
    return { success: false, transaction_id: transactionId, error: err.message };
  }

  // 2) callEngine with retry + backoff.
  let scoreResult = null;
  let lastError = null;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      log('info', 'scoring transaction', {
        transaction_id: transactionId,
        attempt,
      });
      scoreResult = await callEngine(txnJsonString, deps);
      lastError = null;
      break;
    } catch (err) {
      lastError = err;
      log('warn', 'engine call failed', {
        transaction_id: transactionId,
        attempt,
        error: err.message,
      });
      if (attempt < maxAttempts) {
        await wait(backoffMs * attempt); // simple linear backoff
      }
    }
  }

  if (lastError || !scoreResult) {
    log('error', 'engine call exhausted retries', {
      transaction_id: transactionId,
      attempt: maxAttempts,
      error: lastError ? lastError.message : 'no score produced',
    });
    await moveFile(filePath, queueDir, 'failed', { fs, path });
    return {
      success: false,
      transaction_id: transactionId,
      error: lastError ? lastError.message : 'no score produced',
    };
  }

  // 3) postScore.
  try {
    await postScore(scoreResult, deps);
    log('info', 'score posted', {
      transaction_id: transactionId,
      attempt: maxAttempts,
    });
  } catch (err) {
    log('error', 'failed to post score', {
      transaction_id: transactionId,
      error: err.message,
    });
    await moveFile(filePath, queueDir, 'failed', { fs, path });
    return { success: false, transaction_id: transactionId, error: err.message };
  }

  // 4) Success -> move to processed/.
  await moveFile(filePath, queueDir, 'processed', { fs, path });
  log('info', 'transaction processed', { transaction_id: transactionId });
  return { success: true, transaction_id: transactionId, score: scoreResult };
}

/**
 * Move a file into a subdirectory of the queue dir (processed/ or failed/),
 * creating the destination directory if needed. Failures here are logged but
 * never thrown — they must not crash the worker loop.
 */
async function moveFile(filePath, queueDir, subdir, { fs, path }) {
  try {
    const destDir = path.join(queueDir, subdir);
    if (fs.mkdir) {
      await fs.mkdir(destDir, { recursive: true });
    }
    const dest = path.join(destDir, path.basename(filePath));
    await fs.rename(filePath, dest);
  } catch (err) {
    log('warn', 'failed to move queue file', {
      file: path.basename(filePath),
      to: subdir,
      error: err.message,
    });
  }
}

// ---------------------------------------------------------------------------
// processQueueOnce — process every *.json currently in the queue
// ---------------------------------------------------------------------------

/**
 * List QUEUE_DIR/*.json and process each file.
 *
 * @param {object} [deps]
 * @returns {Promise<{processed: number, failed: number}>}
 */
async function processQueueOnce(deps = {}) {
  const fs = deps.fs || fsDefault.promises;
  const path = deps.path || pathDefault;
  const queueDir = deps.queueDir || config.QUEUE_DIR;

  let entries;
  try {
    entries = await fs.readdir(queueDir);
  } catch (err) {
    log('error', 'failed to read queue dir', {
      dir: queueDir,
      error: err.message,
    });
    return { processed: 0, failed: 0 };
  }

  const files = entries
    .filter((name) => name.endsWith('.json'))
    .map((name) => path.join(queueDir, name));

  let processed = 0;
  let failed = 0;

  for (const file of files) {
    const result = await processFile(file, deps);
    if (result.success) {
      processed += 1;
    } else {
      failed += 1;
    }
  }

  log('info', 'queue pass complete', { processed, failed });
  return { processed, failed };
}

// ---------------------------------------------------------------------------
// run — CLI entry: --once processes once and exits, else poll loop
// ---------------------------------------------------------------------------

/**
 * Main run loop.
 * @param {string[]} [argv] - process args (defaults to process.argv)
 * @param {object}   [deps]
 */
async function run(argv = process.argv, deps = {}) {
  const once = argv.includes('--once');
  const pollInterval = deps.pollIntervalMs || config.POLL_INTERVAL_MS;

  if (once) {
    log('info', 'worker starting (once mode)', { queue_dir: config.QUEUE_DIR });
    const summary = await processQueueOnce(deps);
    log('info', 'worker finished (once mode)', summary);
    return summary;
  }

  log('info', 'worker starting (loop mode)', {
    queue_dir: config.QUEUE_DIR,
    poll_interval_ms: pollInterval,
  });

  // Poll forever. Each pass is awaited so passes never overlap.
  // eslint-disable-next-line no-constant-condition
  while (true) {
    try {
      await processQueueOnce(deps);
    } catch (err) {
      log('error', 'unexpected error in queue pass', { error: err.message });
    }
    await sleep(pollInterval);
  }
}

// ---------------------------------------------------------------------------
// Exports + CLI guard
// ---------------------------------------------------------------------------

module.exports = {
  config,
  log,
  callEngine,
  postScore,
  processFile,
  processQueueOnce,
  moveFile,
  run,
};

if (require.main === module) {
  run().catch((err) => {
    log('error', 'worker crashed', { error: err.message });
    process.exit(1);
  });
}
