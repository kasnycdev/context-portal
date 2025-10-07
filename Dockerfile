FROM node:20-slim

# Set the working directory in the container
WORKDIR /app

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    libffi-dev \
    libssl-dev \
    sqlite3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a symlink for python3 to python (for compatibility)
RUN ln -s /usr/bin/python3 /usr/bin/python

# Create a non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy package files for Node.js caching
COPY package*.json ./
RUN npm ci --only=production

# Copy Python requirements and install dependencies
COPY requirements.txt pyproject.toml uv.lock ./
RUN pip3 install --no-cache-dir --break-system-packages setuptools wheel \
    && pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy the full application (both Node.js and Python code)
COPY src/ ./src/
COPY server.js ./
COPY .dockerignore LICENSE* README.md SECURITY.md ./

# Install the Python package
RUN pip3 install --no-cache-dir --break-system-packages .

# Create directory for logs and data, set proper ownership
RUN mkdir -p /data/logs \
    && chown -R appuser:appuser /app /data

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/health', (res) => { process.exit(res.statusCode === 200 ? 0 : 1) }).on('error', () => process.exit(1))"

# Command to run the MCP SSE transport server
CMD ["node", "server.js"]
