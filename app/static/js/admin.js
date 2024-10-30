// Khởi tạo đối tượng để lưu trữ các biểu đồ
const charts = {};

// Hàm lấy giá trị từ cookie
function getCookie(name) {
    console.log(document.cookie);
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

// Hàm hủy biểu đồ dựa trên chartId
function destroyChart(chartId) {
    if (charts[chartId]) {
        console.log(`Hủy biểu đồ: ${chartId}`);
        charts[chartId].destroy();
        delete charts[chartId]; // Xóa khỏi danh sách biểu đồ
        console.log(`Biểu đồ ${chartId} đã bị hủy.`);
    } else {
        console.log(`Không tìm thấy biểu đồ ${chartId} để hủy.`);
    }
}

// Hàm reset canvas trước khi vẽ lại
function resetCanvas(chartId) {
    console.log(`Reset canvas cho: ${chartId}`);
    const canvasWrapper = document.getElementById(chartId).parentElement;
    canvasWrapper.innerHTML = `<canvas id="${chartId}"></canvas>`;
}

// Hàm tạo biểu đồ User Messages (Line chart)
function createUserMessagesChart(data) {
    const chartId = 'userMessagesChart';
    destroyChart(chartId);
    resetCanvas(chartId);

    const ctx = document.getElementById(chartId).getContext('2d');
    charts[chartId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Object.keys(data),
            datasets: [{
                label: 'Tin nhắn',
                data: Object.values(data),
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 2,
                fill: true
            }]
        },
        options: {
            responsive: false,
            plugins: {
                title: { display: false }
            }
        }
    });
}

// Hàm tạo biểu đồ Hourly Messages (Bar chart)
function createHourlyMessagesChart(data) {
    const chartId = 'hourlyMessagesChart';
    destroyChart(chartId);
    resetCanvas(chartId);

    const ctx = document.getElementById(chartId).getContext('2d');
    charts[chartId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(data),
            datasets: [{
                label: 'Tin nhắn theo giờ',
                data: Object.values(data),
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: false,
            plugins: {
                title: { display: false }
            }
        }
    });
}

// Hàm tạo biểu đồ Pie (Feedback chart)
function createPieChart(data) {
    const chartId = 'feedbackChart';
    destroyChart(chartId);
    resetCanvas(chartId);

    const canvas = document.getElementById(chartId);
    canvas.style.height = '300px';  // Thiết lập chiều cao 300px

    const ctx = canvas.getContext('2d');
    charts[chartId] = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Like', 'Dislike', 'No Feedback'],
            datasets: [{
                data: [data.like || 0, data.dislike || 0, data.no_feedback || 0],
                backgroundColor: ['#28a745', '#dc3545', '#2B3467']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, // Không duy trì tỷ lệ mặc định
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: false,
                    text: 'Tỷ lệ phản hồi người dùng'
                }
            }
        }
    });
}

// Hàm tạo biểu đồ User Access (Bar chart)
function createUserAccessChart(data) {
    const chartId = 'userAccessChart';
    destroyChart(chartId);
    resetCanvas(chartId);

    const canvas = document.getElementById(chartId);
    canvas.style.height = '300px';  // Thiết lập chiều cao cố định
    canvas.style.width = '100%';    // Đảm bảo chiều rộng 100%

    const ctx = canvas.getContext('2d');
    console.log(`Canvas Height: ${canvas.style.height}, Width: ${canvas.style.width}`); // Kiểm tra log

    charts[chartId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(data),
            datasets: [{
                label: 'Số người dùng',
                data: Object.values(data),
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}



// Hàm khởi tạo tất cả các biểu đồ
function initializeCharts(userMessagesData, hourlyMessagesData, feedbackCounts, userAccessData) {
    try {
        createUserMessagesChart(userMessagesData);
        createHourlyMessagesChart(hourlyMessagesData);
        createPieChart(feedbackCounts);
        createUserAccessChart(userAccessData);
    } catch (error) {
        console.error("Lỗi khi khởi tạo biểu đồ:", error);
    }
}

// Hàm cập nhật nội dung của dashboard
function updateDashboard(data) {
    setTextContentById('totalSessions', data.total_sessions);
    setTextContentById('totalMessages', data.total_messages);
    setTextContentById('avgSessionDuration', `${data.avg_session_duration} giây`);
    setTextContentById('errorRate', `${data.error_rate}%`);
    setTextContentById('avgResponseTime', `${data.avg_response_time} giây`);

    // Cập nhật biểu đồ với dữ liệu mới
    initializeCharts(
        data.user_messages_data,
        data.hourly_messages_data,
        data.feedback_counts,
        data.user_access_data
    );
}

// Hàm cập nhật nội dung của bảng FAQ
function updateFaqTable(data) {
    console.log("Đang cập nhật bảng FAQ với dữ liệu mới:", data);

    // Lấy đối tượng DataTable
    const table = $('#faqTable').DataTable();

    // Xóa dữ liệu cũ khỏi bảng
    table.clear();

    // Thêm dữ liệu mới vào bảng
    data.forEach(item => {
        table.row.add([
            item.text_content,
            item.usage_count
        ]);
    });

    // Vẽ lại bảng với dữ liệu mới
    table.draw();
}

// Hàm hỗ trợ để kiểm tra và gán nội dung văn bản vào các phần tử
function setTextContentById(id, text) {
    const element = document.getElementById(id);
    if (element) {
        element.innerText = text;
    } else {
        console.warn(`Không tìm thấy phần tử với ID: ${id}`);
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');

    // // Thiết lập giá trị mặc định cho endDate là hôm nay
    // const today = new Date().toISOString().split('T')[0];
    // endDateInput.value = today;

    // // Thiết lập startDate là 30 ngày trước từ hôm nay nếu chưa chọn
    // const defaultStartDate = new Date();
    // defaultStartDate.setDate(defaultStartDate.getDate() - 30);
    // startDateInput.value = defaultStartDate.toISOString().split('T')[0];

    // Kiểm tra và không cho phép chọn endDate là ngày trong tương lai
    endDateInput.addEventListener('change', function () {
        if (new Date(endDateInput.value) > new Date()) {
            alert('Ngày kết thúc không thể là ngày trong tương lai.');
            endDateInput.value = today; // Reset lại về hôm nay nếu chọn sai
        }
    });


    // Lắng nghe sự kiện khi người dùng bấm nút "Lọc"
    document.getElementById('filterButton').addEventListener('click', function () {
        const user = document.getElementById('userDropdown').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;

        if (!user) {
            alert('Vui lòng chọn người dùng.');
            return;
        }

        if (new Date(startDate) > new Date(endDate)) {
            alert('Ngày bắt đầu không thể lớn hơn ngày kết thúc.');
            return;
        }

        const filterData = {
            user: user === 'all' ? null : user, // Nếu chọn "Tất cả", gửi user là null
            startDate: startDate,
            endDate: endDate
        };

        fetch('/api/filter_dashboard', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(filterData)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Dữ liệu nhận được từ API:', data);
            updateDashboard(data);
            updateFaqTable(data.non_faqs_data);
        })
        .catch(error => {
            console.error('Lỗi:', error);
            alert('Không có dữ liệu trong phạm vi tìm kiếm.')
        })
    });
});

// Khi trang được load, khởi tạo biểu đồ ban đầu
window.onload = function () {
    const user_id = getCookie('user_id');

    if (user_id) {
        const userNameElement = document.getElementById('user-name');
        userNameElement.textContent = `Xin chào, ${user_id}`;
    } else {
        console.error('User ID not found in cookies');
        window.location.href = 'signin';
    }
};
