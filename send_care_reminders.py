"""
Daily dispatcher for CareEvent reminders — the home-assistant trigger engine.
Meant to run on a schedule (Render Cron Job), once per day. Zero AI calls in
this script: just a plain query on dueDate/sent, an email send, and a
reschedule if the event is recurring. All AI reasoning already happened
when the CareEvent row was created (see generate_care_events() in utils.py).

Usage:
    python send_care_reminders.py           # sends for real
    python send_care_reminders.py --dry-run # logs what would be sent, no email/db writes
"""

import sys
from datetime import date, timedelta, datetime

from dotenv import load_dotenv
load_dotenv()

from app import app, db
from models import CareEvent
from utils import send_care_event_email


def main(dry_run=False):
    with app.app_context():
        today = date.today()
        due = CareEvent.query.filter(CareEvent.dueDate <= today, CareEvent.sent == False).all()
        print(f"{len(due)} care event(s) due as of {today.isoformat()}{' [DRY RUN]' if dry_run else ''}")

        for event in due:
            report = event.report
            recipient = None
            if report:
                if report.user_id and report.user:
                    recipient = report.user.email
                recipient = recipient or report.customerEmail

            if not recipient:
                print(f"  Skipping {event.appliance} (report {event.reportId}): no recipient email on file")
                continue

            if dry_run:
                print(f"  Would send to {recipient}: [{event.appliance}] {event.message[:80]}...")
                continue

            try:
                send_care_event_email(recipient, event.appliance, event.message)
                event.sent = True
                event.sentAt = datetime.utcnow()

                if event.recurringIntervalDays:
                    next_event = CareEvent(
                        reportId=event.reportId,
                        appliance=event.appliance,
                        eventType=event.eventType,
                        dueDate=today + timedelta(days=event.recurringIntervalDays),
                        recurringIntervalDays=event.recurringIntervalDays,
                        message=event.message,
                        sent=False,
                    )
                    db.session.add(next_event)
                    print(f"  Sent + rescheduled {event.appliance} for {next_event.dueDate.isoformat()}")
                else:
                    print(f"  Sent {event.appliance} (one-time)")
            except Exception as e:
                print(f"  Failed to send {event.appliance}: {e}")

        if not dry_run:
            db.session.commit()


if __name__ == '__main__':
    main(dry_run='--dry-run' in sys.argv)
