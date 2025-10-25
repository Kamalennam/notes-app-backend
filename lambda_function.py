import os
import smtplib
import datetime
from email.message import EmailMessage
from pymongo import MongoClient


def get_collection():
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI not found in environment variables.")
    db_name = os.getenv("MONGO_DB", "notes")
    coll_name = os.getenv("MONGO_COLLECTION", "notes")
    client = MongoClient(mongo_uri)
    return client[db_name][coll_name]



def send_email(subject, body, scheduled_time=None):
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")  
    smtp_pass = os.getenv("SMTP_PASS")  
    mail_from = os.getenv("MAIL_FROM", smtp_user)
    mail_to = os.getenv("MAIL_TO", smtp_user)

    if not (smtp_user and smtp_pass):
        print("❌ Missing SMTP credentials. Check environment variables.")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = mail_to

    # Append schedule info
    if scheduled_time:
        body = f"Scheduled: {scheduled_time}\n\n{body}"

    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as s:
            s.starttls()
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)
        print(f"✅ Email sent successfully → {mail_to}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False



def send_todays_summary():
    now = datetime.datetime.now(datetime.timezone.utc)
    start = datetime.datetime(now.year, now.month, now.day, tzinfo=datetime.timezone.utc)
    end = start + datetime.timedelta(days=1)

    print("=" * 60)
    print(f"📅 Checking reminders between {start} and {end}")
    print("=" * 60)

    try:
        coll = get_collection()
        query = {"schedule_date": {"$gte": start, "$lt": end}}
        notes = list(coll.find(query))
        print(f"Found {len(notes)} note(s) scheduled for today.")
    except Exception as e:
        print(f"❌ MongoDB query failed: {e}")
        return False

    if not notes:
        print("No scheduled notes for today.")
        return True

    # Compose summary
    lines = ["Here are your scheduled tasks for today:\n"]
    for i, note in enumerate(notes, 1):
        sd = note.get("schedule_date")
        if isinstance(sd, datetime.datetime):
            sd_str = sd.astimezone(datetime.timezone.utc).isoformat()
        else:
            sd_str = str(sd)
        lines.append(f"{i}. {note.get('title', 'Untitled')}\n   {note.get('content', '')}\n   Scheduled: {sd_str}\n")

    subject = f"📚 Today's Reminders ({len(notes)} task{'s' if len(notes) > 1 else ''})"
    body = "\n".join(lines)

    return send_email(subject, body, now)



def lambda_handler(event, context):
    print("🚀 Lambda Triggered:", datetime.datetime.now())
    ok = send_todays_summary()
    return {"statusCode": 200, "body": f"Reminders sent: {ok}"}
