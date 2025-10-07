import http from 'http';
import https from 'https';

class HTTPClientTransport {
  constructor(url) {
    this.url = url;
  }

  async start() {
    // Nothing to start for HTTP transport
  }

  async send(message) {
    return new Promise((resolve, reject) => {
      const parsedUrl = new URL(this.url);

      const requestOptions = {
        hostname: parsedUrl.hostname,
        port: parsedUrl.port,
        path: parsedUrl.pathname,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      };

      const requestModule = parsedUrl.protocol === 'https:' ? https : http;
      const req = requestModule.request(requestOptions, (res) => {
        let data = '';
        res.on('data', (chunk) => {
          data += chunk;
        });

        res.on('end', () => {
          try {
            const response = JSON.parse(data);
            resolve(response);
          } catch (err) {
            reject(new Error(`Failed to parse response: ${err.message}`));
          }
        });
      });

      req.on('error', (err) => {
        reject(err);
      });

      req.write(JSON.stringify(message));
      req.end();
    });
  }

  async close() {
    // Nothing to close for HTTP transport
  }
}

export { HTTPClientTransport };
