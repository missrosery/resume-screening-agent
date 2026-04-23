"use client";

import { FormEvent, useState } from "react";

import { ResumeDetailDrawer } from "@/components/ResumeDetailDrawer";
import { api } from "@/lib/api";
import { streamChat } from "@/lib/stream";
import { ScreeningMessage } from "@/lib/types";

export function ChatRoom({ sessionId }: { sessionId: string }) {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ScreeningMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [detailResumeId, setDetailResumeId] = useState<string | null>(null);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setMessages([]);
    try {
      await streamChat(api.apiUrl, sessionId, message, (msg) => {
        setMessages((current) => [...current, msg]);
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Streaming failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <main className="grid gap-6 md:grid-cols-[0.9fr_1.1fr]">
        <section className="panel">
          <h2 className="mb-4 text-xl font-semibold">Agent 对话</h2>
          <form className="space-y-3" onSubmit={handleSubmit}>
            <textarea
              className="input min-h-40"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="例如：帮我找 3 位适合 AI Agent 应用开发岗位的候选人"
            />
            <button className="button" disabled={loading} type="submit">
              {loading ? "处理中..." : "发送"}
            </button>
          </form>
          {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
        </section>
        <section className="panel space-y-3">
          <h2 className="text-xl font-semibold">流式输出</h2>
          {messages.map((msg, index) => (
            <div key={`${msg.type}-${index}`} className="rounded-xl border border-slate-200 p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{msg.type}</p>
              {msg.content ? <p className="mt-2 whitespace-pre-wrap text-sm">{msg.content}</p> : null}
              {msg.data ? (
                <div className="mt-3 rounded-lg bg-slate-50 p-3 text-sm">
                  <div className="flex items-center justify-between gap-3">
                    <strong>{msg.data.name}</strong>
                    <div className="flex items-center gap-3">
                      <span>{msg.data.match_score}</span>
                      <button
                        className="text-sm text-slate-600 hover:underline"
                        type="button"
                        onClick={() => setDetailResumeId(msg.data?.resume_id || null)}
                      >
                        查看详情
                      </button>
                    </div>
                  </div>
                  <p className="mt-2">{msg.data.match_reasons.join("；")}</p>
                  <p className="mt-2 text-amber-700">{msg.data.weaknesses.join("；")}</p>
                </div>
              ) : null}
            </div>
          ))}
        </section>
      </main>

      <ResumeDetailDrawer
        open={Boolean(detailResumeId)}
        resumeId={detailResumeId}
        onClose={() => setDetailResumeId(null)}
      />
    </>
  );
}
