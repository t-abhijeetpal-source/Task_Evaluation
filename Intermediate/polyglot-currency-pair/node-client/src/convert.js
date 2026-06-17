'use strict';

/**
 * Node.js CLI client for the FastAPI currency conversion service.
 *
 * Usage:  node src/convert.js <amount> <from> <to>
 * Example: node src/convert.js 100 USD INR   ->  100 USD = 8300 INR
 *
 * The logic is split into small pure-ish functions so it can be unit-tested
 * with a mocked HTTP client (see tests/convert.test.js).
 */

const axios = require('axios');

const API_URL = process.env.API_URL || 'http://localhost:8000';
const SUPPORTED = ['USD', 'INR', 'EUR'];

// Exit codes — distinct per failure class so callers/tests can assert them.
const EXIT = { OK: 0, SERVER_ERROR: 1, BAD_ARGS: 2, API_UNAVAILABLE: 3 };

/**
 * Parse and validate CLI arguments (the args after `node convert.js`).
 * @throws Error with a user-facing message on invalid input.
 */
function parseArgs(argv) {
  if (!Array.isArray(argv) || argv.length !== 3) {
    throw new Error('Usage: node convert.js <amount> <from> <to>  (e.g. 100 USD INR)');
  }
  const [amountStr, from, to] = argv;
  const amount = Number(amountStr);
  if (!Number.isFinite(amount)) {
    throw new Error(`Amount must be a number, got "${amountStr}"`);
  }
  if (amount <= 0) {
    throw new Error('Amount must be positive');
  }
  return { amount, from: String(from).toUpperCase(), to: String(to).toUpperCase() };
}

/**
 * Call the conversion API. `client` is injectable for testing.
 * @returns {Promise<object>} the response body.
 */
async function convert({ amount, from, to }, client = axios) {
  const res = await client.post(`${API_URL}/convert`, { amount, from, to });
  return res.data;
}

/** Format a successful conversion for display. */
function formatResult(amount, from, data) {
  return `${amount} ${from} = ${data.converted_amount} ${data.to}`;
}

/**
 * Orchestrate one CLI invocation. Dependencies (http client, loggers) are
 * injectable so tests can run without a real server or real stdout.
 * @returns {Promise<number>} process exit code.
 */
async function run(argv, deps = {}) {
  const client = deps.client || axios;
  const log = deps.log || console.log;
  const errOut = deps.error || console.error;

  let args;
  try {
    args = parseArgs(argv);
  } catch (e) {
    errOut(`Error: ${e.message}`);
    return EXIT.BAD_ARGS;
  }

  try {
    const data = await convert(args, client);
    log(formatResult(args.amount, args.from, data));
    return EXIT.OK;
  } catch (e) {
    if (e.response) {
      // Server responded with a non-2xx status (e.g. 400 unsupported currency).
      const msg =
        e.response.data && e.response.data.error
          ? e.response.data.error
          : `Server returned status ${e.response.status}`;
      errOut(`Error: ${msg}`);
      return EXIT.SERVER_ERROR;
    }
    if (e.request || e.code === 'ECONNREFUSED') {
      // Request was made but no response — backend unavailable.
      errOut(`Error: API unavailable at ${API_URL}. Is the FastAPI service running?`);
      return EXIT.API_UNAVAILABLE;
    }
    errOut(`Error: ${e.message}`);
    return EXIT.SERVER_ERROR;
  }
}

// CLI entry point (only when run directly, not when imported by tests).
if (require.main === module) {
  run(process.argv.slice(2)).then((code) => process.exit(code));
}

module.exports = { parseArgs, convert, formatResult, run, API_URL, SUPPORTED, EXIT };
