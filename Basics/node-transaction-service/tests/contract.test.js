'use strict';

const fs = require('fs');
const path = require('path');
const request = require('supertest');
const createApp = require('../src/app');
const { InMemoryStorage } = require('../src/storage/inMemoryStorage');

const VECTORS = JSON.parse(
  fs.readFileSync(path.join(__dirname, '../../fixtures/transaction-vectors.json'), 'utf8')
);

function buildApp() {
  return createApp({ storage: new InMemoryStorage() });
}

function expandBody(raw) {
  const body = { ...raw };
  if (body.description === 'REPEAT_X_501') {
    body.description = 'x'.repeat(501);
  }
  return body;
}

async function runSteps(app, steps) {
  for (const step of steps) {
    const method = step.method.toLowerCase();
    const headers = step.headers || {};
    let req = request(app)[method](step.path).set(headers);

    if (step.body) {
      req = req.send(expandBody(step.body));
    }

    const res = await req;
    expect(res.status).toBe(step.expectStatus);

    if (step.expectBody) {
      expect(res.body).toEqual(step.expectBody);
    }
    if (step.expectLength !== undefined) {
      expect(res.body).toHaveLength(step.expectLength);
    }
    if (step.expectFirst) {
      expect(res.body[0]).toMatchObject(step.expectFirst);
    }
    if (step.expectSecond) {
      expect(res.body[1]).toMatchObject(step.expectSecond);
    }
    if (step.expectBodyKeys) {
      for (const key of step.expectBodyKeys) {
        expect(res.body).toHaveProperty(key);
      }
    }
    if (step.expectHeader) {
      for (const [key, value] of Object.entries(step.expectHeader)) {
        expect(res.headers[key.toLowerCase()]).toBe(value);
      }
    }
  }
}

describe('B4/B5 shared contract vectors', () => {
  test.each(VECTORS.scenarios)('$name', async (scenario) => {
    const app = buildApp();
    await runSteps(app, scenario.steps);
  });

  test.each(VECTORS.validationFailures)('validation: $name', async (caseDef) => {
    const app = buildApp();
    const res = await request(app)
      .post('/transactions')
      .send(expandBody(caseDef.body));
    expect(res.status).toBe(caseDef.expectStatus);
  });

  test.each(VECTORS.observability)('observability: $name', async (caseDef) => {
    const app = buildApp();
    const headers = caseDef.headers || {};
    let req = request(app)[caseDef.method.toLowerCase()](caseDef.path).set(headers);
    const res = await req;
    expect(res.status).toBe(caseDef.expectStatus);

    if (caseDef.expectBodyKeys) {
      for (const key of caseDef.expectBodyKeys) {
        expect(res.body).toHaveProperty(key);
      }
    }
    if (caseDef.expectHeader) {
      for (const [key, value] of Object.entries(caseDef.expectHeader)) {
        expect(res.headers[key.toLowerCase()]).toBe(value);
      }
    }
  });
});
