from functools import wraps
from flask import session, redirect, url_for, abort, request
from databases import connect_db, admin_verify, session_exists

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        conn = connect_db()
        # Kiểm tra xem người dùng có trong session và có quyền admin không
        user_id = request.cookies.get('user_id')
        session_id = request.cookies.get('session_id')
        if not admin_verify(conn, user_id):
            # Nếu không có quyền, trả về lỗi 403 Forbidden
            abort(403)  
        if not session_exists(conn, user_id, session_id):
            abort(403) 
        return f(*args, **kwargs)
    return decorated_function
