import multiprocessing

# Gunicorn configuration file

# Worker timeout in seconds (default is 30)
# Increased to 300s (5 minutes) for PDF generation with WeasyPrint
timeout = 300

# Graceful timeout - time to wait for workers to finish after receiving SIGTERM
graceful_timeout = 30

# Number of worker processes
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class
worker_class = 'sync'

# Maximum requests a worker will process before restarting
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Keep alive connections
keepalive = 5