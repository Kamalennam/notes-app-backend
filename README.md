# Notes App Backend

Small notes backend with scheduled email reminders.

Setup
1. Copy `.env.template` to `.env` and fill real values (do NOT commit `.env`).
2. Create a virtual environment and install requirements:

   python -m venv .venv; .\.venv\Scripts\Activate; pip install -r requirements.txt

Local test (simulate 22:30 reminder)
1. Set test mode so no real emails are sent:

   # PowerShell
   $env:EMAIL_TEST_MODE='1'
   python .\test_send_reminder.py

This will print a message showing a test-mode send was attempted.

Scheduler
The scheduler runs every minute and checks for notes scheduled for the current minute. In production, set `EMAIL_TEST_MODE=0` and fill SMTP credentials.

Deploy to EC2 (brief)
1. Provision an EC2 instance (Ubuntu 22.04 recommended).
2. Install Python 3.11+, clone repo, create virtualenv and install requirements.
3. Create a systemd service that runs `python main.py` (or runs via gunicorn if you prefer production-grade server).
4. Ensure `.env` is present on the instance with correct values and that outbound SMTP is allowed.
