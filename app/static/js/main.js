let isConversationStarted = false;
let isWaitingForBot = false; // New flag to indicate waiting for bot response
let conversationIdPromise = null;
let feedbackMessageId = null;

window.onload = function () {
  console.log("Window loaded");
  const urlParams = new URLSearchParams(window.location.search);
  const user_id = urlParams.get("user_id");
  const session_id = urlParams.get("session_id");
  console.log("User ID:", user_id, "Session ID:", session_id);

  fetch("/api/user_exist", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ user_id}),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log("User existence check:", data);
      if (data.result) {
        conversationIdPromise = checkOrCreateSession(user_id, session_id);
      } else {
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
};
