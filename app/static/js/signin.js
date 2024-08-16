document.getElementById('signinForm').addEventListener('submit', function(event) {
    event.preventDefault();  // Ngăn chặn hành động mặc định để kiểm tra tính hợp lệ

    // Lấy các giá trị từ các trường nhập liệu
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('pa