#!/bin/bash

set -e

# Step 1: Create the directory
echo "📁 Creating incident-bot directory..."
mkdir -p ~/incident-bot
cd ~/incident-bot

# Step 2: Write main.py
echo "📝 Writing main.py..."
cat > main.py <<'EOF'
from fastapi import FastAPI, Request
import json
import logging
import os
import uvicorn
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("incident_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("incident_bot")

app = FastAPI(title="Incident Bot")

@app.get("/")
async def root():
    return {"status": "online", "message": "Incident Bot is running"}

@app.post("/alert")
async def receive_alert(request: Request):
    try:
        data = await request.json()
        logger.info(f"Received alert webhook: {json.dumps(data, indent=2)}")
        alerts = data.get("alerts", [])

        for i, alert in enumerate(alerts):
            status = alert.get("status", "unknown")
            labels = alert.get("labels", {})
            annotations = alert.get("annotations", {})
            logger.info(f"Processing alert {i+1}/{len(alerts)}:")
            logger.info(f"  Status: {status}")
            logger.info(f"  Labels: {labels}")
            logger.info(f"  Annotations: {annotations}")

            alert_record = {
                "timestamp": datetime.now().isoformat(),
                "status": status,
                "labels": labels,
                "annotations": annotations
            }

            with open("alerts_received.jsonl", "a") as f:
                f.write(json.dumps(alert_record) + "\n")

        return {
            "status": "success",
            "message": f"Processed {len(alerts)} alerts",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error processing alert: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

@app.post("/alert/critical")
async def receive_critical_alert(request: Request):
    try:
        data = await request.json()
        logger.info(f"Received CRITICAL alert webhook: {json.dumps(data, indent=2)}")
        return {
            "status": "success",
            "message": "Processed critical alert",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing critical alert: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

@app.post("/alert/flask")
async def receive_flask_alert(request: Request):
    try:
        data = await request.json()
        logger.info(f"Received Flask app alert webhook: {json.dumps(data, indent=2)}")
        return {
            "status": "success",
            "message": "Processed Flask application alert",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing Flask app alert: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    logger.info(f"Starting Incident Bot on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
EOF

# Step 3: Create requirements.txt
echo "📦 Creating requirements.txt..."
cat > requirements.txt <<EOF
fastapi==0.75.0
uvicorn==0.17.6
python-multipart==0.0.5
EOF

# Step 4: Create a virtual environment
echo "🐍 Creating virtual environment..."
python3 -m venv venv

# Step 5: Activate venv and install dependencies
echo "📦 Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Step 6: Run the app
echo "🚀 Starting Incident Bot with Uvicorn..."
uvicorn main:app --host 0.0.0.0 --port 8000

