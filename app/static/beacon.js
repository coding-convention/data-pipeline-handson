(function () {
  const schemaVersion = "1.0.0";
  const sessionId = crypto.randomUUID();
  const anonymousUserId = `anon-${crypto.randomUUID()}`;

  function baseEvent(eventType, questionId) {
    return {
      event_id: crypto.randomUUID(),
      event_type: eventType,
      schema_version: schemaVersion,
      session_id: sessionId,
      anonymous_user_id: anonymousUserId,
      occurred_at_client: new Date().toISOString(),
      page_url: window.location.href,
      user_agent: navigator.userAgent,
      question_id: questionId || null,
      referrer: document.referrer || null,
    };
  }

  function sendBeaconEvent(payload) {
    const body = JSON.stringify(payload);
    if (navigator.sendBeacon) {
      const blob = new Blob([body], { type: "application/json" });
      navigator.sendBeacon("/beacon", blob);
      return Promise.resolve();
    }
    return fetch("/beacon", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      keepalive: true,
    });
  }

  async function submitAnswer(questionElement) {
    const questionId = Number(questionElement.dataset.questionId);
    const selected = questionElement.querySelector("input[type='radio']:checked");
    const result = questionElement.querySelector(".result");
    if (!selected) {
      result.textContent = "먼저 선택지를 고르세요.";
      return;
    }

    const response = await fetch("/api/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question_id: questionId, selected_choice: selected.value }),
    });
    const answer = await response.json();
    result.textContent = answer.is_correct ? "정답입니다!" : `오답입니다. 정답은 ${answer.correct_choice} 입니다.`;
    await sendBeaconEvent({
      ...baseEvent("answer_submitted", questionId),
      selected_choice: answer.selected_choice,
      correct_choice: answer.correct_choice,
      is_correct: answer.is_correct,
    });
  }

  async function skipQuestion(questionElement) {
    const questionId = Number(questionElement.dataset.questionId);
    const result = questionElement.querySelector(".result");
    await fetch("/api/skip", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question_id: questionId, skip_reason: "next_question" }),
    });
    result.textContent = "건너뛰기가 기록되었습니다.";
    await sendBeaconEvent({
      ...baseEvent("question_skipped", questionId),
      skip_reason: "next_question",
    });
  }

  document.querySelectorAll(".question").forEach((questionElement) => {
    sendBeaconEvent(baseEvent("page_view", Number(questionElement.dataset.questionId)));
    questionElement
      .querySelector(".submit-answer")
      .addEventListener("click", () => void submitAnswer(questionElement));
    questionElement
      .querySelector(".skip-question")
      .addEventListener("click", () => void skipQuestion(questionElement));
  });
})();
