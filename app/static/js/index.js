function signOut() {
    // Xử lý đăng xuất và redirect về trang sign in
    window.location.href = '/signin'; // URL này cần thay thế bằng URL của trang sign in
}

function truncateText(text, maxLength) {
    if (text.length > maxLength) {
        return text.substring(0, maxLength) + '...';
    }
    return text;
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

function setCookie(name, value, days) {
    let expires = "";
    if (days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

function clearActiveChatItems() {
    // Loại bỏ class 'active' khỏi tất cả các chat-item
    const chatItems = document.querySelectorAll('.chat-item');
    chatItems.forEach(item => {
        item.classList.remove('active');
    });
}

// Gọi API để lấy danh sách cuộc hội thoại
function loadConversations() {
    const user_id = getCookie('user_id');

    fetch('/get_all_conversations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({user_id})
    })
    .then(response => response.json())
    .then(data => {
        const chatHistory = document.getElementById('chatHistory');
        chatHistory.innerHTML = ''; // Xóa nội dung hiện tại trước khi hiển thị mới

        // Hiển thị các cuộc hội thoại hôm nay
        if (data.today.length > 0) {
            const todayHeader = document.createElement('div');
            todayHeader.innerHTML = '<strong>Hôm nay</strong>';
            todayHeader.classList.add('header-title');
            chatHistory.appendChild(todayHeader);
        
            data.today.forEach(conversation => {
                const chatItem = document.createElement('div');
                chatItem.classList.add('chat-item');
                chatItem.setAttribute('data-id', conversation.conversation_id);
                const truncatedTitle = truncateText(conversation.conversation_title, 30);
                chatItem.innerHTML = `<div>${truncatedTitle}</div>`;
                chatItem.onclick = () => openConversation(conversation.conversation_id);
        
                chatHistory.appendChild(chatItem);
            });
        }
        
        // Tương tự cho Hôm qua và 7 ngày trước
        

        // Hiển thị các cuộc hội thoại hôm qua
        if (data.yesterday.length > 0) {
            const yesterdayHeader = document.createElement('div');
            yesterdayHeader.innerHTML = '<strong>Hôm qua</strong>';
            yesterdayHeader.classList.add('header-title');
            chatHistory.appendChild(yesterdayHeader);

            data.yesterday.forEach(conversation => {
                const chatItem = document.createElement('div');
                chatItem.classList.add('chat-item');
                chatItem.setAttribute('data-id', conversation.conversation_id);
                const truncatedTitle = truncateText(conversation.conversation_title, 30);
                chatItem.innerHTML = `<div>${truncatedTitle}</div>`;
                chatItem.onclick = () => openConversation(conversation.conversation_id);

                chatHistory.appendChild(chatItem);
            });
        }

        // Hiển thị các cuộc hội thoại trong 7 ngày trước
        if (data.last_7_days.length > 0) {
            const last7DaysHeader = document.createElement('div');
            last7DaysHeader.innerHTML = '<strong>7 ngày trước</strong>';
            last7DaysHeader.classList.add('header-title');
            chatHistory.appendChild(last7DaysHeader);

            data.last_7_days.forEach(conversation => {
                const chatItem = document.createElement('div');
                chatItem.classList.add('chat-item');
                chatItem.setAttribute('data-id', conversation.conversation_id);
                const truncatedTitle = truncateText(conversation.conversation_title, 30);
                chatItem.innerHTML = `<div>${truncatedTitle}</div>`;
                chatItem.onclick = () => openConversation(conversation.conversation_id);

                chatHistory.appendChild(chatItem);
            });
        }
    })
    .catch(error => {
        console.error('Error loading conversations:', error);
    });
}


function openConversation(conversation_id, isReload = false) {
    console.log('Opening conversation:', conversation_id);

    // Xử lý giao diện active cho các chat-item
    clearActiveChatItems();
    const chatItem = document.querySelector(`.chat-item[data-id='${conversation_id}']`);
    if (chatItem) {
        chatItem.classList.add('active');
    }

    // Gọi API để lấy session_id từ conversation_id
    fetch('/api/get_session_id', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ conversation_id })
    })
    .then(response => response.json())
    .then(data => {
        if (data.session_id) {
            // Lưu session_id vào cookie
            setCookie('session_id', data.session_id, 1);  // Session có thời gian sống 1 ngày

            // Lưu conversation_id vào cookie
            setCookie('conversation_id', conversation_id, 1);

            // Sau khi session_id và conversation_id đã được thiết lập, gọi API để cập nhật tiêu đề dựa trên tin nhắn thứ 2 của người dùng
            updateConversationTitle(conversation_id, getCookie('user_id'), data.session_id);

            // Reload lại trang nếu không phải là hành động reload lại sau khi mở conversation
            if (!isReload) {
                location.reload();  // Reload lại trang để mở lại conversation
            }
        } else {
            console.error('Error retrieving session_id:', data.error);
        }
    })
    .catch(error => {
        console.error('Error fetching session_id:', error);
    });
}

// Khi nhấn vào nút tạo cuộc trò chuyện mới
document.querySelector('.new-chat-btn').addEventListener('click', function() {
    const user_id = getCookie('user_id'); // Lấy user_id từ cookie

    // Gọi API để tạo session_id mới và bắt đầu cuộc trò chuyện mới
    fetch('/create_new_conversation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_id })
    })
    .then(response => response.json())
    .then(data => {
        if (data.session_id) {
            console.log('New session created:', data.session_id);
            // Lưu session_id vào cookie với thời gian hiệu lực 30 phút
            document.cookie = `session_id=${data.session_id}; path=/; max-age=1800`; // 1800 giây = 30 phút

            // Sau đó gọi API bắt đầu cuộc trò chuyện
            fetch('/api/start_conversation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ user_id, session_id: data.session_id })
            })
            .then(response => response.json())
            .then(conversationData => {
                if (conversationData.conversation_id) {
                    console.log('New conversation started:', conversationData.conversation_id);
                    // Xử lý logic sau khi tạo cuộc trò chuyện mới, ví dụ như mở cuộc trò chuyện mới
                    openConversation(conversationData.conversation_id);
                } else {
                    console.error('Error starting new conversation:', conversationData.result);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        } else {
            console.error('Error creating new session:', data.message);
        }
    })
    .catch(error => {
        console.error('Error creating session:', error);
    });
});

function updateConversationTitle(conversation_id, user_id, session_id) {
    fetch('/api/update_conversation_title', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ conversation_id, user_id, session_id })
    })
    .then(response => response.json())
    .then(data => {
        if (data.new_title) {
            console.log('Conversation title updated:', data.new_title);
            // Cập nhật giao diện nếu cần
        } else {
            console.error('Error updating title:', data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

let isReloaded = false;

window.onload = function() {
    // Lấy user_id từ cookie
    const user_id = getCookie('user_id');
    
    // Nếu tìm thấy user_id, cập nhật tên người dùng trên trang
    if (user_id) {
        const userNameElement = document.getElementById('user-name');
        userNameElement.textContent = `Xin chào, ${user_id}`;
    } else {
        console.error('User ID not found in cookies');
    }
    loadConversations();
    
    // Kiểm tra nếu đã có conversation_id và session_id được lưu trong cookie
    const savedConversationId = getCookie('conversation_id');
    const savedSessionId = getCookie('session_id');

    if (savedConversationId && savedSessionId) {
        // Nếu đã có conversation_id và session_id, thì tự động mở lại conversation
        openConversation(savedConversationId, true);
    }
};

// Hàm để lọc các cuộc hội thoại dựa trên từ khóa tìm kiếm
function searchConversations() {
    const input = document.getElementById('searchInput').value.toLowerCase();
    const chatItems = document.querySelectorAll('.chat-item');
    
    chatItems.forEach(chatItem => {
        const title = chatItem.innerText.toLowerCase();
        if (title.includes(input)) {
            chatItem.style.display = ""; // Hiển thị nếu khớp với từ khóa tìm kiếm
        } else {
            chatItem.style.display = "none"; // Ẩn nếu không khớp với từ khóa tìm kiếm
        }
    });
}

// Thêm sự kiện input cho thanh tìm kiếm
document.getElementById('searchInput').addEventListener('input', searchConversations);