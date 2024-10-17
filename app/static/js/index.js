function signOut() {
    window.location.href = '/signin'; // URL đăng xuất
}

function truncateText(text, maxLength) {
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
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
    const chatItems = document.querySelectorAll('.chat-item');
    chatItems.forEach(item => {
        item.classList.remove('active');
    });
}

// Gọi API để lấy danh sách các cuộc hội thoại và cập nhật giao diện
function loadConversations() {
    const user_id = getCookie('user_id');

    fetch('/get_all_conversations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_id })
    })
    .then(response => response.json())
    .then(data => {
        const chatHistory = document.getElementById('chatHistory');
        chatHistory.innerHTML = ''; // Xóa nội dung hiện tại trước khi hiển thị mới

        // Hiển thị các cuộc hội thoại hôm nay
        if (data.today && data.today.length > 0) {
            const todayHeader = document.createElement('div');
            todayHeader.innerHTML = '<strong>Hôm nay</strong>';
            todayHeader.classList.add('header-title');
            chatHistory.appendChild(todayHeader);
        
            data.today.forEach(conversation => {
                const chatItem = createChatItem(conversation, 20); // Tạo chat item
                chatHistory.appendChild(chatItem);
            });
        }

        // Hiển thị các cuộc hội thoại hôm qua
        if (data.yesterday && data.yesterday.length > 0) {
            const yesterdayHeader = document.createElement('div');
            yesterdayHeader.innerHTML = '<strong>Hôm qua</strong>';
            yesterdayHeader.classList.add('header-title');
            chatHistory.appendChild(yesterdayHeader);

            data.yesterday.forEach(conversation => {
                const chatItem = createChatItem(conversation, 20); // Tạo chat item
                chatHistory.appendChild(chatItem);
            });
        }

        // Hiển thị các cuộc hội thoại trong 7 ngày trước
        if (data.last_7_days && data.last_7_days.length > 0) {
            const last7DaysHeader = document.createElement('div');
            last7DaysHeader.innerHTML = '<strong>7 ngày trước</strong>';
            last7DaysHeader.classList.add('header-title');
            chatHistory.appendChild(last7DaysHeader);

            data.last_7_days.forEach(conversation => {
                const chatItem = createChatItem(conversation, 20); // Tạo chat item
                chatHistory.appendChild(chatItem);
            });
        }
    })
    .catch(error => {
        console.error('Error loading conversations:', error);
    });
}

// Tạo một phần tử chat item
function createChatItem(conversation, maxLength) {
    const chatItem = document.createElement('div');
    chatItem.classList.add('chat-item');
    chatItem.setAttribute('data-id', conversation.conversation_id);
    
    // Rút gọn tiêu đề nếu cần
    const truncatedTitle = truncateText(conversation.conversation_title, maxLength);
    chatItem.innerHTML = `<div>${truncatedTitle}</div>`;

    // Sự kiện khi bấm vào chat item
    chatItem.onclick = () => openConversation(conversation.conversation_id);

    return chatItem;
}

// Mở một cuộc hội thoại và đánh dấu nó là active
function openConversation(conversation_id, isReload = false) {
    console.log('Opening conversation:', conversation_id);

    // Loại bỏ class active khỏi các chat-item trước đó
    clearActiveChatItems();
    
    // Tìm và đánh dấu phần tử chat item đang mở
    let chatItem = document.querySelector(`.chat-item[data-id='${conversation_id}']`);
    if (chatItem) {
        chatItem.classList.add('active');
        console.log('Added active class to:', chatItem);
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
            setCookie('conversation_id', conversation_id, 1); // Lưu conversation_id vào cookie

            // Gọi API để cập nhật tiêu đề dựa trên tin nhắn thứ 2 của người dùng
            updateConversationTitle(conversation_id, getCookie('user_id'), data.session_id);

            // Reload lại iframe chatbot
            const iframe = document.getElementById('chatbotIframe');
            if (iframe) {
                iframe.src = iframe.src; // Reload lại iframe
            }
        } else {
            console.error('Error retrieving session_id:', data.error);
        }
    })
    .catch(error => {
        console.error('Error fetching session_id:', error);
    });
}

// Hàm cập nhật tiêu đề của cuộc hội thoại
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
            const chatItem = document.querySelector(`.chat-item[data-id='${conversation_id}']`);
            if (chatItem) {
                chatItem.innerHTML = `<div>${truncateText(data.new_title, 20)}</div>`;
            }
        } else {
            console.error('Error updating title:', data.message);
        }
    })
    .catch(error => {
        console.error('Error updating title:', error);
    });
}

// Hàm kích hoạt cuộc trò chuyện đầu tiên sau khi reload
function activateFirstChatItem() {
    const firstChatItem = document.querySelector('.chat-item');
    if (firstChatItem) {
        const firstConversationId = firstChatItem.getAttribute('data-id');
        if (firstConversationId) {
            openConversation(firstConversationId, true); // Kích hoạt cuộc trò chuyện đầu tiên
            firstChatItem.classList.add('active'); // Thêm class active cho item đầu tiên
            console.log('First chat item activated with conversation_id:', firstConversationId);
        }
    } else {
        console.warn('No chat items found');
    }
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
                    // Lưu conversation_id và session_id vào cookie
                    setCookie('conversation_id', conversationData.conversation_id, 1);
                    setCookie('session_id', data.session_id, 1);

                    // Reload toàn bộ trang
                    location.reload();
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

// Kiểm tra sự tồn tại của cookies và redirect nếu cookies hết hạn
function checkCookiesAndRedirect() {
    const user_id = getCookie('user_id');
    const session_id = getCookie('session_id');

    if (!user_id || !session_id) {
        console.log("Cookies đã hết hạn, redirecting...");
        // Redirect về trang signin nếu cookies hết hạn
        // window.location.href = '/signin';
    } else {
        console.log("Cookies vẫn hợp lệ");
    }
}


// Gắn sự kiện input cho thanh tìm kiếm sau khi trang đã tải
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

    // Kiểm tra cookies ngay khi tải trang
    checkCookiesAndRedirect();

    // Kiểm tra cookies sau mỗi 1 phút
    setInterval(checkCookiesAndRedirect, 60000);

    loadConversations();

    // Sau khi load xong các cuộc hội thoại, đợi một khoảng thời gian trước khi kích hoạt item đầu tiên
    setTimeout(() => {
        console.log("Attempting to activate first chat item...");
        activateFirstChatItem(); // Kích hoạt chat item đầu tiên
    }, 200); // Thời gian chờ ngắn để đảm bảo các phần tử được render

    // Gắn sự kiện tìm kiếm
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', searchConversations);
    }
};

