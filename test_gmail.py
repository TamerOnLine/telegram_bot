from apps.gmail.gmail_client import get_last_emails

if __name__ == "__main__":
    emails = get_last_emails(limit=5)
    for e in emails:
        print("From:", e["from"])
        print("Subject:", e["subject"])
        print("Date:", e["date"])
        print("Snippet:", e["snippet"])
        print("Link:", e["link"])
        print("-" * 40)
