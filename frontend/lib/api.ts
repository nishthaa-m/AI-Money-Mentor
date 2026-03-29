const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function createSession(): Promise<string> {
  const res = await fetch(`${API_BASE}/session/new`, { method: "POST" });
  const data = await res.json();
  return data.session_id;
}

export async function sendMessage(sessionId: string, message: string) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!res.ok) throw new Error("API error");
  return res.json();
}

export interface StreamCallbacks {
  onStatus: (msg: string) => void;
  onToken: (token: string) => void;
  onPlan: (json: string) => void;
  onCalculations: (data: Record<string, any>) => void;
  onDone: (scenario: string | null, profileComplete: boolean) => void;
  onError: (err: string) => void;
}

export async function sendMessageStream(
  sessionId: string,
  message: string,
  callbacks: StreamCallbacks
): Promise<void> {
  const res = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });

  if (!res.ok || !res.body) {
    callbacks.onError("Connection failed");
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      try {
        const event = JSON.parse(line.slice(6));
        switch (event.type) {
          case "status":      callbacks.onStatus(event.content); break;
          case "token":       callbacks.onToken(event.content); break;
          case "plan":        callbacks.onPlan(event.content); break;
          case "calculations": callbacks.onCalculations(event.data); break;
          case "done":        callbacks.onDone(event.scenario, event.profile_complete); break;
        }
      } catch {}
    }
  }
}
