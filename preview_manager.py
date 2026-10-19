"""In-memory previews awaiting explicit confirmation."""

from contextlib import contextmanager
import threading


_pending_previews = {}
_session_locks = {}
_session_locks_guard = threading.Lock()


def session_key(chat_id=None):
    """Return the isolated key used by terminal or Telegram callers."""
    if chat_id is None:
        return ("terminal",)
    return ("telegram", chat_id)


def _get_session_lock(session_key):
    with _session_locks_guard:
        lock = _session_locks.get(session_key)
        if lock is None:
            lock = threading.RLock()
            _session_locks[session_key] = lock
        return lock


@contextmanager
def lock_preview(session_key):
    """Serialize preview operations for this session only."""
    with _get_session_lock(session_key):
        yield


def set_preview(session_key, preview):
    """Store a pending preview for one terminal or Telegram session."""
    with _get_session_lock(session_key):
        _pending_previews[session_key] = preview


def get_preview(session_key):
    """Return the pending preview for a session, if one exists."""
    with _get_session_lock(session_key):
        return _pending_previews.get(session_key)


def format_preview(preview):
    """Format the reminder draft supported by this milestone."""
    if not isinstance(preview, dict) or preview.get("type") != "reminder":
        return "Unsupported preview."

    title = preview.get("title")
    if not isinstance(title, str) or not title.strip():
        return "Invalid reminder preview: title is required."

    due_at = preview.get("due_at")
    if due_at is None:
        return f"Reminder preview: {title}"

    return f"Reminder preview: {title} (due: {due_at})"


def clear_preview(session_key):
    """Remove a pending preview for a session."""
    with _get_session_lock(session_key):
        return _pending_previews.pop(session_key, None)
