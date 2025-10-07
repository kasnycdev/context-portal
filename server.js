const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const { spawn } = require('child_process');
const { Readable, Writable } = require('stream');
require('dotenv').config();

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { SSEServerTransport } = require('@modelcontextprotocol/sdk/server/sse.js');
const { StdioClientTransport } = require('@modelcontextprotocol/sdk/client/stdio.js');
const { Client } = require('@modelcontextprotocol/sdk/client/index.js');

// Dynamic import for the request schemas from the SDK (ES module)
let schemas = null;

class ContextPortalMCPServer {
  constructor() {
    this.app = express();
    this.mcpClient = null;
    this.pythonProcess = null;
    this.workspaceDir = process.env.WORKSPACE_DIR || '/app/data';

    this.setupMiddleware();
    this.setupRoutes();
  }

  async initializePythonBackend() {
    console.log('🐍 Starting Python context-portal backend...');

    // Use python command (assumed to be available in activated venv)
    const pythonPath = 'python';

    // Start the Python FastMCP server in HTTP mode
    const pythonPort = process.env.PYTHON_MCP_PORT || 8001;
    const pythonCommand = pythonPath;
    const pythonArgs = ['-m', 'src.context_portal_mcp.main', '--mode', 'http', '--port', pythonPort.toString(), '--workspace_id', this.workspaceDir];

    const pythonProcess = spawn(pythonCommand, pythonArgs, {
      cwd: this.workspaceDir,
      env: {
        ...process.env,
        PYTHONUNBUFFERED: '1'
      },
      stdio: ['pipe', 'pipe', 'pipe']
    });

    this.pythonProcess = pythonProcess;

    pythonProcess.stderr.on('data', (data) => {
      console.error(`[Python stderr]: ${data.toString()}`);
    });

    pythonProcess.on('error', (error) => {
      console.error('Failed to start Python process:', error);
    });

    pythonProcess.on('exit', (code, signal) => {
      console.log(`Python process exited with code ${code} and signal ${signal}`);
    });

    // Wait a bit for the server to start
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Connect to the Python backend via HTTP
    const { HTTPClientTransport } = await import('./http-transport.js');
    const transport = new HTTPClientTransport(`http://localhost:${pythonPort}/mcp`);

    this.mcpClient = new Client(
      {
        name: 'context-portal-sse-bridge',
        version: '1.0.0',
      },
      {
        capabilities: {}
      }
    );

    await this.mcpClient.connect(transport);
    console.log('✅ Connected to Python context-portal backend');

    return this.mcpClient;
  }

  setupMiddleware() {
    // Security middleware
    this.app.use(helmet({
      contentSecurityPolicy: false, // Disable CSP for SSE
      crossOriginEmbedderPolicy: false
    }));
    
    // CORS configuration for SSE
    this.app.use(cors({
      origin: true,
      credentials: true,
      methods: ['GET', 'POST', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization', 'Cache-Control', 'Accept']
    }));
    
    // Logging
    this.app.use(morgan('combined'));
    
    // JSON parsing
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true }));
  }

  setupRoutes() {
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        server: 'context-portal-mcp-sse-bridge',
        version: '1.0.0',
        backend: 'python-context-portal',
        pythonProcessRunning: this.pythonProcess !== null && this.pythonProcess.exitCode === null
      });
    });

    this.app.get('/', (req, res) => {
      res.json({
        message: 'Context Portal MCP SSE Server',
        version: '1.0.0',
        description: 'SSE transport bridge to Python context-portal backend',
        repository: 'https://github.com/kasnycdev/context-portal',
        endpoints: {
          health: '/health',
          sse: '/sse'
        }
      });
    });

    this.app.get('/sse', async (req, res) => {
      console.log('📡 SSE connection requested from:', req.ip);

      if (!this.mcpClient) {
        try {
          await this.initializePythonBackend();
        } catch (error) {
          console.error('Failed to initialize Python backend:', error);
          res.status(500).json({ error: 'Failed to connect to context-portal backend' });
          return;
        }
      }

      res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Cache-Control, Content-Type'
      });

      const server = new Server(
        {
          name: 'context-portal-server',
          version: '1.0.0',
        },
        {
          capabilities: {
            resources: {},
            tools: {},
            prompts: {},
          },
        }
      );

      await this.setupMCPProxyHandlers(server);

      const transport = new SSEServerTransport('/sse', res);
      await server.connect(transport);

      console.log('✅ SSE client connected, bridge established');

      req.on('close', () => {
        console.log('❌ SSE client disconnected');
        transport.close();
      });

      req.on('error', (err) => {
        console.error('SSE connection error:', err);
        transport.close();
      });
    });
  }

  async setupMCPProxyHandlers(server) {
    // Set up request handlers for different MCP methods
    server.setRequestHandler('resources/list', async (request) => {
      try {
        const result = await this.mcpClient.request({ method: 'resources/list' }, request.params);
        return result;
      } catch (error) {
        console.error('Error proxying resources/list:', error);
        return { resources: [] };
      }
    });

    server.setRequestHandler('resources/read', async (request) => {
      try {
        const result = await this.mcpClient.request({ method: 'resources/read' }, request.params);
        return result;
      } catch (error) {
        console.error('Error proxying resources/read:', error);
        throw error;
      }
    });

    server.setRequestHandler('tools/list', async (request) => {
      try {
        const result = await this.mcpClient.request({ method: 'tools/list' }, request.params);
        return result;
      } catch (error) {
        console.error('Error proxying tools/list:', error);
        return { tools: [] };
      }
    });

    server.setRequestHandler('tools/call', async (request) => {
      try {
        const result = await this.mcpClient.request({ method: 'tools/call' }, request.params);
        return result;
      } catch (error) {
        console.error('Error proxying tools/call:', error);
        throw error;
      }
    });

    server.setRequestHandler('prompts/list', async (request) => {
      try {
        const result = await this.mcpClient.request({ method: 'prompts/list' }, request.params);
        return result;
      } catch (error) {
        console.error('Error proxying prompts/list:', error);
        return { prompts: [] };
      }
    });

    server.setRequestHandler('prompts/get', async (request) => {
      try {
        const result = await this.mcpClient.request({ method: 'prompts/get' }, request.params);
        return result;
      } catch (error) {
        console.error('Error proxying prompts/get:', error);
        throw error;
      }
    });
  }

  start(port = 3000, host = '0.0.0.0') {
    this.app.listen(port, host, () => {
      console.log('='.repeat(60));
      console.log(`🚀 Context Portal MCP SSE Bridge Server`);
      console.log('='.repeat(60));
      console.log(`📍 Server running on: http://${host}:${port}`);
      console.log(`📡 SSE endpoint: http://${host}:${port}/sse`);
      console.log(`🏥 Health check: http://${host}:${port}/health`);
      console.log(`🐍 Backend: Python context-portal (kasnycdev/context-portal)`);
      console.log(`📦 Workspace: ${this.workspaceDir}`);
      console.log('='.repeat(60));
    });
  }

  cleanup() {
    if (this.pythonProcess) {
      console.log('🛑 Terminating Python backend process...');
      this.pythonProcess.kill();
    }
    if (this.mcpClient) {
      console.log('🔌 Closing MCP client connection...');
      this.mcpClient.close();
    }
  }
}

const port = process.env.PORT || 3000;
const host = process.env.HOST || '0.0.0.0';

const server = new ContextPortalMCPServer();
server.start(port, host);

process.on('SIGTERM', () => {
  console.log('\n⚠️  Received SIGTERM, shutting down gracefully...');
  server.cleanup();
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('\n⚠️  Received SIGINT, shutting down gracefully...');
  server.cleanup();
  process.exit(0);
});
