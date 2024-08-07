function uploadPendingFAQ(answer, question, domain, user_id) {
    fetch("/api/upload_pending_FAQ", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question: question,
        answer: answer, // Assuming answer is the same as question for simplicity
        domain: domain,
        user_id: user_id, // Adjust as needed
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
  
  function sendFeedback(feedbackType, messageId, messageElement) {
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
    feedbackMessageId = null;
  }
  
  function submitDislikeFeedback() {
    const feedbackText = document.getElementById("feedbackText").value;
    const messageElement = document.querySelector(
      `.message[data-message-id="${feedbackMessageId}"]`
    );
    submitFeedback("dislike", feedbackMessageId, feedbackText, messageElement);
    closeModal();
  }
  
  function submitFeedback(feedbackType, messageId, feedbackText, messageElement) {
    const urlParams = new URLSearchParams(window.location.search);
    const user_id = urlParams.get("user_id");
    const session_id = urlParams.get("session_id");
  
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
  