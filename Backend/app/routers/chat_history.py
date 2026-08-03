from collections import defaultdict

# Stores chat history per session
# { session_id: [ {"role": "user"/"assistant", "content": "..."}, ... ] }
_store: dict = defaultdict(list)

MAX_HISTORY = 10  # keep last 10 turns (5 user + 5 assistant)


def get_history(session_id: str) -> list:
    """Returns the conversation history for a session."""
    return _store[session_id]


def add_message(session_id: str, role: str, content: str):
    """Adds a single message to the session history."""
    _store[session_id].append({"role": role, "content": content})

    # Trim to last MAX_HISTORY messages to avoid huge prompts
    if len(_store[session_id]) > MAX_HISTORY:
        _store[session_id] = _store[session_id][-MAX_HISTORY:]


def clear_history(session_id: str):
    """Clears the conversation history for a session."""
    _store[session_id] = []