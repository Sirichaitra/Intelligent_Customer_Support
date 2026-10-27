conversation_history = {}


def add_message(session_id, role, message):

    if session_id not in conversation_history:
        conversation_history[session_id] = []

    conversation_history[session_id].append({
        "role": role,
        "message": message
    })


def get_history(session_id):

    return conversation_history.get(
        session_id,
        []
    )


def clear_history(session_id):

    if session_id in conversation_history:
        del conversation_history[session_id]