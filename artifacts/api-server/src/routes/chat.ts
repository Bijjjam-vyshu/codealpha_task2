import { Router, type IRouter } from "express";

type ChatMessage = {
  role: "user" | "bot" | "assistant";
  content: string;
};

const router: IRouter = Router();

function normalize(text: string) {
  return text.trim().toLowerCase().replace(/\s+/g, " ");
}

function latestUserMessage(history: ChatMessage[]) {
  for (let index = history.length - 1; index >= 0; index -= 1) {
    if (history[index]?.role === "user") return history[index]?.content ?? "";
  }
  return "";
}

function chatbotReply(message: string, history: ChatMessage[]) {
  const text = normalize(message);
  const previousUserMessage = normalize(latestUserMessage(history.slice(0, -1)));

  if (!text) return "I’m here with you. What would you like to talk about?";
  if (/\b(hi|hello|hey|hiya|good morning|good afternoon|good evening)\b/.test(text)) {
    return "Hello! How are you?";
  }
  if (/\bhow are you\b|\bhow're you\b/.test(text)) {
    return "I’m doing well, thank you for asking. How are you feeling today?";
  }
  if (/\b(i am|i'm|im|i feel)\b.*\b(good|great|fine|okay|ok|happy|well)\b/.test(text)) {
    return "That’s nice to hear. What has been the best part of your day so far?";
  }
  if (/\b(i am|i'm|im|i feel)\b.*\b(sad|bad|tired|upset|stressed|lonely|angry|not good)\b/.test(text)) {
    return "I’m sorry you’re feeling that way. Would you like to tell me what happened?";
  }
  if (/\b(thank you|thanks|thx)\b/.test(text)) return "You’re welcome. I’m glad I could help.";
  if (/\b(what is your name|who are you|your name)\b/.test(text)) {
    return "I’m Aura, a friendly little chatbot. What should I call you?";
  }
  if (/\b(my name is|call me)\b/.test(text)) {
    const nameMatch = text.match(/\b(?:my name is|call me)\s+([a-z][a-z -]{1,30})/);
    const name = nameMatch?.[1]?.trim().replace(/\b\w/g, (letter) => letter.toUpperCase()) ?? "friend";
    return `Nice to meet you, ${name}. What would you like to chat about?`;
  }
  if (/\b(help|what can you do|capabilities)\b/.test(text)) {
    return "I can chat with you, remember the current conversation, answer simple questions, and keep you company. Try telling me how your day is going.";
  }
  if (/\b(joke|make me laugh)\b/.test(text)) {
    return "Why did the computer take a break? It needed to get a little more space.";
  }
  if (/\b(weather|temperature|forecast)\b/.test(text)) {
    return "I can’t check live weather yet, but if you tell me your city I can still help you plan what to wear or do today.";
  }
  if (/\b(bye|goodbye|see you|see ya|talk later)\b/.test(text)) {
    return "Goodbye for now. I enjoyed talking with you!";
  }
  if (/\b(what|why|how|when|where|can you|could you)\b/.test(text)) {
    return "That’s an interesting question. Tell me a little more about what you mean, and I’ll think it through with you.";
  }
  if (previousUserMessage && text === previousUserMessage) {
    return "I heard you. Is there another part of that you’d like to explore?";
  }
  if (text.split(" ").length <= 3) return `Tell me more about “${message.trim()}”. I’m listening.`;
  return "That sounds worth talking about. What part of it feels most important to you right now?";
}

router.post("/chat", (req, res) => {
  const message = typeof req.body?.message === "string" ? req.body.message.trim() : "";
  const rawHistory = Array.isArray(req.body?.history) ? req.body.history : [];
  const history = rawHistory
    .filter(
      (item: unknown): item is ChatMessage =>
        typeof item === "object" &&
        item !== null &&
        "content" in item &&
        typeof item.content === "string" &&
        "role" in item &&
        (item.role === "user" || item.role === "bot" || item.role === "assistant"),
    )
    .slice(-20);

  if (message.length > 500) {
    res.status(400).json({ error: "Messages must be 500 characters or fewer." });
    return;
  }

  res.json({ reply: chatbotReply(message, history) });
});

export default router;