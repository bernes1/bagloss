import feedparser

def send_message():
    pass

def feed():
    d = feedparser.parse('https://www.githubstatus.com/history.atom')
    
    github_events = []

    # iterate over parsed entries to collect titles
    for entry in d.entries:
        github_events.append(f"{entry.title} at {entry.updated}")

    return github_events

def main():
    for i in feed():
        print(i)


if __name__ == "__main__":
    main()
