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
    const urlParams = new URLSearchParams(window.location.search);
    const user_id = urlParams.get("user_id");
    const session_id = urlParams.get("session_id");
    const conversation_id = sessionStorage.getItem("conversation_id");
  
    if (!conversation_id) {
      console.error("Error: conversation_id is undefined before sending message");
      return;
    }
  
    addMessageToChat(message ? "bot" : "user", messageText, null);
  
    if (!message) {
      userInput.value = "";
    }
    isWaitingForBot = true; // Set flag to true while waiting for bot response
  
    addWaitingBubble(); // Add waiting bubble
  
    fetch(
      `/api/message?text=${encodeURIComponent(
        messageText
      )}&user_id=${encodeURIComponent(user_id)}&session_id=${encodeURIComponent(
        session_id
      )}&conversation_id=${encodeURIComponent(conversation_id)}`
    )
      .then((response) => response.json())
      .then((data) => {
        console.log("Message sent:", data);
        removeWaitingBubble(); // Remove waiting bubble
        if (!message) {
          processBotResponse(data.result, data.message_id, messageText, user_id); // Gọi hàm xử lý kết quả từ bot, truyền thêm messageText là question
        }
        isWaitingForBot = false; // Set flag to false after receiving response
      })
      .catch((error) => {
        console.error("Error:", error);
        removeWaitingBubble(); // Remove waiting bubble
        addMessageToChat("bot", "Sorry, something went wrong.");
        isWaitingForBot = false; // Set flag to false after error
      });
  }
  
  function processBotResponse(result, messageId, messageText, user_id) {
    // Check if response ends with "Domain 1", "Domain 2", "Domain 3", or "Domain 4"
    const domainMatch = result.match(/Domain (1|2|3|4)$/);
    console.log("Đây là domainMatch", domainMatch);
    if (domainMatch) {
      const domain = `Domain ${domainMatch[1]}`;
  
      // Remove the last occurrence of "Domain X" from result
      const resultWithoutDomain = result.replace(/Domain (1|2|3|4)$/, "").trim();
  
      // Add message to chat without the domain part
      addMessageToChat("bot", resultWithoutDomain, messageId);
      
      // Call uploadPendingFAQ
      uploadPendingFAQ(resultWithoutDomain, messageText, domain, user_id);
    } else {
      // Add message to chat as is
      addMessageToChat("bot", result, messageId);
    }
  }
  
  function addMessageToChat(sender, message, messageId) {
    const chatMessages = document.getElementById("chatMessages");
  
    const messageElement = document.createElement("div");
    messageElement.classList.add("message", sender);
    if (messageId) {
      messageElement.dataset.messageId = messageId; // Lưu trữ message_id
    }
  
    const messageContent = document.createElement("div");
    messageContent.classList.add("message-content");
    messageContent.textContent = message;
  
    messageElement.appendChild(messageContent);
  
    if (sender === "bot") {
      const feedbackButtons = document.createElement("div");
      feedbackButtons.classList.add("feedback-buttons");
  
      const likeButton = document.createElement("button");
      likeButton.classList.add("like-button");
      likeButton.innerHTML = '<i class="fas fa-thumbs-up"></i>'; // Add FontAwesome icon
      likeButton.onclick = () => sendFeedback("like", messageId, messageElement);
  
      const dislikeButton = document.createElement("button");
      dislikeButton.classList.add("dislike-button");
      dislikeButton.innerHTML = '<i class="fas fa-thumbs-down"></i>'; // Add FontAwesome icon
      dislikeButton.onclick = () =>
        sendFeedback("dislike", messageId, messageElement);
  
      feedbackButtons.appendChild(likeButton);
      feedbackButtons.appendChild(dislikeButton);
  
      messageElement.appendChild(feedbackButtons);
    }
  
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
  
  function addWaitingBubble() {
    removeWaitingBubble(); // Remove any existing waiting bubble before adding a new one
    const chatMessages = document.getElementById("chatMessages");
  
    const waitingBubble = document.createElement("div");
    waitingBubble.classList.add("message", "bot", "waiting-bubble");
  
    const messageContent = document.createElement("div");
    messageContent.classList.add("message-content");
  
    // Thêm các dấu chấm với hiệu ứng nhấp nháy
    const dot1 = document.createElement("span");
    dot1.classList.add("dot");
    const dot2 = document.createElement("span");
    const dot3 = document.createElement("span");
  
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
  