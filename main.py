import os
import feedparser
import time
import requests
import logging
from datetime import datetime, timedelta, timezone
from dateutil import tz

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




def main():
    logger.info("Starting GitHub status monitor...")
    seen_titles = set()
    while True:
        d = feedparser.parse('https://www.githubstatus.com/history.atom')
        logger.debug(f"Fetched feed with {len(d.entries)} entries")

        ## ignore anything that is older than one day 
        for entry in d.entries:
            if entry.title not in seen_titles:
                if is_one_day_old(entry.updated) == True: 
                    seen_titles.add(entry.title)
                    send_message(entry.title, entry.updated, entry.link)
        time.sleep(60)  # Check every 60 seconds

if __name__ == "__main__":
    main()
