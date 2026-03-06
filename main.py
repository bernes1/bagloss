import os
import feedparser
import time
import requests
from datetime import datetime, timedelta, timezone

token = os.getenv("PUSHOVER_TOKEN")
userkey = os.getenv("PUSHOVER_USER_KEY")


def send_message(event_title,updated_time):
    time = datetime.fromisoformat(updated_time).strftime("%H:%M:%S %d-%m-%Y ")
    event_message = f"New event: {event_title, time}"
    print(event_message)

    r = requests.post("https://api.pushover.net/1/messages.json", data = {
        "token": token,
        "user": userkey,
        "message": event_message
    },headers={"Content-type": "application/x-www-form-urlencoded"})

    return r.text



def is_one_day_old(timestamp: str):
    # checks if is less than one day old
    input_time = datetime.fromisoformat(timestamp)
    current_time = datetime.now(timezone.utc)
    time_diff = current_time - input_time
    return time_diff <= timedelta(days=1)




def main():
    seen_titles = set()
    while True:
        d = feedparser.parse('https://www.githubstatus.com/history.atom')

        ## ignore anything that is older than one day 
        for entry in d.entries:
            if entry.title not in seen_titles:
                if is_one_day_old(entry.updated) == True: 
                    seen_titles.add(entry.title)
                    send_message(entry.title, entry.updated)
        time.sleep(60)  # Check every 60 seconds

if __name__ == "__main__":
    main()
