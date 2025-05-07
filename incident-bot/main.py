from fastapi import FastAPI, Request
import json
import logging
import os
from dotenv import load_dotenv
import uvicorn
from datetime import datetime
import requests
import subprocess
import google.generativeai as genai
import re
import boto3
from botocore.exceptions import ClientError
import io
import threading
import time

# Load environment variables from .env file
load_dotenv()

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

# Initialize Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# If no API key is set, provide a warning
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY environment variable not set. AI suggestions will be disabled.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

# Initialize Slack webhook (optional)
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")

# Configure self-healing settings
SELF_HEALING_ENABLED = os.getenv("SELF_HEALING_ENABLED", "false").lower() == "true"
SELF_HEALING_CONFIDENCE_THRESHOLD = float(os.getenv("SELF_HEALING_CONFIDENCE_THRESHOLD", "0.8"))

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_LOG_PREFIX = os.getenv("S3_LOG_PREFIX", "incident-bot-logs/")
S3_UPLOAD_INTERVAL = int(os.getenv("S3_UPLOAD_INTERVAL", "300"))  # Default: 5 minutes

# Initialize S3 client if credentials are available
s3_client = None
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and S3_BUCKET_NAME:
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        logger.info(f"S3 client initialized. Logs will be uploaded to s3://{S3_BUCKET_NAME}/{S3_LOG_PREFIX}")
    except Exception as e:
        logger.error(f"Failed to initialize S3 client: {str(e)}")
        s3_client = None
else:
    logger.warning("S3 credentials not provided. Log uploads to S3 will be disabled.")

app = FastAPI(title="AI-Powered Incident Bot")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online", 
        "message": "AI-Powered Incident Bot is running",
        "ai_enabled": bool(GEMINI_API_KEY),
        "self_healing_enabled": SELF_HEALING_ENABLED
    }

def get_ai_suggestion(alert_info):
    """Get an AI-powered suggestion for the alert using Gemini"""
    try:
        if not GEMINI_API_KEY:
            return "AI suggestions disabled. Set GEMINI_API_KEY environment variable.", 0.0
        
        # Create a prompt with detailed information about the alert
        prompt = f"""
        You are an AI-powered DevOps engineer. You've received the following alert:
        
        {json.dumps(alert_info, indent=2)}
        
        Based on this alert, please suggest:
        1. What might be causing this issue
        2. Steps to remediate the problem
        3. How to prevent this in the future
        
        Keep your suggestion concise and actionable. If you can suggest specific commands, please do so.
        Start your response with a confidence score between 0 and 1 on a separate line (e.g. "CONFIDENCE: 0.8"),
        indicating how confident you are in your suggestion.
        """
        
        # Call Gemini API
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        response = model.generate_content(prompt)
        
        suggestion = response.text
        
        # Extract confidence score
        confidence_match = re.search(r"CONFIDENCE:\s*(0\.\d+)", suggestion)
        confidence = float(confidence_match.group(1)) if confidence_match else 0.0
        
        # Remove the confidence line from the suggestion
        if confidence_match:
            suggestion = re.sub(r"CONFIDENCE:\s*0\.\d+\n", "", suggestion, 1)
        
        return suggestion, confidence
        
    except Exception as e:
        logger.error(f"Error getting AI suggestion: {str(e)}", exc_info=True)
        return f"Error generating AI suggestion: {str(e)}", 0.0

def send_to_slack(message):
    """Send a message to Slack"""
    if not SLACK_WEBHOOK:
        logger.warning("Slack webhook not configured. Skipping notification.")
        return
    
    try:
        # Format message for Slack
        slack_payload = {
            "text": message,
            "mrkdwn": True
        }
        
        response = requests.post(
            SLACK_WEBHOOK,
            json=slack_payload
        )
        response.raise_for_status()
        logger.info("Successfully sent message to Slack")
    except Exception as e:
        logger.error(f"Error sending to Slack: {str(e)}", exc_info=True)

def upload_file_to_s3(file_path, s3_key=None):
    """Upload a file to S3 bucket"""
    if not s3_client or not S3_BUCKET_NAME:
        logger.warning("S3 client not configured. Skipping upload.")
        return False
    
    try:
        # If s3_key is not provided, use the filename as the key
        if not s3_key:
            s3_key = os.path.join(S3_LOG_PREFIX, os.path.basename(file_path))
        
        # Upload the file
        s3_client.upload_file(file_path, S3_BUCKET_NAME, s3_key)
        logger.info(f"Successfully uploaded {file_path} to s3://{S3_BUCKET_NAME}/{s3_key}")
        return True
    except ClientError as e:
        logger.error(f"Error uploading file to S3: {str(e)}")
        return False

def upload_data_to_s3(data, s3_key):
    """Upload data directly to S3 bucket"""
    if not s3_client or not S3_BUCKET_NAME:
        logger.warning("S3 client not configured. Skipping upload.")
        return False
    
    try:
        # Convert data to bytes if it's a string
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # Create a file-like object
        file_obj = io.BytesIO(data)
        
        # Upload the data
        s3_client.upload_fileobj(file_obj, S3_BUCKET_NAME, s3_key)
        logger.info(f"Successfully uploaded data to s3://{S3_BUCKET_NAME}/{s3_key}")
        return True
    except ClientError as e:
        logger.error(f"Error uploading data to S3: {str(e)}")
        return False

def upload_logs_periodically():
    """Upload log files to S3 at regular intervals"""
    while True:
        try:
            # Upload the main log file
            log_file = "incident_bot.log"
            if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                s3_key = f"{S3_LOG_PREFIX}logs/{timestamp}-{log_file}"
                upload_file_to_s3(log_file, s3_key)
            
            # Upload the alerts and healing actions files
            for filename in ["alerts_processed.jsonl", "healing_actions.jsonl"]:
                if os.path.exists(filename) and os.path.getsize(filename) > 0:
                    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                    s3_key = f"{S3_LOG_PREFIX}data/{timestamp}-{filename}"
                    upload_file_to_s3(filename, s3_key)
                    
        except Exception as e:
            logger.error(f"Error in periodic log upload: {str(e)}")
        
        # Sleep until the next upload interval
        time.sleep(S3_UPLOAD_INTERVAL)

def attempt_self_healing(alert_info, suggestion, confidence):
    """Attempt to automatically remediate the issue based on the AI suggestion"""
    if not SELF_HEALING_ENABLED:
        return "Self-healing disabled", False
    
    if confidence < SELF_HEALING_CONFIDENCE_THRESHOLD:
        return f"Confidence too low for self-healing: {confidence} < {SELF_HEALING_CONFIDENCE_THRESHOLD}", False
    
    # Extract alert name and severity
    alert_name = alert_info.get("labels", {}).get("alertname", "unknown")
    
    # Apply remediation based on alert type
    healing_result = "No healing action taken"
    success = False
    
    try:
        # Handle high CPU usage
        if alert_name == "HighCPUUsage" or alert_name == "HighSimulatedCPULoad":
            # Simple example: for demo purposes, we'll just log that we would scale
            logger.info("⚠️ SELF-HEALING: Would automatically scale the service")
            
            # In a real system, you might use kubectl, AWS CLI, or other tools:
            # subprocess.run(["kubectl", "scale", "deployment", "my-app", "--replicas=5"])
            
            healing_result = "Simulated scaling the service to handle high CPU load"
            success = True
            
        # Handle high memory usage
        elif alert_name == "HighMemoryUsage":
            logger.info("⚠️ SELF-HEALING: Would restart the memory-intensive service")
            
            # In a real system:
            # subprocess.run(["kubectl", "rollout", "restart", "deployment/memory-intensive-app"])
            
            healing_result = "Simulated restarting memory-intensive service"
            success = True
            
        # Handle disk space issues
        elif alert_name == "LowDiskSpace":
            logger.info("⚠️ SELF-HEALING: Would clean up temp files")
            
            # In a real system:
            # subprocess.run(["ssh", "server", "find /tmp -type f -atime +7 -delete"])
            
            healing_result = "Simulated cleaning up temporary files to free disk space"
            success = True
            
        # Log the healing action
        with open("healing_actions.jsonl", "a") as f:
            action_record = {
                "timestamp": datetime.now().isoformat(),
                "alert": alert_info,
                "confidence": confidence,
                "action": healing_result,
                "success": success
            }
            f.write(json.dumps(action_record) + "\n")
            
        return healing_result, success
        
    except Exception as e:
        logger.error(f"Error during self-healing: {str(e)}", exc_info=True)
        return f"Self-healing error: {str(e)}", False

@app.post("/alert")
async def receive_alert(request: Request):
    """Main endpoint for receiving alerts from Alertmanager"""
    try:
        # Get the alert data
        data = await request.json()
        logger.info(f"Received alert webhook: {json.dumps(data, indent=2)}")
        
        # Extract key information
        alerts = data.get("alerts", [])
        response_data = {"processed_alerts": []}
        
        # Process each alert
        for i, alert in enumerate(alerts):
            alert_info = {
                "status": alert.get("status", "unknown"),
                "labels": alert.get("labels", {}),
                "annotations": alert.get("annotations", {})
            }
            
            # Get AI-powered suggestion
            suggestion, confidence = get_ai_suggestion(alert_info)
            
            # Attempt self-healing if appropriate
            healing_result, healing_success = attempt_self_healing(alert_info, suggestion, confidence)
            
            # Prepare message for Slack
            alert_name = alert_info["labels"].get("alertname", "Unknown Alert")
            instance = alert_info["labels"].get("instance", "Unknown Instance")
            description = alert_info["annotations"].get("description", "No description")
            
            slack_message = f"""
:rotating_light: *ALERT: {alert_name}*
:satellite: Instance: {instance}
:bar_chart: Status: {alert_info['status']}
:memo: Description: {description}

:bulb: *AI Suggestion* (Confidence: {confidence:.2f}):
```
{suggestion}
```

:wrench: *Self-Healing*: {healing_result if SELF_HEALING_ENABLED else "Disabled"}
            """
            
            # Send to Slack if configured
            send_to_slack(slack_message)
            
            # Store alert for future reference
            alert_record = {
                "timestamp": datetime.now().isoformat(),
                "alert_info": alert_info,
                "suggestion": suggestion,
                "confidence": confidence,
                "healing_result": healing_result,
                "healing_success": healing_success
            }
            
            # Store locally and upload to S3
            with open("alerts_processed.jsonl", "a") as f:
                record_line = json.dumps(alert_record) + "\n"
                f.write(record_line)
                
            # Also upload this specific alert to S3 immediately
            if s3_client and S3_BUCKET_NAME:
                try:
                    alert_timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                    alert_id = alert_info["labels"].get("alertname", "unknown").lower()
                    s3_key = f"{S3_LOG_PREFIX}alerts/{alert_timestamp}-{alert_id}.json"
                    upload_data_to_s3(json.dumps(alert_record, indent=2), s3_key)
                except Exception as e:
                    logger.error(f"Error uploading alert record to S3: {str(e)}")
                
            # Add to response
            response_data["processed_alerts"].append({
                "alert_name": alert_name,
                "suggestion_summary": suggestion.split("\n")[0] if suggestion else "",
                "confidence": confidence,
                "self_healing": {"action": healing_result, "success": healing_success}
            })
        
        return {
            "status": "success", 
            "message": f"Processed {len(alerts)} alerts with AI suggestions", 
            "timestamp": datetime.now().isoformat(),
            "data": response_data
        }
        
    except Exception as e:
        logger.error(f"Error processing alert: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

def validate_environment():
    """Validate that all required environment variables are set"""
    required_vars = ["GEMINI_API_KEY", "SLACK_WEBHOOK"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set them in your .env file or environment")
        return False
    
    # Check for S3 configuration - these are optional but should be checked as a group
    s3_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "S3_BUCKET_NAME"]
    missing_s3_vars = [var for var in s3_vars if not os.getenv(var)]
    
    if missing_s3_vars and len(missing_s3_vars) < len(s3_vars):
        logger.warning(f"Incomplete S3 configuration. Missing: {', '.join(missing_s3_vars)}")
        logger.warning("S3 log uploads will be disabled.")
    
    return len(missing_vars) == 0

if __name__ == "__main__":
    if not validate_environment():
        # Exit with error code
        import sys
        sys.exit(1)
    
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    logger.info(f"Starting AI-Powered Incident Bot on {host}:{port}")
    logger.info(f"AI Suggestions: {'Enabled' if GEMINI_API_KEY else 'Disabled'}")
    logger.info(f"Self-Healing: {'Enabled' if SELF_HEALING_ENABLED else 'Disabled'}")
    logger.info(f"S3 Log Uploads: {'Enabled' if s3_client else 'Disabled'}")
    
    # Start the S3 upload thread if S3 is configured
    if s3_client:
        upload_thread = threading.Thread(target=upload_logs_periodically, daemon=True)
        upload_thread.start()
        logger.info(f"Started S3 upload thread. Logs will be uploaded every {S3_UPLOAD_INTERVAL} seconds.")
    
    uvicorn.run(app, host=host, port=port)
