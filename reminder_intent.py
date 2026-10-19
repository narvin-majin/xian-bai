"""Deterministic parsing and preview staging for a small reminder grammar."""

from datetime import date, datetime, timedelta
import re

import preview_manager


_TIME = r"(?:1[0-2]|0?[1-9])(?::[0-5]\d)?\s*[ap]\.?m\.?"
_WEEKDAY = (
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday"
)
_MONTH = (
    r"january|february|march|april|may|june|july|august|september|"
    r"october|november|december"
)
_DATE = (
    rf"today|tomorrow|(?:(?:next\s+)?(?:{_WEEKDAY}))|"
    rf"(?:\d{{1,2}}\s+(?:{_MONTH})(?:\s+\d{{4}})?|"
    rf"(?:{_MONTH})\s+\d{{1,2}}(?:,?\s+\d{{4}})?)"
)
_PATTERNS = (
    re.compile(
        rf"^(?P<title>.+?)\s+at\s+(?P<time>{_TIME})\s+(?P<date>{_DATE})$",
        re.IGNORECASE,
    ),
    re.compile(
        rf"^(?P<title>.+?)\s+(?P<date>{_DATE})\s+at\s+(?P<time>{_TIME})$",
        re.IGNORECASE,
    ),
    re.compile(rf"^(?P<title>.+?)\s+(?P<date>{_DATE})$", re.IGNORECASE),
)
_WEEKDAY_PHRASE = re.compile(
    rf"^(?:(?P<next>next)\s+)?(?P<weekday>{_WEEKDAY})$", re.IGNORECASE
)
_DAY_MONTH_PHRASE = re.compile(
    rf"^(?P<day>\d{{1,2}})\s+(?P<month>{_MONTH})(?:\s+(?P<year>\d{{4}}))?$",
    re.IGNORECASE,
)
_MONTH_DAY_PHRASE = re.compile(
    rf"^(?P<month>{_MONTH})\s+(?P<day>\d{{1,2}})(?:,?\s+(?P<year>\d{{4}}))?$",
    re.IGNORECASE,
)
_NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}
_RELATIVE_DURATION = re.compile(
    r"^(?P<title>.+?)\s+in\s+(?P<amount>[+-]?\d+|[a-z]+)\s+"
    r"(?P<unit>minutes?|hours?|days?)$",
    re.IGNORECASE,
)
_RELATIVE_DURATION_HINT = re.compile(
    r"\bin\b.{0,40}\b(?:minutes?|mins?|hours?|hrs?|days?|"
    r"seconds?|secs?|weeks?|months?|years?)\b",
    re.IGNORECASE,
)
_EXPLICIT_REMINDER = re.compile(r"^(?:please\s+)?remind me to\s+", re.IGNORECASE)
_IMPERATIVE = re.compile(
    r"^(?:buy|call|pay|send|pick up|meet|email|take|book|submit|finish|clean|"
    r"water|visit|prepare|schedule|text|message|renew|cancel|order|collect|"
    r"drop off|check|feed|walk)\b",
    re.IGNORECASE,
)
_DATE_OR_TIME_HINT = re.compile(
    rf"\b(?:today|tomorrow|tonight|yesterday|next|this\s+(?:week|month|"
    rf"morning|afternoon|evening)|{_WEEKDAY}|{_MONTH}|noon|midnight|"
    r"morning|afternoon|evening|tonight)\b|\b\d{4}-\d{2}-\d{2}\b|"
    r"\bat\s+\d|\b(?:in|after)\s+\d+|\b\d{1,2}\b",
    re.IGNORECASE,
)


def _clarification():
    return {
        "status": "clarify",
        "message": (
            "I can preview reminders using supported dates or relative times. "
            "Please clarify the date or duration."
        ),
    }


def _parse_time(value):
    normalized = re.sub(r"\s+", " ", value.replace(".", "").strip()).upper()
    for time_format in ("%I:%M %p", "%I %p"):
        try:
            return datetime.strptime(normalized, time_format).time()
        except ValueError:
            pass
    return None


def _interpret_date(value, current):
    normalized = value.strip().lower()
    if normalized == "today":
        due_date = current.date()
    elif normalized == "tomorrow":
        due_date = current.date() + timedelta(days=1)
    else:
        weekday = _WEEKDAY_PHRASE.fullmatch(normalized)
        if weekday:
            target = datetime.strptime(weekday.group("weekday"), "%A").weekday()
            days_ahead = (target - current.weekday()) % 7
            if weekday.group("next") and days_ahead == 0:
                days_ahead = 7
            due_date = current.date() + timedelta(days=days_ahead)
        else:
            calendar_date = (
                _DAY_MONTH_PHRASE.fullmatch(normalized)
                or _MONTH_DAY_PHRASE.fullmatch(normalized)
            )
            if not calendar_date:
                return None

            month_number = datetime.strptime(
                calendar_date.group("month"), "%B"
            ).month
            year = int(calendar_date.group("year") or current.year)
            try:
                due_date = date(year, month_number, int(calendar_date.group("day")))
            except ValueError:
                return None

            # A yearless past date is ambiguous; do not silently roll it forward.
            if due_date < current.date():
                return None

    return due_date


def _interpret_relative_duration(match, current):
    amount_text = match.group("amount").lower()
    if amount_text in _NUMBER_WORDS:
        amount = _NUMBER_WORDS[amount_text]
    else:
        try:
            amount = int(amount_text)
        except ValueError:
            return None

    if amount <= 0:
        return None

    unit = match.group("unit").lower().rstrip("s")
    title = match.group("title").strip(" \t.,!?")
    if not title:
        return None

    try:
        if unit == "minute":
            due_at = (current + timedelta(minutes=amount)).strftime("%Y-%m-%d %H:%M")
        elif unit == "hour":
            due_at = (current + timedelta(hours=amount)).strftime("%Y-%m-%d %H:%M")
        else:
            # Whole relative days use local calendar dates, like other date-only reminders.
            due_at = (current.date() + timedelta(days=amount)).strftime("%Y-%m-%d")
    except (OverflowError, ValueError):
        return None

    return {"status": "preview", "title": title, "due_at": due_at}


def parse_reminder_request(text, now=None):
    """Return a preview/clarification result, or None for ordinary chat."""
    if not isinstance(text, str):
        return None

    cleaned = text.strip().rstrip(".!?").strip()
    if not cleaned:
        return None

    explicit = _EXPLICIT_REMINDER.match(cleaned)
    body = cleaned[explicit.end():].strip() if explicit else cleaned
    imperative = bool(_IMPERATIVE.match(body))
    if not explicit and not imperative:
        return None

    current = now or datetime.now()
    relative = _RELATIVE_DURATION.fullmatch(body)
    if relative:
        parsed_duration = _interpret_relative_duration(relative, current)
        return parsed_duration if parsed_duration is not None else _clarification()

    matched = None
    for pattern in _PATTERNS:
        matched = pattern.fullmatch(body)
        if matched:
            break

    if matched is None:
        has_date_hint = bool(
            _DATE_OR_TIME_HINT.search(body) or _RELATIVE_DURATION_HINT.search(body)
        )
        if explicit and not has_date_hint:
            title = body.strip(" \t.,!?")
            if title:
                return {"status": "preview", "title": title, "due_at": None}
        if has_date_hint:
            return _clarification()
        return None

    title = matched.group("title").strip(" \t.,!?")
    if not title:
        return _clarification()
    if re.search(r"\b(?:last|this|coming|upcoming)$", title, re.IGNORECASE):
        return _clarification()

    due_date = _interpret_date(matched.group("date"), current)
    if due_date is None:
        return _clarification()
    time_value = matched.groupdict().get("time")
    if time_value is None and re.search(r"\bat\s+\d", title, re.IGNORECASE):
        return _clarification()

    if time_value:
        due_time = _parse_time(time_value)
        if due_time is None:
            return _clarification()
        due_datetime = datetime.combine(due_date, due_time)
        if due_datetime <= current:
            return _clarification()
        due_at = due_datetime.strftime("%Y-%m-%d %H:%M")
    else:
        due_at = due_date.strftime("%Y-%m-%d")

    return {"status": "preview", "title": title, "due_at": due_at}


def handle_reminder_request(text, session_key, now=None):
    """Stage a recognized reminder draft and return its confirmation prompt."""
    parsed = parse_reminder_request(text, now=now)
    if parsed is None:
        return None
    if parsed["status"] == "clarify":
        return parsed["message"]

    preview = {
        "type": "reminder",
        "title": parsed["title"],
        "due_at": parsed["due_at"],
    }
    preview_manager.set_preview(session_key, preview)
    return (
        f"{preview_manager.format_preview(preview)}\n"
        "Reply /confirm to save or /cancel to discard."
    )
