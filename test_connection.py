import psycopg2
import os

try:
    # Thay thế 'db' bằng tên dịch vụ hoặc IP của container PostgreSQL
    connection = psycopg2.connect(
        host="db",
        database="pvpower",
        user="phuongpd",
        password="vdkvn22.05",
        port="5432"
    )
    cursor = connection.cursor()
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    print("Kết nối thành công tới cơ sở dữ liệu!")
    print("Phiên bản PostgreSQL:", db_version)

except psycopg2.OperationalError as e:
    print("Không thể kết nối đến cơ sở dữ liệu:", e)

finally:
    if 'connection' in locals() and connection is not None:
        cursor.close()
        connection.close()
        print("Đã đóng kết nối tới cơ sở dữ liệu.")
