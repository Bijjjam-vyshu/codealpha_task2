"""A small Python chatbot website with a human-friendly conversation flow.

Run locally with:
    python chatbot_app.py
"""

from __future__ import annotations

import json
import os
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


MAX_MESSAGE_LENGTH = 500


def normalize(text: str) -> str:
    """Normalize text so intent matching stays forgiving."""
    return re.sub(r"\s+", " ", text.strip().lower())


def latest_user_message(history: list[dict[str, str]]) -> str:
    for message in reversed(history):
        if message.get("role") == "user":
            return message.get("content", "")
    return ""


def chatbot_reply(message: str, history: list[dict[str, str]]) -> str:
    """Return a contextual reply without requiring an external AI service."""
    text = normalize(message)
    previous_user_message = normalize(latest_user_message(history[:-1]))

    if not text:
        return "I’m here with you. What would you like to talk about?"

    if re.search(r"\b(hi|hello|hey|hiya|good morning|good afternoon|good evening)\b", text):
        return "Hello! How are you?"

    if re.search(r"\bhow are you\b|\bhow're you\b", text):
        return "I’m doing well, thank you for asking. How are you feeling today?"

    if re.search(r"\b(i am|i'm|im|i feel)\b.*\b(good|great|fine|okay|ok|happy|well)\b", text):
        return "That’s nice to hear. What has been the best part of your day so far?"

    if re.search(r"\b(i am|i'm|im|i feel)\b.*\b(sad|bad|tired|upset|stressed|lonely|angry|not good)\b", text):
        return "I’m sorry you’re feeling that way. Would you like to tell me what happened?"

    if re.search(r"\b(thank you|thanks|thx)\b", text):
        return "You’re welcome. I’m glad I could help."

    if re.search(r"\b(what is your name|who are you|your name)\b", text):
        return "I’m Aura, a friendly little chatbot. What should I call you?"

    if re.search(r"\b(my name is|call me)\b", text):
        name_match = re.search(r"\b(?:my name is|call me)\s+([a-z][a-z -]{1,30})", text)
        name = name_match.group(1).strip().title() if name_match else "friend"
        return f"Nice to meet you, {name}. What would you like to chat about?"

    if re.search(r"\b(help|what can you do|capabilities)\b", text):
        return (
            "I can chat with you, remember the current conversation, answer simple questions, "
            "and keep you company. Try telling me how your day is going."
        )

    if re.search(r"\b(joke|make me laugh)\b", text):
        return "Why did the computer take a break? It needed to get a little more space."

    if re.search(r"\b(weather|temperature|forecast)\b", text):
        return (
            "I can’t check live weather yet, but if you tell me your city I can still help "
            "you plan what to wear or do today."
        )

    if re.search(r"\b(bye|goodbye|see you|see ya|talk later)\b", text):
        return "Goodbye for now. I enjoyed talking with you!"

    if re.search(r"\b(what|why|how|when|where|can you|could you)\b", text):
        return (
            "That’s an interesting question. Tell me a little more about what you mean, "
            "and I’ll think it through with you."
        )

    if previous_user_message and text == previous_user_message:
        return "I heard you. Is there another part of that you’d like to explore?"

    if len(text.split()) <= 3:
        return f"Tell me more about “{message.strip()}”. I’m listening."

    return (
        "That sounds worth talking about. What part of it feels most important to you right now?"
    )


HTML_PAGE = r"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Aura — a friendly chatbot</title>
    <style>
      :root {
        color-scheme: dark;
        --ink: #effaff;
        --muted: #9bc0d4;
        --line: rgba(143, 213, 244, 0.2);
        --panel: rgba(7, 31, 47, 0.88);
        --panel-strong: #0e2e43;
        --accent: #76d4f6;
        --accent-dark: #06283b;
        --bot: #183f56;
        --user: #76d4f6;
      }

      * { box-sizing: border-box; }

      body {
        margin: 0;
        min-height: 100vh;
        color: var(--ink);
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
          "Segoe UI", sans-serif;
        background:
          radial-gradient(circle at 15% 10%, rgba(118, 212, 246, 0.2), transparent 32%),
          radial-gradient(circle at 90% 100%, rgba(38, 115, 153, 0.24), transparent 34%),
          #071b2a;
      }

      .shell {
        width: min(960px, calc(100% - 32px));
        margin: 0 auto;
        padding: 30px 0;
      }

      .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 22px;
      }

      .brand { display: flex; align-items: center; gap: 12px; }
      .mark {
        display: grid;
        width: 42px;
        height: 42px;
        place-items: center;
        color: var(--accent-dark);
        font-weight: 800;
        border-radius: 13px;
        background: var(--accent);
        box-shadow: 0 0 32px rgba(118, 212, 246, 0.28);
      }
      .brand h1 { margin: 0; font-size: 17px; letter-spacing: -0.02em; }
      .brand p { margin: 3px 0 0; color: var(--muted); font-size: 12px; }

      .status {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        color: var(--muted);
        font-size: 12px;
      }
      .status::before {
        width: 7px;
        height: 7px;
        content: "";
        border-radius: 50%;
        background: var(--accent);
        box-shadow: 0 0 0 4px rgba(215, 245, 106, 0.12);
      }

      .chat-card {
        display: flex;
        min-height: min(730px, calc(100vh - 120px));
        flex-direction: column;
        overflow: hidden;
        border: 1px solid var(--line);
        border-radius: 24px;
        background: var(--panel);
        box-shadow: 0 24px 80px rgba(0, 0, 0, 0.32);
        backdrop-filter: blur(20px);
      }

      .intro {
        padding: 28px 30px 20px;
        border-bottom: 1px solid var(--line);
      }
      .eyebrow {
        margin: 0 0 10px;
        color: var(--accent);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }
      .intro h2 {
        max-width: 600px;
        margin: 0;
        font-size: clamp(26px, 4vw, 40px);
        line-height: 1.06;
        letter-spacing: -0.05em;
      }
      .intro-copy {
        max-width: 580px;
        margin: 13px 0 0;
        color: var(--muted);
        font-size: 14px;
        line-height: 1.6;
      }

      .messages {
        display: flex;
        flex: 1;
        min-height: 300px;
        flex-direction: column;
        gap: 16px;
        overflow-y: auto;
        padding: 24px 30px;
      }
      .message-row { display: flex; gap: 10px; animation: rise 220ms ease-out; }
      .message-row.user { justify-content: flex-end; }
      .avatar {
        display: grid;
        flex: 0 0 30px;
        width: 30px;
        height: 30px;
        place-items: center;
        color: var(--accent-dark);
        font-size: 11px;
        font-weight: 800;
        border-radius: 10px;
        background: var(--accent);
      }
      .message-row.user .avatar { order: 2; color: #06283b; background: #c9efff; }
      .bubble {
        max-width: min(75%, 560px);
        padding: 12px 15px;
        color: #e9ebe7;
        font-size: 14px;
        line-height: 1.5;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 17px 17px 17px 5px;
        background: var(--bot);
      }
      .message-row.user .bubble {
        color: var(--accent-dark);
        border: 0;
        border-radius: 17px 17px 5px 17px;
        background: var(--user);
      }
      .time {
        margin-top: 6px;
        color: #777c77;
        font-size: 10px;
      }
      .message-row.user .time { text-align: right; }

      .typing {
        display: none;
        align-items: center;
        gap: 5px;
        padding: 0 30px 14px 70px;
        color: var(--muted);
        font-size: 12px;
      }
      .typing.visible { display: flex; }
      .typing i {
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: var(--accent);
        animation: pulse 900ms infinite;
      }
      .typing i:nth-child(2) { animation-delay: 130ms; }
      .typing i:nth-child(3) { animation-delay: 260ms; }

      .composer-wrap { padding: 0 30px 24px; }
      .quick-prompts { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
      .quick-prompts button {
        padding: 7px 11px;
        color: var(--muted);
        font: inherit;
        font-size: 12px;
        border: 1px solid var(--line);
        border-radius: 999px;
        background: transparent;
        cursor: pointer;
        transition: 160ms ease;
      }
      .quick-prompts button:hover { color: var(--ink); border-color: var(--accent); }
      .composer {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 8px 8px 16px;
        border: 1px solid var(--line);
        border-radius: 17px;
        background: var(--panel-strong);
      }
      textarea {
        flex: 1;
        min-height: 24px;
        max-height: 100px;
        resize: none;
        color: var(--ink);
        font: inherit;
        font-size: 14px;
        border: 0;
        outline: 0;
        background: transparent;
      }
      textarea::placeholder { color: #6d716d; }
      .send {
        display: grid;
        width: 40px;
        height: 40px;
        flex: 0 0 40px;
        place-items: center;
        color: var(--accent-dark);
        font-size: 18px;
        border: 0;
        border-radius: 12px;
        background: var(--accent);
        cursor: pointer;
        transition: transform 160ms ease, background 160ms ease;
      }
      .send:hover { transform: translateY(-2px); background: #a8e8ff; }
      .send:disabled { cursor: wait; opacity: 0.6; }
      .hint { margin: 9px 2px 0; color: #696e69; font-size: 11px; }

      @keyframes rise { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
      @keyframes pulse { 0%, 100% { opacity: .35; transform: translateY(0); } 50% { opacity: 1; transform: translateY(-2px); } }

      @media (max-width: 600px) {
        .shell { width: min(100% - 18px, 960px); padding: 15px 0; }
        .chat-card { min-height: calc(100vh - 84px); border-radius: 20px; }
        .intro, .messages { padding-left: 18px; padding-right: 18px; }
        .composer-wrap { padding: 0 18px 18px; }
        .typing { padding-left: 58px; }
        .bubble { max-width: 84%; }
        .topbar { margin-bottom: 14px; }
        .status { display: none; }
      }
    </style>
  </head>
  <body>
    <main class="shell">
      <header class="topbar">
        <div class="brand">
          <div class="mark">A</div>
          <div><h1>Aura</h1><p>Your friendly conversation partner</p></div>
        </div>
        <div class="status">Online and ready to chat</div>
      </header>

      <section class="chat-card" aria-label="Chat with Aura">
        <div class="intro">
          <p class="eyebrow">A small hello can start anything</p>
          <h2>Tell me what’s on your mind.</h2>
          <p class="intro-copy">I’m here for a relaxed conversation. Say hi, share how your day is going, or ask me a question.</p>
        </div>

        <div id="messages" class="messages" aria-live="polite"></div>
        <div id="typing" class="typing" aria-label="Aura is typing">
          <span>Aura is typing</span><i></i><i></i><i></i>
        </div>

        <div class="composer-wrap">
          <div class="quick-prompts" aria-label="Conversation starters">
            <button type="button" data-message="Hi">Say hi</button>
            <button type="button" data-message="Tell me a joke">Tell me a joke</button>
            <button type="button" data-message="How are you?">Ask how I’m doing</button>
          </div>
          <form id="composer" class="composer">
            <textarea id="message" rows="1" maxlength="500" placeholder="Write a message..." aria-label="Your message"></textarea>
            <button class="send" type="submit" aria-label="Send message">↗</button>
          </form>
          <p class="hint">Press Enter to send · Shift + Enter for a new line</p>
        </div>
      </section>
    </main>

    <script>
      const messagesElement = document.getElementById("messages");
      const composer = document.getElementById("composer");
      const input = document.getElementById("message");
      const sendButton = composer.querySelector(".send");
      const typing = document.getElementById("typing");
      const conversation = [];

      function timeNow() {
        return new Intl.DateTimeFormat([], { hour: "numeric", minute: "2-digit" }).format(new Date());
      }

      function addMessage(role, content) {
        conversation.push({ role, content });
        const row = document.createElement("div");
        row.className = `message-row ${role}`;
        const avatar = document.createElement("div");
        avatar.className = "avatar";
         avatar.textContent = role === "bot" ? "A" : "You";
        const contentWrap = document.createElement("div");
        const bubble = document.createElement("div");
        bubble.className = "bubble";
        bubble.textContent = content;
        const time = document.createElement("div");
        time.className = "time";
        time.textContent = timeNow();
        contentWrap.append(bubble, time);
        row.append(avatar, contentWrap);
        messagesElement.appendChild(row);
        messagesElement.scrollTop = messagesElement.scrollHeight;
      }

      async function sendMessage(rawMessage) {
        const content = rawMessage.trim();
        if (!content || sendButton.disabled) return;
        addMessage("user", content);
        input.value = "";
        input.style.height = "auto";
        sendButton.disabled = true;
        typing.classList.add("visible");
        messagesElement.scrollTop = messagesElement.scrollHeight;

        try {
          const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: content, history: conversation })
          });
          if (!response.ok) throw new Error("Chat request failed");
          const data = await response.json();
          await new Promise((resolve) => setTimeout(resolve, 350));
          addMessage("bot", data.reply);
        } catch (error) {
          addMessage("bot", "I’m having a little trouble connecting. Please try that again.");
        } finally {
          typing.classList.remove("visible");
          sendButton.disabled = false;
          input.focus();
        }
      }

      composer.addEventListener("submit", (event) => {
        event.preventDefault();
        sendMessage(input.value);
      });

      input.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
          event.preventDefault();
          composer.requestSubmit();
        }
      });

      input.addEventListener("input", () => {
        input.style.height = "auto";
        input.style.height = `${Math.min(input.scrollHeight, 100)}px`;
      });

      document.querySelectorAll("[data-message]").forEach((button) => {
        button.addEventListener("click", () => sendMessage(button.dataset.message));
      });

      addMessage("bot", "Hello! I’m Aura. How are you?");
    </script>
  </body>
</html>
"""


class ChatbotHandler(BaseHTTPRequestHandler):
    """Serve the chat page and a small JSON chat endpoint."""

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] not in ("/", "/index.html"):
            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return

        encoded = HTML_PAGE.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self) -> None:
        if self.path.split("?", 1)[0] != "/api/chat":
            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(content_length))
            message = str(body.get("message", "")).strip()
            history = body.get("history", [])
            if not isinstance(history, list):
                history = []
            history = [
                item
                for item in history[-20:]
                if isinstance(item, dict)
                and item.get("role") in {"user", "bot"}
                and isinstance(item.get("content"), str)
            ]
            if len(message) > MAX_MESSAGE_LENGTH:
                self._send_json(
                    {"error": f"Messages must be {MAX_MESSAGE_LENGTH} characters or fewer."},
                    HTTPStatus.BAD_REQUEST,
                )
                return
            self._send_json({"reply": chatbot_reply(message, history)})
        except (ValueError, TypeError, json.JSONDecodeError):
            self._send_json({"error": "Please send a valid chat message."}, HTTPStatus.BAD_REQUEST)

    def log_message(self, format_string: str, *args: Any) -> None:
        # Keep the terminal output useful while avoiding noisy request logs.
        print(f"[chatbot] {self.address_string()} - {format_string % args}")


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), ChatbotHandler)
    print(f"Aura chatbot listening on port {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Aura chatbot")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()