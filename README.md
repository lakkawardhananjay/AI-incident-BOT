# 🤖 AI-Driven Incident Management & Self-Healing System

An intelligent, containerized system designed to monitor, detect, respond, and self-heal infrastructure issues in real time — with incident alerts, AI-powered remediation suggestions, and logs archived to AWS S3.

## 🚀 Project Overview

This project automates end-to-end incident management for modern DevOps environments using:

- **Prometheus** for metric collection and alerting
- **Alertmanager** for routing alerts
- **Slack Integration** for real-time incident notifications with remediation suggestions
- **Self-Healing Scripts** for automated issue resolution
- **OpenTofu (Terraform alternative)** for infrastructure provisioning
- **Docker Compose** for service orchestration
- **AWS S3** for logging and archiving incident history
- **Shell Scripts** for environment bootstrap

---

## 🧠 Key Features

| Feature | Description |
|--------|-------------|
| 🔍 Monitoring | Continuous resource monitoring using Prometheus |
| 🚨 Alerting | Threshold-based alerts pushed to Slack |
| 💬 AI Suggestions | Slack messages include AI-generated incident fixes |
| 🔁 Self-Healing | Auto-restart crashed services or scale infra via scripts |
| 🪵 Log Upload | Incident logs archived to Amazon S3 |
| 🧱 Infra-as-Code | OpenTofu for declarative and reproducible setup |
| 🐳 Orchestration | All services containerized via Docker Compose |

---

## 📸 Architecture Diagram

```txt
  +-----------+         +---------------+         +-------------+
  | Prometheus| ----->  | Alertmanager  | ----->  |   Slack Bot |
  +-----------+         +---------------+         +-------------+
        |                     |                         |
        v                     v                         |
  [ Target Metrics ]     [ Webhook Trigger ]            |
        |                     |                         |
        v                     v                         |
  +----------------+   +------------------+             |
  | Self-Healing   |<--| AI Suggestion API|             |
  | Scripts        |   +------------------+             |
  +----------------+                                   |
        |                                              |
        v                                              v
  +-------------------+                         +----------------+
  | Incident Logs     | ---> (Archive) -------> |  AWS S3 Bucket |
  +-------------------+                         +----------------+
```
## ⚙️ Tech Stack
Infrastructure: OpenTofu, AWS (S3)

Monitoring: Prometheus

Alerting: Alertmanager

Notification: Slack Webhooks

Automation: Bash scripting

Containerization: Docker, Docker Compose

AI Suggestion Engine: GPT or custom LLM logic (optional)

Logging: S3 Upload with incident ID + timestamp

## 📦 Project Structure
```
ai-incident-manager/
├── docker-compose.yml
├── alertmanager/
│   └── alertmanager.yml
├── prometheus/
│   └── prometheus.yml
├── scripts/
│   ├── self_heal.sh
│   ├── upload_to_s3.sh
│   └── setup.sh
├── infra/
│   └── main.tftpl (OpenTofu templates)
├── logs/
├── slack-bot/
│   └── app.py
└── README.md
```
## 🛠️ Setup Instructions
Clone the Repository
bash
```
git clone https://github.com/lakkawardhananjay/AI-incident-BOT.git
cd AI-incident-BOT
```
## Configure Environment Variables
Update infra/variables.tf and .env file with your AWS credentials, Slack webhook, and S3 bucket details.

## Provision Infrastructure

bash
```
cd infra
tofu init
tofu apply
```
## Run Services

bash
```
docker-compose up --build

```
Simulate an Incident
Trigger a CPU spike or kill a service to see the alert, Slack notification, AI suggestion, and healing in action.

## 📈 Sample Slack Alert

<br>🚨 ALERT: HighSimulatedCPULoad</br>
<br>🌐 Instance: localhost:5000</br>
<br>📊 Status: resolved</br>
<br>📝 Description: The Flask application is reporting high CPU load simulation.</br>

## 🧪 Future Improvements

Here are some potential enhancements to take this system to the next level:

- 🔔 **Integrate with PagerDuty or OpsGenie**  
  Enable automated on-call alerting and escalation workflows.

- 📊 **Add a Grafana Dashboard**  
  Visualize real-time metrics and alert statuses using an intuitive UI.

- 🧠 **Train a Custom AI Model**  
  Tailor suggestions based on your infrastructure and historical incidents for more accurate and context-aware remediation.

- 🔐 **Implement RBAC and Audit Logs**  
  Secure self-healing actions with role-based access control and maintain logs for accountability and compliance.


🙌 Credits
  <br>Created by lakkawardhananjay </br>
  <br>Maintained with ❤️ for DevOps automation and resilience</br>

📄 License
MIT License

  Copyright (c) [2025] [Dhananjay lakkawar]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE, AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT, OR OTHERWISE, ARISING FROM,
OUT OF, OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
