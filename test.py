import jwt
from datetime import datetime, timedelta

# Thông tin cần mã hóa
user_id = "phuongpd"
secret_key = "96fc0cc6-3531-435d-9279-368691964ed3"  # Khóa bí mật để mã hóa

# Thời gian hiện tại
now = datetime.utcnow()
now = now + timedelta(hours=7)

expiration_time = now + timedelta(hours=24, minutes=30)
exp_timestamp = expiration_time.timestamp()
start = now.date()

# Chuyển đổi `start` sang chuỗi để JSON có thể serializable
start_str = start.isoformat()

# Payload của token
payload = {
    'user_id': user_id,
    'exp': exp_timestamp,
    "start": start_str,  # Dùng chuỗi ISO format thay vì object datetime.date
    "session_id": "dsadassdads"
}

print(payload)

# Tạo JWT token
token = jwt.encode(payload, secret_key, algorithm='HS256')

print(f"Generated token: {token}")
# token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoicGh1b25ncGQiLCJzdGFydCI6IjIwMjQtMTAtMTRUMDI6MDc6NDUuODM0WiIsInNlc3Npb25faWQiOiJhYmN4eXoiLCJleHAiOjE3Mjg5NTgwNjV9.n4nFqW_ol6_uxbbigW8dOGMe0xPP7rK0Z5GlL3vKB6M"

# Giải mã JWT token để kiểm tra lại
token_decode = jwt.decode(token, secret_key, algorithms=['HS256'])
print("decode:", token_decode)

# import jwt
# from datetime import datetime, timedelta
# import base64

# # Thông tin cần mã hóa
# user_id = "phuongpd"
# secret_key = "96fc0cc6-3531-435d-9279-368691964ed3"  # Khóa bí mật ban đầu

# # Mã hóa secret key thành Base64 (tương tự với cách họ làm trong Java)
# encoded_secret_key = base64.urlsafe_b64encode(secret_key.encode('utf-8')).decode('utf-8')
# print(f"encoded secret_key: {encoded_secret_key}")

# # Thời gian hiện tại
# now = datetime.utcnow()
# now = now + timedelta(hours=7)

# expiration_time = now + timedelta(hours=24, minutes=0)
# exp_timestamp = expiration_time.timestamp()
# start = now.date()

# # Chuyển đổi `start` sang chuỗi để JSON có thể serializable
# start_str = start.isoformat()

# # Payload của token
# payload = {
#     'user_id': user_id,
#     'exp': exp_timestamp,
#     "start": start_str,  # Dùng chuỗi ISO format thay vì object datetime.date
#     "session_id": "dsadassdads"
# }

# print(payload)

# # Tạo JWT token bằng secret key đã mã hóa Base64
# token = jwt.encode(payload, encoded_secret_key, algorithm='HS256')

# print(f"Generated token: {token}")
# # token = "eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiY2hhdGJvdCIsInN0YXJ0IjoxNzI4NTI1NDMwMjg0LCJzZXNzaW9uX2lkIjoiODgyRUJENzQzNjlGNDg0QTFFMDE1MjhBMkU5RDMyRkIiLCJleHAiOjE3Mjg1MjkwMzAsImlhdCI6MTcyODUyNTQzMH0.DbUnBOoPebNxFjh7dId4EmdDKrf3jzkbHV_mKo5taOU"

# # Giải mã JWT token để kiểm tra lại
# token_decode = jwt.decode(token, encoded_secret_key, algorithms=['HS256'])
# print("decode:", token_decode)
