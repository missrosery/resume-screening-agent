import { ScreeningMessage } from "./types";

export async function streamChat(
  apiUrl: string,
  sessionId: string,
  message: string,
  onMessage: (msg: ScreeningMessage) => void,
) {
  const response = await fetch(`${apiUrl}/sessions/${sessionId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!response.ok || !response.body) {
    throw new Error("Streaming request failed");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.trim()) {
        continue;
      }
      onMessage(JSON.parse(line) as ScreeningMessage);
    }
  }

  if (buffer.trim()) {
    onMessage(JSON.parse(buffer) as ScreeningMessage);
  }
}
