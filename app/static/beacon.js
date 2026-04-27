(function () {
  const schemaVersion = "1.0.0";
  const sessionId = crypto.randomUUID();
  const anonymousUserId = `anon-${crypto.randomUUID()}`;

  const startPanel = document.querySelector("#start-panel");
  const quizPanel = document.querySelector("#quiz-panel");
  const finishPanel = document.querySelector("#finish-panel");
  const startButton = document.querySelector("#start-quiz");
  const nextButton = document.querySelector("#next-question");
  const restartButton = document.querySelector("#restart-quiz");
  const progress = document.querySelector("#quiz-progress");
  const questionElements = Array.from(document.querySelectorAll(".question"));

  const state = {
    order: [],
    orderIndex: -1,
  };

  function baseEvent(eventType, questionId, metadata = {}) {
    return {
      event_id: crypto.randomUUID(),
      event_type: eventType,
      schema_version: schemaVersion,
      session_id: sessionId,
      anonymous_user_id: anonymousUserId,
      occurred_at_client: new Date().toISOString(),
      page_url: window.location.href,
      user_agent: navigator.userAgent,
      question_id: questionId ?? null,
      referrer: document.referrer || null,
      ...metadata,
    };
  }

  function sendBeaconEvent(payload) {
    const body = JSON.stringify(payload);
    if (navigator.sendBeacon) {
      const blob = new Blob([body], { type: "application/json" });
      if (navigator.sendBeacon("/beacon", blob)) {
        return Promise.resolve();
      }
    }
    return fetch("/beacon", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      keepalive: true,
    });
  }

  function shuffledIndexes(length) {
    const indexes = Array.from({ length }, (_, index) => index);
    for (let index = indexes.length - 1; index > 0; index -= 1) {
      const swapIndex = Math.floor(Math.random() * (index + 1));
      [indexes[index], indexes[swapIndex]] = [indexes[swapIndex], indexes[index]];
    }
    return indexes;
  }

  function resetQuestion(questionElement) {
    questionElement.hidden = true;
    questionElement.querySelector(".result").textContent = "";
    questionElement.querySelectorAll("input[type='radio']").forEach((input) => {
      input.checked = false;
      input.disabled = false;
    });
    questionElement.querySelector(".submit-answer").disabled = false;
    questionElement.querySelector(".skip-question").disabled = false;
  }

  function disableQuestion(questionElement) {
    questionElement.querySelectorAll("input[type='radio']").forEach((input) => {
      input.disabled = true;
    });
    questionElement.querySelector(".submit-answer").disabled = true;
    questionElement.querySelector(".skip-question").disabled = true;
  }

  function currentQuestionElement() {
    return questionElements[state.order[state.orderIndex]];
  }

  function currentDisplayOrder() {
    return state.orderIndex >= 0 ? state.orderIndex + 1 : null;
  }

  function hasNextQuestion() {
    return state.orderIndex < state.order.length - 1;
  }

  function showQuestion() {
    questionElements.forEach((questionElement) => {
      questionElement.hidden = true;
    });

    const questionElement = currentQuestionElement();
    const questionId = Number(questionElement.dataset.questionId);
    const displayOrder = currentDisplayOrder();
    questionElement.hidden = false;
    nextButton.hidden = true;
    nextButton.textContent = hasNextQuestion() ? "다음 문제" : "결과 보기";
    progress.textContent = `문제 ${displayOrder} / ${state.order.length}`;
    void sendBeaconEvent(
      baseEvent("page_view", questionId, {
        quiz_step: "question",
        display_order: displayOrder,
      })
    ).catch(() => undefined);
  }

  function showFinish() {
    questionElements.forEach((questionElement) => {
      questionElement.hidden = true;
    });
    quizPanel.hidden = true;
    finishPanel.hidden = false;
    void sendBeaconEvent(
      baseEvent("page_view", null, {
        quiz_step: "finish",
        display_order: null,
      })
    ).catch(() => undefined);
  }

  function moveToNextQuestion() {
    if (!hasNextQuestion()) {
      showFinish();
      return;
    }
    state.orderIndex += 1;
    showQuestion();
  }

  function startQuiz() {
    state.order = shuffledIndexes(questionElements.length);
    state.orderIndex = 0;
    questionElements.forEach(resetQuestion);
    startPanel.hidden = true;
    finishPanel.hidden = true;
    quizPanel.hidden = false;
    showQuestion();
  }

  async function submitAnswer(questionElement) {
    const questionId = Number(questionElement.dataset.questionId);
    const displayOrder = currentDisplayOrder();
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
    disableQuestion(questionElement);
    await sendBeaconEvent({
      ...baseEvent("answer_submitted", questionId, {
        quiz_step: "question",
        display_order: displayOrder,
      }),
      selected_choice: answer.selected_choice,
      correct_choice: answer.correct_choice,
      is_correct: answer.is_correct,
    }).catch(() => undefined);
    nextButton.hidden = false;
  }

  async function skipQuestion(questionElement) {
    const questionId = Number(questionElement.dataset.questionId);
    const displayOrder = currentDisplayOrder();
    disableQuestion(questionElement);
    await fetch("/api/skip", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question_id: questionId, skip_reason: "next_question" }),
    });
    await sendBeaconEvent({
      ...baseEvent("question_skipped", questionId, {
        quiz_step: "question",
        display_order: displayOrder,
      }),
      skip_reason: "next_question",
    }).catch(() => undefined);
    moveToNextQuestion();
  }

  questionElements.forEach((questionElement) => {
    questionElement
      .querySelector(".submit-answer")
      .addEventListener("click", () => void submitAnswer(questionElement));
    questionElement
      .querySelector(".skip-question")
      .addEventListener("click", () => void skipQuestion(questionElement));
  });

  startButton.addEventListener("click", startQuiz);
  nextButton.addEventListener("click", moveToNextQuestion);
  restartButton.addEventListener("click", startQuiz);

  void sendBeaconEvent(
    baseEvent("page_view", null, {
      quiz_step: "landing",
      display_order: null,
    })
  ).catch(() => undefined);
})();
