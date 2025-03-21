let isConversationStarted = false;
let isWaitingForBot = false;
let conversationIdPromise = null;
let feedbackMessageId = null;

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
        console.log("Chui vào cái check rồi");
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
        addMessageToChat(
          "bot",
          "Xin chào, tôi có thể giúp gì bạn?",
          data.message_id
        );
  
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


window.onload = function () {
  console.log("Window loaded");

  // Lấy token từ URL
  const params = new URLSearchParams(window.location.search);
  const token = params.get("token");

  console.log("Token from URL:", token);
  let user_id;
  let session_id;

  if (token) {
    // Gọi API kiểm tra token
    fetch("/api/verify_token", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ token: token }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.user_id && data.session_id) {
          // Lưu user_id và session_id vào localStorage
          localStorage.setItem("user_id", data.user_id);
          localStorage.setItem("session_id", data.session_id);
          user_id = data.user_id;
          session_id = data.session_id;
          console.log("Local storage set successfully");

          // Tiếp tục logic bình thường sau khi lưu user_id và session_id
          continueWithSession(user_id, session_id);
        } else {
          console.error("Invalid token, redirecting to signin...");
          // window.location.href = '/signin';
        }
      })
      .catch((error) => {
        console.error("Error verifying token:", error);
        // window.location.href = '/signin';
      });
  } else {
    // Lấy user_id và session_id từ localStorage nếu không có token
    console.log("Cookie:", getCookie("user_id"));
    console.log("Cookie:", getCookie("session_id"));
    user_id = localStorage.getItem("user_id") || getCookie("user_id");
    session_id = localStorage.getItem("session_id") || getCookie("session_id");

    console.log(
      "User ID from localStorage:",
      user_id,
      "Session ID from localStorage:",
      session_id
    );

    if (user_id && session_id) {
      continueWithSession(user_id, session_id);
    } else {
      console.error("No valid session, redirecting to signin...");
      // window.location.href = '/signin';
    }
  }
};

// Utility functions
function parseMarkdown(text) {
  if (!text) return "";

  // Xử lý headings (thêm vào đầu tiên)
  text = text.replace(/^(\d+)\.\s+(.+)$/gm, '<h3 class="heading">$1. $2</h3>');

  // Xử lý bullet points với dấu gạch ngang
  text = text.replace(/^[-]\s+(.+)$/gm, "<li>$1</li>");
  text = text.replace(/^[○o]\s+(.+)$/gm, "<li>$1</li>");

  // Gom nhóm các bullet points liên tiếp vào ul
  text = text.replace(/((?:<li>.*<\/li>\n?)+)/g, "<ul>$1</ul>");

  // Xử lý code blocks
  text = text.replace(
    /```(\w*)\n([\s\S]*?)```/g,
    function (match, language, code) {
      return `<pre><code class="language-${language}">${code.trim()}</code></pre>`;
    }
  );

  // Xử lý inline code
  text = text.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Xử lý bold text
  text = text.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");

  // Xử lý italic text
  text = text.replace(/\*([^*]+)\*/g, "<em>$1</em>");

  // Xử lý links
  text = text.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    '<a href="$2" target="_blank">$1</a>'
  );

  // Xử lý paragraphs (giữ nguyên khoảng cách cho heading)
  text = text.replace(/\n\n/g, "<br><br>");

  return text;
}

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return null;
}

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
        console.log("Chui vào cái continue rồi");
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

function createFeedbackButtons(messageId, messageElement) {
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
  copyButton.onclick = () =>
    copyToClipboard(
      messageElement.querySelector(".message-content").textContent
    );

  feedbackButtons.appendChild(likeButton);
  feedbackButtons.appendChild(dislikeButton);
  feedbackButtons.appendChild(copyButton);

  return feedbackButtons;
}

function addMessageToChat(sender, message, messageId) {
  const chatMessages = document.getElementById("chatMessages");
  const messageElement = document.createElement("div");
  messageElement.classList.add("message", sender);
  if (messageId) {
    messageElement.dataset.messageId = messageId;
  }

  if (sender === "bot") {
    const botAvatar = document.createElement("img");
    botAvatar.src = "/static/images/Logo_Petrovietnam.svg.png";
    botAvatar.classList.add("bot-avatar");
    messageElement.appendChild(botAvatar);
  }

  const messageContent = document.createElement("div");
  messageContent.classList.add("message-content");

  if (sender === "bot") {
    messageContent.innerHTML = parseMarkdown(message);
  } else {
    messageContent.textContent = message;
  }

  messageElement.appendChild(messageContent);
  chatMessages.appendChild(messageElement);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  return messageElement;
}

function addStreamingMessage(sender, messageId = null) {
  const messageElement = addMessageToChat(sender, "", messageId);
  const messageContent = messageElement.querySelector(".message-content");

  return {
    element: messageElement,
    content: messageContent,
    updateContent: (text) => {
      text = text.replace(/\nTrue$/, "").trim();
      text = text.replace(/\\n/g, "\n");
      messageContent.innerHTML = parseMarkdown(text);
    },
    addFeedback: (messageId) => {
      const feedbackButtons = createFeedbackButtons(messageId, messageElement);
      messageElement.appendChild(feedbackButtons);
    },
  };
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

      if (typeof transcripts === "string") {
        try {
          transcripts = JSON.parse(transcripts);
        } catch (e) {
          console.error("Error parsing transcripts:", e);
          return;
        }
      }

      if (Array.isArray(transcripts) && Array.isArray(transcripts[0])) {
        transcripts = transcripts[0];
      }

      if (Array.isArray(transcripts)) {
        transcripts.forEach((transcript) => {
          if (Array.isArray(transcript)) {
            transcript.forEach((innerTranscript) => {
              if (innerTranscript && innerTranscript.role) {
                const role = innerTranscript.role.toLowerCase();
                if (innerTranscript.text != "") {
                  const messageElement = addMessageToChat(
                    role,
                    innerTranscript.text,
                    innerTranscript.messageId || null
                  );
                  if (role === "bot" && innerTranscript.messageId) {
                    const feedbackButtons = createFeedbackButtons(
                      innerTranscript.messageId,
                      messageElement
                    );
                    messageElement.appendChild(feedbackButtons);
                  }
                }
              }
            });
          } else if (transcript && transcript.role) {
            const role = transcript.role.toLowerCase();
            if (transcript.text != "") {
              const messageElement = addMessageToChat(
                role,
                transcript.text,
                transcript.messageId || null
              );
              if (role === "bot" && transcript.messageId) {
                const feedbackButtons = createFeedbackButtons(
                  transcript.messageId,
                  messageElement
                );
                messageElement.appendChild(feedbackButtons);
              }
            }
          }
        });
      }
    })
    .catch((error) => {
      console.error("Error loading transcripts:", error);
    });
}

function sendMessage(message = null) {
    if (!isConversationStarted || isWaitingForBot) {
        console.log("Conversation has not started yet or still waiting for bot response.");
        return;
    }

    const userInput = document.getElementById("userInput");
    const messageText = message || userInput.value.trim();
    if (messageText === "") return;

    const user_id = localStorage.getItem("user_id") || getCookie("user_id");
    const session_id = localStorage.getItem("session_id") || getCookie("session_id");
    const conversation_id = sessionStorage.getItem("conversation_id") || getCookie("conversation_id");

    if (!conversation_id) {
        console.error("Error: conversation_id is undefined before sending message");
        return;
    }

    // Hiển thị tin nhắn của user
    addMessageToChat("user", messageText, null);
    if (!message) userInput.value = "";
    
    isWaitingForBot = true;
    
    // Thêm waiting bubble
    addWaitingBubble();
    let botResponse = "";
    let botMessage = null;

    const delayMessageTimeout = setTimeout(() => {
        if (!botMessage) {
            removeWaitingBubble();
            botMessage = addStreamingMessage("bot");
            botMessage.updateContent("Chờ chút nhé, tôi đang tổng hợp lại câu trả lời cho bạn đây.");
        }
    }, 4000);

    // Tạo URL với các tham số
    const url = `/api/message?text=${encodeURIComponent(messageText)}&user_id=${encodeURIComponent(user_id)}&session_id=${encodeURIComponent(session_id)}&conversation_id=${encodeURIComponent(conversation_id)}`;

    // Tạo EventSource để xử lý streaming
    const eventSource = new EventSource(url);

    eventSource.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            console.log("Received event:", data);

            if (data.event === 'message') {
                clearTimeout(delayMessageTimeout);

                // Tạo botMessage chỉ khi nhận được chunk đầu tiên
                if (!botMessage) {
                    removeWaitingBubble();
                    botMessage = addStreamingMessage("bot");
                }

                if (!botMessage.element.dataset.messageId) {
                    botMessage.element.dataset.messageId = data.message_id;
                    botMessage.addFeedback(data.message_id);
                }

                if (data.chunk) {
                    let chunk = data.chunk;
                    botResponse += chunk;
                    botMessage.updateContent(botResponse);

                    const chatMessages = document.getElementById("chatMessages");
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            } else if (data.event === 'message_end' || data.event === 'tts_message_end') {
                console.log("Message completed");
                isWaitingForBot = false;
                userInput.disabled = false;
                userInput.focus();
                eventSource.close();
            } else if (data.event === 'error') {
                console.error("Error from server:", data.message);
                if (!botMessage) {
                    removeWaitingBubble();
                    botMessage = addStreamingMessage("bot");
                }
                botMessage.updateContent("Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.");
                isWaitingForBot = false;
                userInput.disabled = false;
            }
        } catch (error) {
            console.error("Error processing event:", error);
            isWaitingForBot = false;
        }
    };

    eventSource.onerror = function(error) {
        // Nếu đã đóng kết nối bình thường thì không xử lý error
        if (eventSource.readyState === EventSource.CLOSED) {
            console.log("EventSource closed normally");
            isWaitingForBot = false;
            return;
        }
        
        // Chỉ xử lý error khi thực sự có lỗi và chưa có response
        if (!botResponse || botResponse.trim() === '') {
            console.error("EventSource error:", error);
            clearTimeout(delayMessageTimeout);
            if (!botMessage) {
                removeWaitingBubble();
                botMessage = addStreamingMessage("bot");
            }
            botMessage.updateContent("Xin lỗi, tôi không đủ thông tin để trả lời câu hỏi này.");
            isWaitingForBot = false;
            userInput.disabled = false;
        }
        
        eventSource.close();
    };
}

function handleKeyPress(event) {
  if (event.key === "Enter" && !isWaitingForBot && isConversationStarted) {
    sendMessage();
  }
}

function copyToClipboard(text) {
  const textarea = document.createElement("textarea");
  textarea.value = text;
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
  alert("Đã sao chép vào clipboard");
}

function sendFeedback(feedbackType, messageId, messageElement) {
  if (!messageId) {
    console.error("Error: messageId is null or undefined");
    return;
  }

  const feedbackButtons = messageElement.querySelector(".feedback-buttons");
  const likeButton = feedbackButtons.querySelector(".like-button");
  const dislikeButton = feedbackButtons.querySelector(".dislike-button");

  // Kiểm tra xem đã có nút nào được chọn chưa
  const hasSelectedFeedback = likeButton.classList.contains("selected") || 
                            dislikeButton.classList.contains("selected");
  if (hasSelectedFeedback) {
    return; // Nếu đã có feedback thì không cho phép thay đổi
  }

  // Disable cả hai nút sau khi đã chọn
  likeButton.disabled = true;
  dislikeButton.disabled = true;

  if (feedbackType === "dislike") {
    feedbackMessageId = messageId;
    showModal();
    dislikeButton.classList.add("selected");
  } else {
    submitFeedback(feedbackType, messageId, "", messageElement);
    likeButton.classList.add("selected");
  }
}

function submitFeedback(feedbackType, messageId, feedbackText, messageElement) {
  const user_id = localStorage.getItem("user_id") || getCookie("user_id");
  const session_id =
    localStorage.getItem("session_id") || getCookie("session_id");

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
    });
}

// Event listeners
document.addEventListener("DOMContentLoaded", function () {
  const userInput = document.getElementById("userInput");
  if (userInput) {
    userInput.addEventListener("keypress", handleKeyPress);
  }
  isConversationStarted = true;
});

// Add CSS
const style = document.createElement("style");
style.textContent = `
    .message-content h3.heading {
        font-size: 1.1em;
        font-weight: bold;
        margin: 0.5em 0 0.2em 0;
        color: #2c3e50;
    }

    .message-content ul {
        list-style-type: disc;
        margin: 0.2em 0;
        padding-left: 2em;
    }

    .message-content li {
        margin: 0.2em 0;
        line-height: 1;
    }

    .message-content p {
        margin: 0.2em 0;
        line-height: 1;
    }

    pre {
        background-color: #f6f8fa;
        border-radius: 6px;
        padding: 16px;
        margin: 0.5em 0;
        overflow: auto;
    }
    
    code {
        font-family: monospace;
        background-color: #f6f8fa;
        padding: 2px 4px;
        border-radius: 3px;
    }
    
    pre code {
        background-color: transparent;
        padding: 0;
    }

    .feedback-buttons button.selected {
        background-color: #e3e3e3;
        cursor: not-allowed;
    }

    .feedback-buttons button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    .feedback-buttons button:not(.selected):not(:disabled):hover {
        background-color: #f0f0f0;
    }
`;
document.head.appendChild(style);

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
