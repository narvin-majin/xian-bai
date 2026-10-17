"""Background checks and one-time delivery for timed reminders."""

from datetime import datetime
import json
import logging
import threading

import reminder_manager


logger = logging.getLogger(__name__)


def _due_datetime(reminder):
    due_at = reminder.get("due_at")
    if not isinstance(due_at, str) or len(due_at) != 16:
        return None

    try:
        return datetime.strptime(due_at, "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def check_due_reminders(send_notification, now=None):
    """Send due timed reminders once, recording delivery before sending."""
    current_time = now or datetime.now()
    sent_count = 0

    while True:
        delivery = None
        with reminder_manager.REMINDERS_LOCK:
            try:
                data = reminder_manager.load_reminders()
            except (OSError, UnicodeError, json.JSONDecodeError):
                logger.exception("Could not load reminders for scheduler check")
                return sent_count

            for reminder in data.get("reminders", []):
                due_at = _due_datetime(reminder)
                if (
                    due_at is None
                    or due_at > current_time
                    or reminder.get("done")
                    or reminder.get("notified")
                    or reminder.get("chat_id") is None
                ):
                    continue

                # Persist each claim separately before delivery. This avoids
                # marking later reminders if the process stops during a send.
                reminder["notified"] = True
                delivery = reminder.copy()
                try:
                    reminder_manager.save_reminders(data)
                except (OSError, TypeError, ValueError):
                    logger.exception("Could not record reminder notification")
                    return sent_count
                break

        if delivery is None:
            return sent_count

        try:
            send_notification(
                delivery["chat_id"],
                f"Reminder: {delivery['title']}",
            )
            sent_count += 1
        except Exception:
            # Do not retry automatically: delivery may have reached Telegram
            # before a network error was reported.
            logger.exception(
                "Reminder notification for %r to chat %s failed; it will not "
                "be retried to avoid a duplicate",
                delivery["title"],
                delivery["chat_id"],
            )


def _run_scheduler(send_notification, interval_seconds, stop_event):
    while not stop_event.is_set():
        check_due_reminders(send_notification)
        stop_event.wait(interval_seconds)


def start_scheduler(send_notification, interval_seconds=30):
    """Start an immediate check and recurring checks on a daemon thread."""
    stop_event = threading.Event()
    thread = threading.Thread(
        target=_run_scheduler,
        args=(send_notification, interval_seconds, stop_event),
        name="reminder-scheduler",
        daemon=True,
    )
    thread.start()
    return stop_event, thread


def run_with_polling(bot, send_notification, interval_seconds=30):
    """Run bot polling with one scheduler and stop it when polling exits."""
    stop_event, thread = start_scheduler(
        send_notification, interval_seconds=interval_seconds
    )
    try:
        bot.infinity_polling()
    finally:
        stop_event.set()
        thread.join(timeout=5)
