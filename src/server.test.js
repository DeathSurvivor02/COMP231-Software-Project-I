const test = require('node:test');
const assert = require('node:assert');
const { routes } = require('./server.js');

test('GET /api/health returns status UP and valid timestamp', () => {
  let responseData = '';
  const mockReq = { url: '/api/health' };
  const mockRes = {
    writeHead: (code, headers) => {
      assert.strictEqual(code, 200);
      assert.strictEqual(headers['Content-Type'], 'application/json');
    },
    end: (body) => {
      responseData = JSON.parse(body);
    }
  };

  routes['/api/health'](mockReq, mockRes);
  assert.strictEqual(responseData.status, 'UP');
  assert.ok(responseData.timestamp);
});

test('GET /api/stories returns iteration progress data', () => {
  let responseData = '';
  const mockReq = { url: '/api/stories' };
  const mockRes = {
    writeHead: (code, headers) => {
      assert.strictEqual(code, 200);
    },
    end: (body) => {
      responseData = JSON.parse(body);
    }
  };

  routes['/api/stories'](mockReq, mockRes);
  assert.strictEqual(responseData.iteration, 1);
  assert.strictEqual(responseData.totalPoints, 120);
  assert.strictEqual(responseData.completedPoints, 35);
  assert.strictEqual(responseData.remainingPoints, 98);
});
