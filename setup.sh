#!/bin/bash

set -e

PROM_VERSION="2.52.0"
ALERTMANAGER_VERSION="0.27.0"
SERVER_DIR=~/monitoring/server
VENV_DIR="$SERVER_DIR/venv"
TMUX_SESSION="flask-server"

echo "🔧 Updating system packages..."
sudo apt update -y && sudo apt upgrade -y

echo "🐍 Installing python3.12-venv..."
sudo apt install -y python3.12-venv tmux curl

# Setup monitoring directory
mkdir -p ~/monitoring
cd ~/monitoring

echo "📦 Downloading Prometheus v$PROM_VERSION..."
curl -LO https://github.com/prometheus/prometheus/releases/download/v${PROM_VERSION}/prometheus-${PROM_VERSION}.linux-amd64.tar.gz
tar -xzf prometheus-${PROM_VERSION}.linux-amd64.tar.gz
mv prometheus-${PROM_VERSION}.linux-amd64 prometheus
rm prometheus-${PROM_VERSION}.linux-amd64.tar.gz
echo "✅ Prometheus ready."

echo "📦 Downloading Alertmanager v$ALERTMANAGER_VERSION..."
curl -LO https://github.com/prometheus/alertmanager/releases/download/v${ALERTMANAGER_VERSION}/alertmanager-${ALERTMANAGER_VERSION}.linux-amd64.tar.gz
tar -xzf alertmanager-${ALERTMANAGER_VERSION}.linux-amd64.tar.gz
mv alertmanager-${ALERTMANAGER_VERSION}.linux-amd64 alertmanager
rm alertmanager-${ALERTMANAGER_VERSION}.linux-amd64.tar.gz
echo "✅ Alertmanager ready."

echo "🗂 Creating Flask app directory and files..."
mkdir -p "$SERVER_DIR"
cd "$SERVER_DIR"

# 1. Write app.py
cat > app.py <<EOF
from flask import Flask
import time
import threading
from prometheus_client import Counter, generate_latest, Gauge, CONTENT_TYPE_LATEST

app = Flask(__name__)

REQUEST_COUNT = Counter("request_count", "Total number of requests", ['endpoint'])
CPU_LOAD = Gauge("cpu_load_simulation", "Simulated CPU Load")

@app.route("/")
def hello():
    REQUEST_COUNT.labels(endpoint="/").inc()
    return "Hello from the monitoring app!"

@app.route("/cpu")
def cpu_intensive():
    REQUEST_COUNT.labels(endpoint="/cpu").inc()
    CPU_LOAD.set(1.0)  # simulate high CPU load

    def burn_cpu():
        start = time.time()
        while time.time() - start < 20:  # keep CPU busy for 20 seconds
            _ = [x ** 2 for x in range(10000)]
        CPU_LOAD.set(0.0)  # reset after load

    thread = threading.Thread(target=burn_cpu)
    thread.start()

    return "Started CPU load for 20 seconds!"

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
EOF

# 2. Write requirements.txt
cat > requirements.txt <<EOF
flask==2.0.1
prometheus-client==0.11.0
EOF

# 3. Create venv
echo "🐍 Creating virtual environment..."
python3.12 -m venv "$VENV_DIR"

# 4. Start tmux and run app
echo "🖥 Launching Flask app in tmux session: $TMUX_SESSION"
tmux new-session -d -s "$TMUX_SESSION" bash

# Send commands to tmux
tmux send-keys -t "$TMUX_SESSION" "cd $SERVER_DIR" C-m
tmux send-keys -t "$TMUX_SESSION" "source $VENV_DIR/bin/activate" C-m
tmux send-keys -t "$TMUX_SESSION" "pip install -r requirements.txt" C-m
tmux send-keys -t "$TMUX_SESSION" "python3 app.py" C-m

echo "✅ Flask app is running in tmux session: $TMUX_SESSION"
echo "🌐 App is available at http://localhost:5000"
echo "📊 Metrics at http://localhost:5000/metrics"

# 5. Detach
tmux detach -s "$TMUX_SESSION"
echo "🛠 Detached from tmux. Use 'tmux attach -t $TMUX_SESSION' to re-enter."


