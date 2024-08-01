import psycopg2
from psycopg2 import sql
from datetime import datetime, timedelta

def connect_db():
    return psycopg2.connect(
        dbname="pvpower",
        user="phuongpd",
        password="vdkvn22.05",
        host="db",
        port="5432"
    )

def user_exists(conn, user_id):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
    exists = cur.fetchone() is not None
    if exists:
        # get bot_id from user_id
        cur.execute("SELECT bot_id FROM users WHERE user_id = %s", (user_id,))
        bot_id = cur.fetchone()
        return exists, bot_id        
    cur.close()
    return exists, None


def insert_user(conn, user_id, name, bot_id):
    if user_exists(conn, user_id):
        print(f"User {user_id} already exists.")
        return
    cur = conn.cursor()
    insert_user_query = """
    INSERT INTO users (user_id, name, bot_id)
    VALUES (%s, %s, %s)
    """
    cur.execute(insert_user_query, (user_id, name, bot_id))
    conn.commit()
    cur.close()
    print(f"User {user_id} inserted successfully.")

def session(conn, user_id, session_id, start_time, end_time):
    if not user_exists(conn, user_id):
        print(f"User {user_id} does not exist.")
        return
    cur = conn.cursor()
    created_at = updated_at = datetime.now()
    insert_session_query = """
    INSERT INTO sessions (user_id, session_id, start_time, end_time, created_at, updated_at)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    cur.execute(insert_session_query, (user_id, session_id, start_time, end_time, created_at, updated_at))
    conn.commit()
    cur.close()
    print(f"Session {session_id} inserted successfully.")

def session_exists(conn, user_id, session_id):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM sessions WHERE user_id = %s AND session_id = %s", (user_id, session_id))
    exists = cur.fetchone() is not None
    cur.close()
    return exists

def session_valid(conn, user_id, session_id):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM sessions WHERE user_id = %s AND session_id = %s AND end_time > NOW()", (user_id, session_id))
    exists = cur.fetchone() is not None
    cur.close()
    return exists


def conversation(conn, message_id, session_id, user_id, llm_type, inputs, token_input, outputs, token_output, total_token, timestamp, conversation_id, domain):
    if not session_exists(conn, user_id, session_id):
        print(f"Session {session_id} does not exist.")
        return
    cur = conn.cursor()
    print("all variables:", message_id, session_id, user_id, llm_type, inputs, token_input, outputs, token_output, total_token, timestamp, conversation_id, domain)
    insert_conversation_query = """
    INSERT INTO conversation_logs (message_id, session_id, user_id, llm_type, inputs, token_input, outputs, token_output, total_token, timestamp, conversation_id, domain)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cur.execute(insert_conversation_query, (message_id, session_id, user_id, llm_type, inputs, token_input, outputs, token_output, total_token, timestamp, conversation_id, domain))
    print("Pass!")
    conn.commit()
    cur.close()
    print(f"Message {message_id} inserted successfully.")


def get_conversation(conn, user_id, session_id):
    if not session_exists(conn, user_id, session_id):
        print(f"Session {session_id} does not exist.")
        return
    cur = conn.cursor()
    cur.execute("SELECT message_id FROM conversation_logs WHERE session_id = %s", (session_id,))
    message_id = cur.fetchall()
    cur.close()
    return message_id

# update end_time in sessions table = NOW() + 30 minutes
def end_session(conn, user_id, session_id):
    if not session_exists(conn, user_id, session_id):
        print(f"Session {session_id} does not exist.")
        return
    cur = conn.cursor()
    cur.execute("UPDATE sessions SET end_time = NOW() + INTERVAL '30 minutes' WHERE user_id = %s AND session_id = %s", (user_id, session_id))
    conn.commit()
    cur.close()
    print(f"Session {session_id} ended successfully.")

def get_message_lastest_timestamp(conn, user_id, session_id):
    if not session_exists(conn, user_id, session_id):
        print(f"Session {session_id} does not exist.")
        return
    cur = conn.cursor()
    cur.execute("SELECT timestamp FROM conversation_logs WHERE session_id = %s ORDER BY timestamp DESC LIMIT 1", (session_id,))
    timestamp = cur.fetchone()
    cur.close()
    return timestamp

def get_transcripts(conn, user_id, session_id):
    if not session_exists(conn, user_id, session_id):
        print(f"Session {session_id} does not exist.")
        return
    cur = conn.cursor()
    cur.execute("SELECT transcripts FROM transcripts WHERE session_id = %s and user_id = %s", (session_id, user_id))
    transcripts = cur.fetchall()
    cur.close()
    return transcripts

def add_conversation(conn, conversation_id, session_id, user_id):
    if not session_exists(conn, user_id, session_id):
        print(f"Session {session_id} does not exist.")
        return
    cur = conn.cursor()
    insert_conversation_query = """
    INSERT INTO conversations (conversation_id, session_id, user_id)
    VALUES (%s, %s, %s)
    """
    cur.execute(insert_conversation_query, (conversation_id, session_id, user_id))
    conn.commit()
    cur.close()
    print(f"Conversation {conversation_id} inserted successfully.")

def get_conversation_id(conn, user_id, session_id):
    if not session_exists(conn, user_id, session_id):
        print(f"Session {session_id} does not exist.")
        return
    cur = conn.cursor()
    cur.execute("SELECT conversation_id FROM conversations WHERE session_id = %s and user_id = %s", (session_id, user_id))
    conversation_id = cur.fetchone()
    cur.close()
    return conversation_id

def get_bot_id(conn, user_id):
    cur = conn.cursor()
    cur.execute("SELECT bot_id FROM users WHERE user_id = %s", (user_id,))
    bot_id = cur.fetchone()
    cur.close()
    return bot_id

def bot_id_exist(conn, bot_id):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE bot_id = %s", (bot_id,))
    exists = cur.fetchone() is not None
    cur.close()
    return exists

def write_feedback(conn, user_id, session_id, message_id, feedback_type, feedback_text):
    if not session_exists(conn, user_id, session_id):
        print(f"Session {session_id} does not exist.")
        return
    cur = conn.cursor()
    insert_feedback_query = """
    INSERT INTO feedback (user_id, session_id, message_id, feedback_type, feedback_text)
    VALUES (%s, %s, %s, %s, %s)
    """
    cur.execute(insert_feedback_query, (user_id, session_id, message_id, feedback_type, feedback_text))
    conn.commit()
    cur.close()
    print(f"Feedback {message_id} inserted successfully.")

def upload_pending_FAQ(conn, question, answer, domain, user_id):
    cur = conn.cursor()
    insert_pending_FAQ_query = """
    INSERT INTO upload_pending_faq (question, answer, domain, user_id)
    VALUES (%s, %s, %s, %s)
    """
    cur.execute(insert_pending_FAQ_query, (question, answer, domain, user_id))
    conn.commit()
    cur.close()
    print(f"Pending FAQ {question} inserted successfully.")