const BASE_URL = "http://localhost:8000/api";

/**
 * Sends a message to Sahayak and streams the response.
 * onToken is called for each token received.
 * onDone is called when streaming is complete.
 * Returns the session_id for future messages.
 */
export async function sendMessage(message, sessionId, onToken, onDone) {
  const response = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      ...(sessionId && { session_id: sessionId }),
    }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let currentSessionId = sessionId;
  let isFirstChunk = true;
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value, { stream: true });

    // First chunk always contains SESSION:uuid\n
    if (isFirstChunk) {
      const sessionLine = chunk.split("\n")[0];
      if (sessionLine.startsWith("SESSION:")) {
        currentSessionId = sessionLine.replace("SESSION:", "").trim();
        // Rest of the chunk after the session line is actual content
        const rest = chunk.slice(sessionLine.length + 1);
        if (rest) {
          buffer += rest;
          onToken(rest);
        }
      }
      isFirstChunk = false;
      continue;
    }

    buffer += chunk;
    onToken(chunk);
  }

  onDone(currentSessionId);
  return currentSessionId;
}

export async function clearChat(sessionId) {
  await fetch(`${BASE_URL}/chat/clear`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
}