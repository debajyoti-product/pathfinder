import json
import os
from datetime import datetime

USAGE_FILE = "backend/api_usage.json"
ALERTS_FILE = r"C:\Users\Debajyoti\.gemini\antigravity\brain\cfff6e2c-7edd-46ba-92de-cb79a33a9c23\alerts.md"

# Approximate Daily Limits (Free Tiers)
LIMITS = {
    "serper": 1000,
    "hunter": 25,
    "groq": 1000  # Groq is more complex but we'll use a count for simplicity
}

def log_usage(service, count=1):
    now = datetime.now().strftime("%Y-%m-%d")
    
    usage_data = {}
    if os.path.exists(USAGE_FILE):
        with open(USAGE_FILE, "r") as f:
            try:
                usage_data = json.load(f)
            except:
                usage_data = {}
    
    if now not in usage_data:
        usage_data[now] = {"serper": 0, "hunter": 0, "groq": 0}
    
    usage_data[now][service] += count
    
    with open(USAGE_FILE, "w") as f:
        json.dump(usage_data, f, indent=2)
    
    check_limits(now, usage_data[now])

def check_limits(date, current_usage):
    alerts = []
    for service, limit in LIMITS.items():
        used = current_usage.get(service, 0)
        percentage = (used / limit) * 100
        
        if percentage >= 60:
            alerts.append(f"> [!WARNING]\n> **{service.upper()}** usage: {used}/{limit} ({percentage:.1f}%). Limit alert triggered!")
    
    if alerts:
        update_alerts_file(date, alerts)

def update_alerts_file(date, alerts):
    content = f"# API Usage Alerts - {date}\n\n"
    content += "\n\n".join(alerts)
    content += "\n\n---\n*Last updated: " + datetime.now().strftime("%H:%M:%S") + "*"
    
    with open(ALERTS_FILE, "w") as f:
        f.write(content)

def is_over_limit(service):
    now = datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists(USAGE_FILE):
        return False
        
    with open(USAGE_FILE, "r") as f:
        usage_data = json.load(f)
        
    if now not in usage_data:
        return False
        
    used = usage_data[now].get(service, 0)
    limit = LIMITS.get(service, 1000)
    return (used / limit) >= 0.6
