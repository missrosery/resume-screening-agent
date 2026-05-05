"use client";

import { FormEvent, useState, type ReactNode } from "react";
import {
  MessageSquarePlus,
  Send,
  Brain,
  Wrench,
  FileText,
  CheckCircle2,
  AlertCircle,
  Eye,
  Loader2,
} from "lucide-react";

import { ResumeDetailDrawer } from "@/components/ResumeDetailDrawer";
import { api } from "@/lib/api";
import { streamChat } from "@/lib/stream";
import { ScreeningMessage } from "@/lib/types";

const typeMeta: Record<
  string,
  { label: string; icon: ReactNode; color: string }
> = {
  thinking: {
    label: "思考中",
    icon: <Brain className="h-3.5 w-3.5" />,
    color: "text-muted-foreground bg-muted",
  },
  tool_call: {
    label: "工具调用",
    icon: <Wrench className="h-3.5 w-3.5" />,
    color: "text-primary bg-primary/10",
  },
  text: {
    label: "文本",
    icon: <FileText className="h-3.5 w-3.5" />,
    color: "text-foreground bg-secondary",
  },
  resume_card: {
    label: "候选人",
    icon: <FileText className="h-3.5 w-3.5" />,
    color: "text-indigo-700 bg-indigo-50 dark:text-indigo-400 dark:bg-indigo-500/10",
  },
  done: {
    label: "完成",
    icon: <CheckCircle2 className="h-3.5 w-3.5" />,
    color: "text-emerald-700 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-500/10",
  },
  error: {
    label: "错误",
    icon: <AlertCircle className="h-3.5 w-3.5" />,
    color: "text-red-700 bg-red-50 dark:text-red-400 dark:bg-red-500/10",
  },
};

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
          <div className="mb-4 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <MessageSquarePlus className="h-4 w-4" />
            </div>
            <h2 className="text-xl font-semibold text-foreground">
              Agent 对话
            </h2>
          </div>
          <form className="space-y-3" onSubmit={handleSubmit}>
            <textarea
              className="input min-h-40"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="例如：帮我找 3 位适合 AI Agent 应用开发岗位的候选人"
            />
            <button className="button w-full" disabled={loading} type="submit">
              {loading ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  处理中...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <Send className="h-4 w-4" />
                  发送
                </span>
              )}
            </button>
          </form>
          {error ? (
            <div className="mt-3 flex items-center gap-2 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600 dark:bg-red-500/10 dark:text-red-400">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          ) : null}
        </section>

        <section className="panel space-y-3">
          <div className="mb-1 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <FileText className="h-4 w-4" />
            </div>
            <h2 className="text-xl font-semibold text-foreground">流式输出</h2>
          </div>
          {messages.length === 0 && !loading ? (
            <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border py-16 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
                <MessageSquarePlus className="h-6 w-6 text-muted-foreground" />
              </div>
              <p className="mt-3 text-sm font-medium text-muted-foreground">
                在左侧输入问题开始对话
              </p>
              <p className="mt-1 text-xs text-muted-foreground/70">
                Agent 会流式展示思考与执行过程
              </p>
            </div>
          ) : null}
          {messages.map((msg, index) => {
            const meta = typeMeta[msg.type] || typeMeta.text;
            return (
              <div
                key={`${msg.type}-${index}`}
                className="rounded-xl border border-border bg-background p-4 transition-all duration-200 hover:border-primary/20 hover:shadow-card"
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${meta.color}`}
                  >
                    {meta.icon}
                    {meta.label}
                  </span>
                </div>
                {msg.content ? (
                  <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-foreground">
                    {msg.content}
                  </p>
                ) : null}
                {msg.data ? (
                  <div className="mt-3 rounded-xl border border-border bg-secondary/50 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-primary" />
                        <strong className="text-sm font-semibold text-foreground">
                          {msg.data.name}
                        </strong>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="rounded-full bg-indigo-50 px-3 py-1 text-sm font-semibold text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-400">
                          {msg.data.match_score}
                        </span>
                        <button
                          className="flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-primary"
                          type="button"
                          onClick={() =>
                            setDetailResumeId(msg.data?.resume_id || null)
                          }
                        >
                          <Eye className="h-3.5 w-3.5" />
                          查看详情
                        </button>
                      </div>
                    </div>
                    <p className="mt-3 text-sm text-muted-foreground">
                      {msg.data.match_reasons.join("；")}
                    </p>
                    <p className="mt-2 text-sm text-amber-700 dark:text-amber-400">
                      {msg.data.weaknesses.join("；")}
                    </p>
                  </div>
                ) : null}
              </div>
            );
          })}
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
