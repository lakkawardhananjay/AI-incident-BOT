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
        while time.time() - start < 60:  # keep CPU busy for 20 seconds
            _ = [x ** 2 for x in range(10000)]
        CPU_LOAD.set(0.0)  # reset after load

    thread = threading.Thread(target=burn_cpu)
    thread.start()

    return "Started CPU load for 60 seconds!"

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
