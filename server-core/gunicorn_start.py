#!/usr/bin/env python3
"""
F.A.R.O. Server Core - Gunicorn Production Startup Script
Best practices for FastAPI production deployment with Gunicorn + Uvicorn workers

Usage:
    python gunicorn_start.py
    or
    gunicorn -c gunicorn_start.py app.main:app
"""

import multiprocessing
import os
from app.core.config import settings

# =============================================================================
# WORKER CONFIGURATION
# =============================================================================
# Number of worker processes
# For async workers: set equal to number of CPU cores
# Formula: min(32, (2 * CPU_cores) + 1) is for sync workers
# For async (Uvicorn): use CPU_cores directly
workers = settings.workers if isinstance(settings.workers, int) else multiprocessing.cpu_count()

# Worker class: UvicornWorker for FastAPI async
worker_class = settings.gunicorn_worker_class

# Maximum concurrent requests per worker
# Adjust based on expected load and memory
worker_connections = settings.gunicorn_worker_connections

# Maximum number of requests a worker will process before restarting
# Prevents memory leaks from accumulating
max_requests = settings.gunicorn_max_requests

# Random jitter for max_requests to prevent thundering herd
# Workers restart at random times between max_requests and max_requests + jitter
max_requests_jitter = settings.gunicorn_max_requests_jitter

# =============================================================================
# TIMEOUT SETTINGS
# =============================================================================
# Timeout for silent workers (seconds)
# Workers that don't respond within this time are killed and restarted
timeout = settings.gunicorn_timeout

# Graceful timeout for worker restart (seconds)
# Workers have this much time to finish processing requests before being killed
graceful_timeout = settings.gunicorn_graceful_timeout

# Keepalive timeout (seconds)
# How long to keep idle connections open
keepalive = 2

# =============================================================================
# PROCESS MANAGEMENT
# =============================================================================
# Preload application before forking workers
# Reduces memory usage through copy-on-write optimization
preload_app = settings.gunicorn_preload

# Worker process naming
# Useful for monitoring and debugging
proc_name = "faro-server"

# =============================================================================
# LOGGING
# =============================================================================
# Access log format with response time for performance monitoring
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Error log
errorlog = "-"

# Access log (use "-" for stdout)
accesslog = "-"

# Log level
loglevel = settings.log_level.lower()

# =============================================================================
# SERVER CONFIGURATION
# =============================================================================
# Bind address
bind = f"{settings.host}:{settings.port}"

# Worker temp directory
worker_tmp_dir = "/dev/shm"

# =============================================================================
# SECURITY
# =============================================================================
# Limit request line size
limit_request_line = 4096

# Limit request header fields
limit_request_fields = 100

# Limit request header field size
limit_request_field_size = 8190

# =============================================================================
# SSL/TLS (if configured)
# =============================================================================
# Uncomment and configure if using SSL
# keyfile = "/path/to/ssl/key.pem"
# certfile = "/path/to/ssl/cert.pem"
# ssl_version = 3
# cert_reqs = 0
# ca_certs = "/path/to/ca.pem"

# =============================================================================
# ENVIRONMENT
# =============================================================================
# Ensure environment variables are loaded
if not os.environ.get("DATABASE_URL"):
    # Load from .env if not already set
    from dotenv import load_dotenv
    load_dotenv()

# =============================================================================
# DAEMON MODE (optional)
# =============================================================================
# Set to True to run as daemon (background process)
# For containerized deployments (Docker), keep False
daemon = False

# PID file (if daemon mode is enabled)
# pidfile = "/var/run/faro-server.pid"

# =============================================================================
# RAW CONFIG (for reference)
# =============================================================================
# This script can be used directly with Gunicorn:
# gunicorn -c gunicorn_start.py app.main:app
#
# Or imported and used programmatically
