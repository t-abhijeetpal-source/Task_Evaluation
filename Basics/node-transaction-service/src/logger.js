'use strict';

/**
 * Structured JSON logging — one machine-parseable object per line.
 * Any aggregator (CloudWatch, Loki, ELK) can ingest this without a grok stage.
 */
function emit(level, msg, fields = {}) {
  const line = JSON.stringify({
    ts: new Date().toISOString(),
    level,
    msg,
    ...fields,
  });
  // stderr for warn/error, stdout otherwise — standard 12-factor stream split.
  if (level === 'error' || level === 'warn') process.stderr.write(`${line}\n`);
  else process.stdout.write(`${line}\n`);
}

module.exports = {
  info: (msg, fields) => emit('info', msg, fields),
  warn: (msg, fields) => emit('warn', msg, fields),
  error: (msg, fields) => emit('error', msg, fields),
};
