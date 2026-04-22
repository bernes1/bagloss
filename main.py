import os
import feedparser
import time
import requests
import logging
import json
from datetime import datetime, timedelta, timezone
from dateutil import tz
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Outputs to stdout/stderr for Docker
    ]
)
logger = logging.getLogger(__name__)

token = os.getenv("PUSHOVER_TOKEN")
userkey = os.getenv("PUSHOVER_USER_KEY")
user_tz = os.getenv("USER_TZ")

EVENT_LOG_FILE = "/data/incident_log.json"
RETENTION_HOURS = 24

def send_message(event_title:str,updated_time:str,link:str) -> str:
    to_zone = tz.gettz(user_tz)
    time = datetime.fromisoformat(updated_time).astimezone(to_zone).strftime("%H:%M:%S | %d-%m-%Y ")
    event_message = f"New Github Incident: {event_title}\nDate: {time}\nLink: {link}"
    logger.info(event_message)

    r = requests.post("https://api.pushover.net/1/messages.json", data = {
        "token": token,
        "user": userkey,
        "message": event_message,
        "title":"Github Incident",
        "sound":"cashregister"
    },headers={"Content-type": "application/x-www-form-urlencoded"})

    return r.text



def is_one_day_old(timestamp: str):
    # checks if is less than one day old
    input_time = datetime.fromisoformat(timestamp)
    current_time = datetime.now(timezone.utc)
    time_diff = current_time - input_time
    return time_diff <= timedelta(days=1)


def load_and_prune_incident_log():
    """Load incident log and remove entries older than RETENTION_HOURS"""
    if not Path(EVENT_LOG_FILE).exists():
        return {}

    with open(EVENT_LOG_FILE, 'r') as f:
        log = json.load(f)

    # Remove entries older than RETENTION_HOURS
    now = datetime.now(timezone.utc)
    pruned_log = {}

    for title, data in log.items():
        logged_at = datetime.fromisoformat(data["logged_at"])
        if (now - logged_at) <= timedelta(hours=RETENTION_HOURS):
            pruned_log[title] = data

    # Save pruned log back
    save_incident_log(pruned_log)
    return pruned_log


def save_incident_log(log):
    """Save the incident log to file"""
    Path(EVENT_LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(EVENT_LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2)


def log_incident(event_title, updated_time, link, incident_log):
    """Log incident and mark that we've sent a notification"""
    incident_log[event_title] = {
        "timestamp": updated_time,
        "link": link,
        "logged_at": datetime.now(timezone.utc).isoformat()
    }
    save_incident_log(incident_log)




def main():
    logger.info("Starting GitHub status monitor...")
    incident_log = load_and_prune_incident_log()
    last_prune_time = datetime.now(timezone.utc)

    while True:
        d = feedparser.parse('https://www.githubstatus.com/history.atom')
        logger.debug(f"Fetched feed with {len(d.entries)} entries")

        ## ignore anything that is older than one day
        for entry in d.entries:
            if entry.title not in incident_log:
                if is_one_day_old(entry.updated) == True:
                    send_message(entry.title, entry.updated, entry.link)
                    log_incident(entry.title, entry.updated, entry.link, incident_log)

        # Prune log every 24 hours
        now = datetime.now(timezone.utc)
        if (now - last_prune_time) >= timedelta(hours=24):
            incident_log = load_and_prune_incident_log()
            last_prune_time = now
            logger.info("Pruned incident log")

        time.sleep(60)  # Check every 60 seconds

if __name__ == "__main__":
    main()
