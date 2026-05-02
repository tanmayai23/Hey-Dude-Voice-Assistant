/* HEY DUDE — JARVIS · front-end controller
   Robust voice strategy:
   - Browser SpeechRecognition with continuous=false but auto-chained sessions
     (each onend spawns a fresh recognizer — Chrome handles this much better
     than continuous=true which throws InvalidStateError on long sessions).
   - Real-time mic level meter via AudioContext + AnalyserNode so the user
     can SEE the mic is receiving audio even before words are recognized.
   - Auto-finalize after 4s of silence; manual stop sends what's gathered.
   - Aggregates final transcripts across sessions so long sentences work.

   Backend contract preserved:
     receiveRecognitionResult, closeSiriWave, activateMicFromHotword,
     showGeminiResponse, addToChatHistory.
*/
$(function () {
  // ============================================================
  // Visibility-based animation pause
  // ============================================================
  function syncVisibility() {
    document.body.classList.toggle("is-hidden", document.hidden);
  }
  document.addEventListener("visibilitychange", syncVisibility);
  syncVisibility();

  // ============================================================
  // Clock
  // ============================================================
  function tickClock() {
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, "0");
    const mm = String(now.getMinutes()).padStart(2, "0");
    const stamp = `${hh}:${mm}`;
    $("#WidgetClock").text(stamp);
    $("#TopTime").text(stamp);
    $("#WidgetDate").text(
      now.toLocaleDateString(undefined, {
        month: "short", day: "numeric", year: "numeric"
      }).toUpperCase()
    );
  }
  tickClock();
  setInterval(tickClock, 30 * 1000);

  // ============================================================
  // Greeting
  // ============================================================
  (function setGreet() {
    const h = new Date().getHours();
    let word, sub;
    if (h < 5)       { word = "morning"; sub = "LATE WATCH · I'M HERE QUIETLY"; }
    else if (h < 12) { word = "morning"; sub = "SYSTEM READY · STANDING BY"; }
    else if (h < 17) { word = "afternoon"; sub = "SYSTEM READY · STANDING BY"; }
    else if (h < 21) { word = "evening"; sub = "SYSTEM READY · STANDING BY"; }
    else             { word = "night"; sub = "LATE HOURS · STANDING BY"; }
    $("#GreetTimeWord").text(word);
    $("#HeroSub").text(sub);
  })();

  if (typeof eel !== "undefined" && eel.get_profile) {
    eel.get_profile()(function (p) {
      if (p && p.name) {
        const first = p.name.split(" ")[0];
        $("#GreetName").text(first.charAt(0).toUpperCase() + first.slice(1).toLowerCase());
      }
    });
  }

  // ============================================================
  // Chat history
  // ============================================================
  let chatHistory = JSON.parse(localStorage.getItem("chatHistory") || "[]");

  function addToHistory(message, type = "text") {
    const timestamp = new Date().toLocaleString(undefined, {
      month: "short", day: "numeric",
      hour: "2-digit", minute: "2-digit", hour12: false,
    });
    chatHistory.unshift({ message, type, timestamp, fullDate: new Date().toISOString() });
    if (chatHistory.length > 100) chatHistory = chatHistory.slice(0, 100);
    localStorage.setItem("chatHistory", JSON.stringify(chatHistory));
    updateChatHistoryDisplay();
  }
  window.addToChatHistory = addToHistory;
  if (typeof eel !== "undefined" && eel.expose) {
    eel.expose(addToChatHistory, "addToChatHistory");
  }

  function updateChatHistoryDisplay() {
    const $list = $("#chatHistoryList");
    const $empty = $("#emptyHistoryMessage");
    if (chatHistory.length === 0) {
      $empty.show();
      $list.empty();
      return;
    }
    $empty.hide();
    $list.empty();
    chatHistory.forEach((item, index) => {
      const cls = item.type === "voice" ? "voice"
                : item.type === "gemini" ? "gemini" : "text";
      const tag = item.type === "voice" ? "VOICE"
                : item.type === "gemini" ? "AI" : "TEXT";
      const $item = $(`
        <div class="chat-history-item" data-index="${index}">
          <div class="chat-time">${item.timestamp}</div>
          <div class="chat-message"></div>
          <span class="chat-type ${cls}">${tag}</span>
        </div>
      `);
      $item.find(".chat-message").text(item.message);
      $item.click(() => {
        $("#ChatBox").val(item.message).trigger("input");
        const off = bootstrap.Offcanvas.getInstance($("#offcanvasscrolling")[0]);
        if (off) off.hide();
      });
      $list.append($item);
    });
  }

  $("#clearHistoryBtn").click(function () {
    if (confirm("Clear archive?")) {
      chatHistory = [];
      localStorage.removeItem("chatHistory");
      updateChatHistoryDisplay();
    }
  });

  $("#offcanvasscrolling").on("shown.bs.offcanvas", updateChatHistoryDisplay);
  updateChatHistoryDisplay();

  // ============================================================
  // Gemini response
  // ============================================================
  window.showGeminiResponse = function (text) {
    $("#geminiResponseText").text(text);
    $("#geminiResponse").removeAttr("hidden").hide().fadeIn(220);
    $("#Orb").removeClass("is-thinking");
    $("#OrbCaption").text("ready when you are");
  };
  window.closeGeminiResponse = function () {
    $("#geminiResponse").fadeOut(180, function () {
      $(this).attr("hidden", true);
    });
  };
  if (typeof eel !== "undefined" && eel.expose) {
    eel.expose(showGeminiResponse, "showGeminiResponse");
  }

  // ============================================================
  // SiriWave
  // ============================================================
  let siriWave = null;
  let isListening = false;

  function ensureSiriWave() {
    if (siriWave) return true;
    if (typeof SiriWave === "undefined") return false;
    const container = document.getElementById("siri-container");
    if (!container) return false;
    container.innerHTML = "";
    try {
      siriWave = new SiriWave({
        container,
        width: container.offsetWidth || 600,
        height: 44,
        style: "ios9",
        amplitude: 1,
        speed: 0.18,
        color: "#ff2d4f",
        autostart: false,
      });
      return true;
    } catch (err) {
      return false;
    }
  }

  function showLiveBar() {
    $("#LiveBar").removeAttr("hidden");
    $("#SiriMessage").text("listening — speak naturally, take your time");
    $("#Orb").addClass("is-listening");
    $(".composer__shell").addClass("is-listening");
    $("#ComposerHint").attr("hidden", true);
    $("#ComposerLive").removeAttr("hidden");
    $("#DockVoice").text("LIVE");
    document.body.classList.add("is-listening-mode");
    if (ensureSiriWave()) siriWave.start();
  }

  function hideLiveBar() {
    if (siriWave) siriWave.stop();
    $("#LiveBar").attr("hidden", true);
    $("#Orb").removeClass("is-listening is-thinking");
    $("#MicBtn").removeClass("active");
    $(".composer__shell").removeClass("is-listening");
    $("#ComposerHint").removeAttr("hidden");
    $("#ComposerLive").attr("hidden", true);
    $("#DockVoice").text("STANDBY");
    document.body.classList.remove("is-listening-mode");
    isListening = false;
    stopMicMeter();
  }

  window.closeSiriWave = function () { hideLiveBar(); };
  window.activateMicFromHotword = function () {
    if (isListening) return;
    triggerListen();
  };
  if (typeof eel !== "undefined" && eel.expose) {
    eel.expose(closeSiriWave, "closeSiriWave");
    eel.expose(activateMicFromHotword, "activateMicFromHotword");
  }

  window.receiveRecognitionResult = function (text) {
    if (!text) {
      $("#SiriMessage").text("didn't catch that — try once more");
      return;
    }
    $("#SiriMessage").text(text);
    const sysMessages = ["Listening", "Yes,", "How can I help", "Can you repeat", "You typed", "Thinking"];
    const isSystem = sysMessages.some((s) => text.includes(s));
    if (!isSystem) {
      $("#ChatBox").val(text).trigger("input");
      addToHistory(text, "voice");
      $("#Orb").removeClass("is-listening").addClass("is-thinking");
      $("#OrbCaption").text("processing");
    }
  };
  if (typeof eel !== "undefined" && eel.expose) {
    eel.expose(receiveRecognitionResult, "receiveRecognitionResult");
  }

  // ============================================================
  // MIC LEVEL METER — proves the mic is alive even if STT fails
  // ============================================================
  let audioCtx = null;
  let analyser = null;
  let micStream = null;
  let meterRAF = null;

  async function startMicMeter() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;
    try {
      micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      console.warn("Mic permission denied:", err);
      $("#SiriMessage").text("microphone blocked — check the lock icon in the address bar");
      return;
    }

    if (!audioCtx) {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      audioCtx = new Ctx();
    }
    if (audioCtx.state === "suspended") {
      try { await audioCtx.resume(); } catch (e) {}
    }

    const source = audioCtx.createMediaStreamSource(micStream);
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 256;
    analyser.smoothingTimeConstant = 0.6;
    source.connect(analyser);

    const data = new Uint8Array(analyser.frequencyBinCount);
    const $bars = $(".micmeter__bar");
    $(".micmeter").addClass("is-active");

    function loop() {
      analyser.getByteFrequencyData(data);
      // Slice the spectrum into 5 bands
      const bins = [
        avg(data, 0, 5),
        avg(data, 5, 12),
        avg(data, 12, 24),
        avg(data, 24, 48),
        avg(data, 48, 96),
      ];
      bins.forEach((v, i) => {
        const h = Math.max(4, Math.min(28, 4 + (v / 255) * 28));
        $bars.eq(i).css("height", h + "px");
      });
      meterRAF = requestAnimationFrame(loop);
    }
    loop();
  }

  function avg(arr, from, to) {
    let s = 0;
    for (let i = from; i < to && i < arr.length; i++) s += arr[i];
    return s / (to - from);
  }

  function stopMicMeter() {
    if (meterRAF) cancelAnimationFrame(meterRAF);
    meterRAF = null;
    if (micStream) {
      micStream.getTracks().forEach((t) => t.stop());
      micStream = null;
    }
    analyser = null;
    $(".micmeter").removeClass("is-active");
    $(".micmeter__bar").css("height", "6px");
  }

  // ============================================================
  // VOICE — chained sessions for reliability
  // ============================================================
  const BrowserSR = window.SpeechRecognition || window.webkitSpeechRecognition;
  let session = null;

  /* Aggregator */
  let finalAggregate = "";
  let currentInterim = "";
  let userStopped = false;
  let silenceTimer = null;
  const SILENCE_FINALIZE_MS = 4000;

  function clearSilence() {
    if (silenceTimer) { clearTimeout(silenceTimer); silenceTimer = null; }
  }
  function armSilence() {
    clearSilence();
    silenceTimer = setTimeout(finalizeAndSend, SILENCE_FINALIZE_MS);
  }
  function currentSpoken() {
    return (finalAggregate + " " + currentInterim).replace(/\s+/g, " ").trim();
  }
  function finalizeAndSend() {
    const text = currentSpoken();
    if (!text) { stopListen(); return; }
    userStopped = true;
    if (session) { try { session.abort(); } catch (e) {} session = null; }
    hideLiveBar();
    $("#OrbCaption").text("processing");
    sendText(text);
  }

  function buildSession() {
    const r = new BrowserSR();
    r.lang = navigator.language && navigator.language.startsWith("en") ? navigator.language : "en-IN";
    r.continuous = false;       // Chrome handles short sessions much better
    r.interimResults = true;
    r.maxAlternatives = 1;

    r.onresult = function (event) {
      let newFinalThisEvent = "";
      let newInterim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const res = event.results[i];
        const t = res[0].transcript;
        if (res.isFinal) newFinalThisEvent += t + " ";
        else newInterim += t;
      }
      if (newFinalThisEvent) {
        finalAggregate = (finalAggregate + " " + newFinalThisEvent).replace(/\s+/g, " ").trim();
      }
      currentInterim = newInterim.trim();
      const display = currentSpoken();
      $("#ChatBox").val(display).trigger("input");
      $("#SiriMessage").text(display ? display : "listening");
      armSilence();
    };

    r.onerror = function (event) {
      console.warn("SR error:", event.error);
      if (event.error === "not-allowed" || event.error === "service-not-allowed") {
        userStopped = true;
        hideLiveBar();
        $("#SiriMessage").text("microphone blocked — click the lock icon in the address bar");
        $("#OrbCaption").text("mic permission needed");
      } else if (event.error === "audio-capture") {
        userStopped = true;
        hideLiveBar();
        $("#SiriMessage").text("no microphone detected");
      } else if (event.error === "network") {
        // Keep going — sometimes the next session works.
      } else if (event.error === "no-speech" || event.error === "aborted") {
        // Will be handled by onend → restart cycle
      }
    };

    r.onend = function () {
      // If the user hasn't asked to stop, spawn a fresh session.
      // continuous=false naturally ends after a pause; we restart it
      // immediately to keep an open ear until silenceTimer fires or stop.
      session = null;
      if (!userStopped && isListening) {
        setTimeout(() => {
          if (!userStopped && isListening) {
            try {
              session = buildSession();
              session.start();
            } catch (e) {
              console.warn("restart failed", e);
              hideLiveBar();
            }
          }
        }, 120);
      }
    };

    return r;
  }

  function triggerListen() {
    if (!BrowserSR) {
      startPythonListen();
      return;
    }

    // Reset state
    finalAggregate = "";
    currentInterim = "";
    userStopped = false;
    isListening = true;
    $("#ChatBox").val("").trigger("input");
    $("#MicBtn").addClass("active");
    showLiveBar();

    // Start mic level meter (so user can see audio is flowing)
    startMicMeter();

    // Spawn first session
    try {
      session = buildSession();
      session.start();
      try { if (typeof eel !== "undefined" && eel.playassistantsound) eel.playassistantsound(); } catch (e) {}
      armSilence();
    } catch (err) {
      console.warn("SR start failed:", err);
      isListening = false;
      hideLiveBar();
      startPythonListen();
    }
  }

  function startPythonListen() {
    if (typeof eel === "undefined") {
      $("#SiriMessage").text("backend offline");
      return;
    }
    try { if (eel.playassistantsound) eel.playassistantsound(); } catch (e) {}
    showLiveBar();
    startMicMeter();
    try {
      eel.start_listen();
      isListening = true;
      $("#MicBtn").addClass("active");
    } catch (err) {
      hideLiveBar();
    }
  }

  function stopListen() {
    clearSilence();
    userStopped = true;
    if (session) { try { session.abort(); } catch (e) {} session = null; }
    const collected = currentSpoken();
    hideLiveBar();
    if (collected) {
      $("#OrbCaption").text("processing");
      sendText(collected);
    } else {
      $("#OrbCaption").text("tap the reactor or hit the mic");
    }
    finalAggregate = "";
    currentInterim = "";
  }

  $("#MicBtn").click(function () {
    if (isListening) stopListen();
    else triggerListen();
  });
  $("#StopListenBtn").click(stopListen);
  $("#LiveBar").click(function (e) {
    if (e.target === this) stopListen();
  });
  $("#Orb").click(function () {
    if (!isListening) triggerListen();
  });

  $(document).on("keyup", function (e) {
    if ((e.key === "j" || e.key === "J") && e.ctrlKey && e.shiftKey) {
      if (!isListening) triggerListen();
      else stopListen();
    }
  });

  // ============================================================
  // Composer (text)
  // ============================================================
  function sendText(message) {
    if (!message || !message.trim()) return;
    addToHistory(message, "text");
    $("#ChatBox").val("").trigger("input");
    $("#Orb").addClass("is-thinking");
    $("#OrbCaption").text("processing");
    try { eel.allCommands(message); } catch (err) { console.error(err); }
  }

  function showHideSend(value) {
    if (value && value.length > 0) {
      $("#SendBtn").show().removeAttr("hidden");
    } else {
      $("#SendBtn").hide().attr("hidden", true);
    }
  }
  window.ShowHideButton = showHideSend;

  $("#ChatBox").on("input", function () {
    showHideSend($(this).val());
  });
  $("#ChatBox").on("keyup", function (e) {
    if (e.key === "Enter") sendText($(this).val());
  });
  $("#SendBtn").click(function () {
    sendText($("#ChatBox").val());
  });

  $(".sug").click(function () {
    const cmd = $(this).data("cmd");
    if (cmd) sendText(cmd);
  });

  $("#ResetChatBtn").click(function () {
    if (typeof eel !== "undefined" && eel.reset_chat) {
      eel.reset_chat()(function () {
        $("#OrbCaption").text("link reset · ready");
        setTimeout(() => $("#OrbCaption").text("tap the reactor or hit the mic"), 2200);
      });
    }
  });
});
