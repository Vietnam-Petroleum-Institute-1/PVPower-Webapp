import jwt
from datetime import datetime, timedelta

# Thông tin cần mã hóa
user_id = "phuongpd"
secret_key = "96fc0cc6-3531-435d-9279-368691964ed3"  # Khóa bí mật để mã hóa


# Thời gian hiện tại
now = datetime.utcnow()
start = now.date()
# Thời điểm hết hạn (11:00:00)
expiration_time = datetime.combine(now.date(), datetime.min.time()) + timedelta(hours=24, minutes=40)
exp_timestamp = expiration_time.timestamp()
# Payload của token
payload = {
    'user_id': user_id,
    'exp': exp_timestamp,
    "start": start,
    "session_id": "Your session id"
}
print(payload)

# Tạo JWT token
token = jwt.encode(payload, secret_key, algorithm='HS256')

print(f"Generated token: {token}")

token_decode = jwt.decode(token, secret_key, algorithms='HS256')
print("decode:", token_decode)