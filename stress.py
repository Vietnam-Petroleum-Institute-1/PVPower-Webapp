from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import threading
import time

# URL của chatbot
url = 'https://bot.pvpower.vn/'
# Hàm gửi tin nhắn stress test
def send_message_test(thread_id):
    print(f"Starting thread {thread_id}")
    
    # Thay đổi để dùng Edge
    driver = webdriver.Edge(executable_path='path/to/your/edgedriver')  # Đảm bảo cung cấp đúng đường dẫn đến Edge WebDriver

    # Mở URL của chatbot
    driver.get(url)
    time.sleep(2)  # Chờ trang tải

    try:
        # Tìm input message và gửi tin nhắn
        input_box = driver.find_element_by_id('userInput')
        input_box.send_keys(f"Câu hỏi từ người dùng {thread_id}")
        input_box.send_keys(Keys.RETURN)

        print(f"Thread {thread_id}: Gửi câu hỏi thành công!")
        time.sleep(5)  # Chờ phản hồi từ chatbot
    finally:
        driver.quit()

# Số lượng luồng (tạo bao nhiêu người dùng giả lập)
num_threads = 10

# Tạo các luồng
threads = []

for i in range(num_threads):
    thread = threading.Thread(target=send_message_test, args=(i,))
    threads.append(thread)
    thread.start()

# Chờ tất cả các luồng hoàn thành
for thread in threads:
    thread.join()

print("Stress test hoàn thành.")
