const http = require('http');

const PORT = process.env.PORT || 3000;

const routes = {
  '/api/health': (req, res) => {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'UP',
      uptime: process.uptime(),
      timestamp: new Date().toISOString(),
      service: 'COMP231 ScribeFlow Core API'
    }));
  },
  '/api/stories': (req, res) => {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      iteration: 1,
      totalPoints: 120,
      completedPoints: 35,
      remainingPoints: 98,
      status: 'In Progress'
    }));
  }
};

const server = http.createServer((req, res) => {
  const handler = routes[req.url];
  if (handler) {
    handler(req, res);
  } else {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Endpoint not found' }));
  }
});

if (require.main === module) {
  server.listen(PORT, () => {
    console.log(`COMP231 Server running on http://localhost:${PORT}`);
  });
}

module.exports = { server, routes };
