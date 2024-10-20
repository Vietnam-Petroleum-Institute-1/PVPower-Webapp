let isConversationStarted = false;
let isWaitingForBot = false; // New flag to indicate waiting for bot response
let conversationIdPromise = null;
let feedbackMessageId = null;

window.onload = function () {
  console.log("Window loaded");

  // Lấy token từ URL
  const params = new URLSearchParams(window.location.search);
  const token = params.get('token');
  
  console.log('Token from URL:', token);  
  let user_id;
  let session_id;

  if (token) {
      // Gọi API kiểm tra token
      fetch('/api/verify_token', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
          },
          body: JSON.stringify({ token: token }),
      })
      .then(response => response.json())
      .then(data => {
          if (data.user_id && data.session_id) {
              // Lưu user_id và session_id vào localStorage
              localStorage.setItem('user_id', data.user_id);
              localStorage.setItem('session_id', data.session_id);
              user_id = data.user_id;
              session_id = data.session_id;
              console.log('Local storage set successfully');

              // Tiếp tục logic bình thường sau khi lưu user_id và session_id
              continueWithSession(user_id, session_id);
          } else {
              console.error('Invalid token, redirecting to signin...');
              // window.location.href = '/signin';
          }
      })
      .catch(error => {
          console.error('Error verifying token:', error);
          // window.location.href = '/signin';
      });
  } else {
    // Lấy user_id và session_id từ localStorage nếu không có token
    console.log("Cookie:", getCookie("user_id"));
    console.log("Cookie:", getCookie("session_id"));
    user_id = localStorage.getItem("user_id") || getCookie("user_id");
    session_id = localStorage.getItem("session_id") || getCookie("session_id");
    
    console.log("User ID from localStorage:", user_id, "Session ID from localStorage:", session_id);
    
    if (user_id && session_id) {
      continueWithSession(user_id, session_id);
    } else {
      console.error('No valid session, redirecting to signin...');
      // window.location.href = '/signin';
    }
  }
};

// Hàm tiếp tục logic sau khi có user_id và session_id
function continueWithSession(user_id, session_id) {
  console.log("User ID:", user_id, "Session ID:", session_id);
  // Nếu có user_id và session_id, tiếp tục logic bình thường
  fetch("/api/user_exist", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ user_id }),
  })
  .then((response) => response.json())
  .then((data) => {
    console.log("User existence check:", data);
    if (data.result) {
      conversationIdPromise = checkOrCreateSession(user_id, session_id);
      loadTranscripts(user_id, session_id); // Load transcripts nếu có session_id
    } else {
      console.log("Chui vào cái continue rồi")
      document.getElementById("chatMessages").innerHTML =
        '<div class="message bot"><div class="message-content">Vui lòng đăng nhập để sử dụng trợ lý ảo</div></div>';
      const chatInput = document.querySelector(".chat-input");
      if (chatInput) {
        chatInput.style.display = "none";
      }
    }
  })
  .catch((error) => {
    console.error("Error:", error);
  });
}

function loadTranscripts(user_id, session_id) {
  console.log("Loading transcripts");

  fetch("/api/get_transcripts", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ user_id, session_id }),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log("Transcripts data received:", data);

      let transcripts = data.transcripts;

      // Nếu transcripts là một chuỗi, parse nó thành object
      if (typeof transcripts === "string") {
        try {
          transcripts = JSON.parse(transcripts);
        } catch (e) {
          console.error("Error parsing transcripts:", e);
          return;
        }
      }

      // Kiểm tra nếu transcripts là một mảng và chứa các mảng bên trong
      if (Array.isArray(transcripts) && Array.isArray(transcripts[0])) {
        transcripts = transcripts[0];
      }

      // Kiểm tra nếu transcripts là một mảng
      if (Array.isArray(transcripts)) {
        transcripts.forEach((transcript) => {
          if (Array.isArray(transcript)) {
            transcript.forEach((innerTranscript) => {
              if (innerTranscript && innerTranscript.role) {
                const role = innerTranscript.role.toLowerCase();
                if (innerTranscript.text != "") {
                  addMessageToChat(
                    role,
                    innerTranscript.text,
                    innerTranscript.messageId || null
                  );
                }
              } else {
                console.warn("Transcript item missing role:", innerTranscript);
              }
            });
          } else if (transcript && transcript.role) {
            const role = transcript.role.toLowerCase();
            addMessageToChat(
              role,
              transcript.text,
              transcript.messageId || null
            );
          } else {
            console.warn("Transcript item missing role:", transcript);
          }
        });
      } else {
        console.error("Transcripts data is not in the expected format.");
      }
    })
    .catch((error) => {
      console.error("Error loading transcripts:", error);
    });
}

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return null;
}

function checkOrCreateSession(user_id, session_id) {
  console.log("Checking or creating session");
  showWaitingBubble();
  return fetch("/api/session_exist", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ user_id, session_id }),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log("Session existence check:", data);
      if (data.result === 1) {
        document.getElementById("chatContainer").style.display = "flex";
        return getConversation(user_id, session_id);
      } else if (data.result === 0) {
        const currentDate = new Date();
        const start_time = new Date(
          currentDate.getTime() + 7 * 60 * 60 * 1000
        ).toISOString();
        const end_time = new Date(
          currentDate.getTime() + 7 * 60 * 60 * 1000 + 60 * 60 * 1000
        ).toISOString();
        return createSession(user_id, session_id, start_time, end_time);
      } else {
        console.log("Chui vào cái check rồi")
        document.getElementById("chatMessages").innerHTML =
          '<div class="message bot"><div class="message-content">Vui lòng đăng nhập để sử dụng trợ lý ảo</div></div>';
        const chatInput = document.querySelector(".chat-input");
        if (chatInput) {
          chatInput.style.display = "none";
        }
      }
    })
    .catch((error) => {
      console.error("Error in checkOrCreateSession:", error);
      throw error;
    })
    .finally(() => {
      hideWaitingBubble();
    });
}

function createSession(user_id, session_id, start_time, end_time) {
  console.log("Creating session");
  showWaitingBubble();
  return fetch("/api/session", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ user_id, session_id, start_time, end_time }),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log("Session creation result:", data);
      document.getElementById("chatContainer").style.display = "flex";
      return startConversation(user_id, session_id);
    })
    .catch((error) => {
      console.error("Error in createSession:", error);
      throw error;
    })
    .finally(() => {
      hideWaitingBubble();
    });
}

function startConversation(user_id, session_id) {
  console.log("Starting conversation");
  showWaitingBubble();
  return fetch("/api/start_conversation", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ user_id, session_id }),
  })
    .then((response) => response.json())
    .then((data) => {
      const conversation_id = data.conversation_id;
      sessionStorage.setItem("conversation_id", conversation_id);

      const userInput = document.getElementById("userInput");
      const sendButton = document.getElementById("sendButton");
      if (userInput && sendButton) {
        userInput.disabled = false;
        sendButton.disabled = false;
      }

      isConversationStarted = true;
      addMessageToChat("bot", "Xin chào, tôi có thể giúp gì bạn?", data.message_id);

      return conversation_id;
    })
    .catch((error) => {
      console.error("Error in startConversation:", error);
      throw error;
    })
    .finally(() => {
      hideWaitingBubble();
    });
}

function getConversation(user_id, session_id) {
  console.log("Getting conversation");
  showWaitingBubble();
  return fetch("/api/conversation_id", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ user_id, session_id }),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log("Conversation ID:", data.result);
      sessionStorage.setItem("conversation_id", data.result);

      const userInput = document.getElementById("userInput");
      const sendButton = document.getElementById("sendButton");
      if (userInput && sendButton) {
        userInput.disabled = false;
        sendButton.disabled = false;
      }

      isConversationStarted = true;
      return data.result;
    })
    .catch((error) => {
      console.error("Error in getConversation:", error);
      throw error;
    })
    .finally(() => {
      hideWaitingBubble();
    });
}

function handleKeyPress(event) {
  if (event.key === "Enter" && !isWaitingForBot && isConversationStarted) {
    sendMessage();
  }
}

function sendMessage(message = null) {
  if (!isConversationStarted || isWaitingForBot) {
    console.log(
      "Conversation has not started yet or still waiting for bot response."
    );
    return;
  }

  const userInput = document.getElementById("userInput");
  const messageText = message || userInput.value.trim();
  if (messageText === "") {
    return;
  }

  const user_id = localStorage.getItem("user_id") || getCookie("user_id");
  const session_id = localStorage.getItem("session_id") || getCookie("session_id");
  const conversation_id = sessionStorage.getItem("conversation_id");

  if (!conversation_id) {
    console.error("Error: conversation_id is undefined before sending message");
    return;
  }

  addMessageToChat(message ? "bot" : "user", messageText, null);

  if (!message) {
    userInput.value = "";
  }
  isWaitingForBot = true;
  addWaitingBubble();

  const delayMessageTimeout = setTimeout(() => {
    removeWaitingBubble();
    addMessageToChat(
      "bot",
      "Chờ chút nhé, tôi đang tổng hợp lại câu trả lời cho bạn đây."
    );
    addWaitingBubble();
  }, 4000);

  fetch(
    `/api/message?text=${encodeURIComponent(
      messageText
    )}&user_id=${encodeURIComponent(user_id)}&session_id=${encodeURIComponent(
      session_id
    )}&conversation_id=${encodeURIComponent(conversation_id)}`
  )
    .then((response) => response.json())
    .then((data) => {
      clearTimeout(delayMessageTimeout);
      console.log("Message sent:", data);
      removeWaitingBubble();
      processBotResponse(data.result, data.message_id, messageText, user_id);
      handleResponse(data.result);
      isWaitingForBot = false;
    })
    .catch((error) => {
      clearTimeout(delayMessageTimeout);
      console.error("Error:", error);
      removeWaitingBubble();
      addMessageToChat(
        "bot",
        "Xin lỗi, tôi không đủ thông tin để trả lời câu hỏi này."
      );
      isWaitingForBot = false;
    });
}

function processBotResponse(result, messageId, messageText, user_id) {
  const domainMatch = result.match(/Group (1|2|3|4) Doc$/);
  console.log("Đây là domainMatch", domainMatch);
  if (domainMatch) {
    const domain = `False Group ${domainMatch[1]}`;

    const resultWithoutDomain = result
      .replace(/False Group (1|2|3|4) Doc$/, "")
      .trim();

    addMessageToChat("bot", resultWithoutDomain, messageId);

    uploadPendingFAQ(resultWithoutDomain, messageText, domain, user_id);
  } else if (result.match(/False/)) {
    const domain = `False`;

    const resultWithoutDomain = result.replace(/False/, "").trim();

    addMessageToChat("bot", resultWithoutDomain, messageId);

    uploadPendingFAQ(resultWithoutDomain, messageText, domain, user_id);
  } else {
    const resultWithoutDomain = result.replace(/True/, "").trim();

    addMessageToChat("bot", resultWithoutDomain, messageId);
  }
}

function uploadPendingFAQ(answer, question, domain, user_id) {
  fetch("/api/upload_pending_FAQ", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question: question,
      answer: answer,
      domain: domain,
      user_id: user_id,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log("Success:", data);
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}

function addMessageToChat(sender, message, messageId) {
  const chatMessages = document.getElementById("chatMessages");

  const messageElement = document.createElement("div");
  messageElement.classList.add("message", sender);
  if (messageId) {
    messageElement.dataset.messageId = messageId; // Lưu trữ message_id
  }

  // Thêm hình ảnh avatar cho bot nếu sender là bot
  if (sender === "bot") {
    const botAvatar = document.createElement("img");
    botAvatar.src = "/static/images/Logo_Petrovietnam.svg.png"; // Đường dẫn đến ảnh avatar của bot
    botAvatar.classList.add("bot-avatar");
    messageElement.appendChild(botAvatar);
  }

  const messageContent = document.createElement("div");
  messageContent.classList.add("message-content");
  messageContent.textContent = message;

  messageElement.appendChild(messageContent);

  // Nếu tin nhắn là của bot và có messageId, thêm nút feedback
  if (sender === "bot" && messageId) {
    const feedbackButtons = document.createElement("div");
    feedbackButtons.classList.add("feedback-buttons");

    const likeButton = document.createElement("button");
    likeButton.classList.add("like-button");
    likeButton.innerHTML = '<i class="fas fa-thumbs-up"></i>';
    likeButton.onclick = () => sendFeedback("like", messageId, messageElement);

    const dislikeButton = document.createElement("button");
    dislikeButton.classList.add("dislike-button");
    dislikeButton.innerHTML = '<i class="fas fa-thumbs-down"></i>';
    dislikeButton.onclick = () =>
      sendFeedback("dislike", messageId, messageElement);

    const copyButton = document.createElement("button");
    copyButton.classList.add("copy-button");
    copyButton.innerHTML = '<i class="fas fa-copy"></i>';
    copyButton.onclick = () => copyToClipboard(messageContent.textContent);

    feedbackButtons.appendChild(likeButton);
    feedbackButtons.appendChild(dislikeButton);
    feedbackButtons.appendChild(copyButton);

    // Thêm feedback buttons vào messageElement nhưng nằm ngoài messageContent
    messageElement.appendChild(feedbackButtons);
  }

  chatMessages.appendChild(messageElement);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Hàm để sao chép nội dung vào clipboard
function copyToClipboard(text) {
  const textarea = document.createElement("textarea");
  textarea.value = text;
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
  alert("Copied to clipboard");
}

function addWaitingBubble() {
  removeWaitingBubble();
  const chatMessages = document.getElementById("chatMessages");

  const waitingBubble = document.createElement("div");
  waitingBubble.classList.add("message", "bot", "waiting-bubble");

  const messageContent = document.createElement("div");
  messageContent.classList.add("message-content");

  const dot1 = document.createElement("span");
  dot1.classList.add("dot");
  const dot2 = document.createElement("span");
  dot2.classList.add("dot");
  const dot3 = document.createElement("span");
  dot3.classList.add("dot");

  messageContent.appendChild(dot1);
  messageContent.appendChild(dot2);
  messageContent.appendChild(dot3);

  waitingBubble.appendChild(messageContent);
  chatMessages.appendChild(waitingBubble);

  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeWaitingBubble() {
  const chatMessages = document.getElementById("chatMessages");
  const waitingBubble = chatMessages.querySelector(".waiting-bubble");
  if (waitingBubble) {
    chatMessages.removeChild(waitingBubble);
  }
}

function showWaitingBubble() {
  removeWaitingBubble();
  const chatMessages = document.getElementById("chatMessages");
  const waitingBubble = document.createElement("div");
  waitingBubble.classList.add("message", "bot", "waiting-bubble");

  const messageContent = document.createElement("div");
  messageContent.classList.add("message-content");

  const dot1 = document.createElement("span");
  dot1.classList.add("dot");
  const dot2 = document.createElement("span");
  dot2.classList.add("dot");
  const dot3 = document.createElement("span");
  dot3.classList.add("dot");
  messageContent.appendChild(dot1);
  messageContent.appendChild(dot2);
  messageContent.appendChild(dot3);

  waitingBubble.appendChild(messageContent);
  chatMessages.appendChild(waitingBubble);

  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideWaitingBubble() {
  removeWaitingBubble();
}

function submitFeedback(feedbackType, messageId, feedbackText, messageElement) {
  const user_id = getCookie("user_id");
  const session_id = getCookie("session_id");

  fetch("/api/feedback", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_id,
      session_id,
      messageId,
      feedbackType,
      feedbackText,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log("Feedback sent:", data);
      if (feedbackType === "dislike") {
        messageElement
          .querySelector(".dislike-button")
          .classList.add("selected");
      } else {
        messageElement.querySelector(".like-button").classList.add("selected");
      }
    })
    .catch((error) => {
      console.error("Error sending feedback:", error);
      if (error.message.includes("Unexpected token")) {
        console.error("Likely received HTML instead of JSON. Server error.");
      } else {
        console.error("Unknown error occurred while sending feedback.");
      }
    });
}

function sendFeedback(feedbackType, messageId, messageElement) {
  if (!messageId) {
    console.error("Error: messageId is null or undefined");
    return;
  }

  const feedbackButtons = messageElement.querySelector(".feedback-buttons");
  const likeButton = feedbackButtons.querySelector(".like-button");
  const dislikeButton = feedbackButtons.querySelector(".dislike-button");

  // Disable buttons after feedback
  likeButton.disabled = true;
  dislikeButton.disabled = true;

  if (feedbackType === "dislike") {
    feedbackMessageId = messageId;
    showModal();
  } else {
    submitFeedback(feedbackType, messageId, "", messageElement);
  }
}

function showModal() {
  document.getElementById("feedbackModal").style.display = "block";
}

function closeModal() {
  document.getElementById("feedbackModal").style.display = "none";

  // Kích hoạt lại các nút like và dislike khi modal bị đóng
  if (feedbackMessageId) {
    const messageElement = document.querySelector(
      `.message[data-message-id="${feedbackMessageId}"]`
    );
    if (messageElement) {
      const feedbackButtons = messageElement.querySelector(".feedback-buttons");
      const likeButton = feedbackButtons.querySelector(".like-button");
      const dislikeButton = feedbackButtons.querySelector(".dislike-button");

      likeButton.disabled = false;
      dislikeButton.disabled = false;

      dislikeButton.classList.remove("selected"); // Bỏ trạng thái đã chọn
    }
  }

  feedbackMessageId = null; // Reset lại feedbackMessageId
}

function submitDislikeFeedback() {
  const feedbackText = document.getElementById("feedbackText").value;
  const messageElement = document.querySelector(
    `.message[data-message-id="${feedbackMessageId}"]`
  );
  submitFeedback("dislike", feedbackMessageId, feedbackText, messageElement);
  closeModal();
}

function handleResponse(response) {
  // Giả định response là một object có chứa mảng các câu hỏi
  const extractedQuestions = extractQuestionsFromResponse(response);

  // Nếu có câu hỏi, hiển thị chúng dưới dạng bong bóng gợi ý
  if (extractedQuestions.length > 0) {
    showSuggestions(extractedQuestions);
  }
}

// Hàm trích xuất câu hỏi từ response (tuỳ thuộc vào cấu trúc của response)
function extractQuestionsFromResponse(response) {
  const questions = [];
  const questionPattern = /Câu hỏi \d+:\s(.+?)(?:$|\n)/g; // Regex để tìm các câu hỏi trong response
  let match;
  while ((match = questionPattern.exec(response)) !== null) {
    questions.push(match[1].trim());
  }
  return questions;
}

function showSuggestions(questions) {
  const suggestionsContainer = document.getElementById("suggestions-container");
  suggestionsContainer.innerHTML = ""; // Xóa các gợi ý trước đó
  suggestionsContainer.style.display = "flex"; // Hiển thị lại container nếu nó bị ẩn

  questions.forEach((question, index) => {
    const suggestionButton = document.createElement("button");
    suggestionButton.classList.add("suggestion-bubble");
    suggestionButton.textContent = `Câu hỏi ${index + 1}: ${question}`;
    suggestionButton.onclick = () => sendSuggestedQuestion(question);
    suggestionsContainer.appendChild(suggestionButton);
  });
}

function sendSuggestedQuestion(question) {
  const userInput = document.getElementById("userInput");
  userInput.value = question; // Đặt câu hỏi vào ô nhập liệu

  hideSuggestions(); // Ẩn ngay các bong bóng gợi ý sau khi người dùng chọn

  sendMessage(); // Tự động gửi câu hỏi
}

function hideSuggestions() {
  const suggestionsContainer = document.getElementById("suggestions-container");
  suggestionsContainer.innerHTML = ""; // Xóa toàn bộ các nút gợi ý
  suggestionsContainer.style.display = "none"; // Ẩn container
}

function openInNewTab() {
  window.open('https://bot.pvpower.vn', '_blank');
}

document.addEventListener('visibilitychange', function() {
  if (document.visibilityState === 'visible') {
    location.reload(); // Reload lại trang khi tab được quay lại
  }
});