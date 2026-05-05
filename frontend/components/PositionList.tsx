"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import {
  Briefcase,
  Building2,
  FileText,
  Trash2,
  Plus,
  AlertCircle,
  CheckCircle2,
  Inbox,
} from "lucide-react";

import { api } from "@/lib/api";
import { Position } from "@/lib/types";

export function PositionList() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [title, setTitle] = useState("");
  const [department, setDepartment] = useState("");
  const [requirements, setRequirements] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [deletingPositionId, setDeletingPositionId] = useState<string | null>(
    null,
  );

  async function load() {
    try {
      setPositions(await api.listPositions());
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载岗位失败");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMessage("");

    if (!title.trim()) {
      setError("请填写岗位名称");
      return;
    }

    setIsCreating(true);
    try {
      await api.createPosition({
        title: title.trim(),
        department: department.trim() || undefined,
        requirements: requirements.trim() || undefined,
      });
      setTitle("");
      setDepartment("");
      setRequirements("");
      setMessage("岗位已创建。");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建岗位失败");
    } finally {
      setIsCreating(false);
    }
  }

  async function handleDelete(position: Position) {
    if (deletingPositionId) {
      return;
    }

    const confirmed = window.confirm(
      `确定删除岗位"${position.title}"吗？该岗位下的简历、筛选会话和关联向量文档都会一起删除。`,
    );
    if (!confirmed) {
      return;
    }

    setError("");
    setMessage("");
    setDeletingPositionId(position.id);
    try {
      await api.deletePosition(position.id);
      setPositions((items) => items.filter((item) => item.id !== position.id));
      setMessage(`已删除岗位：${position.title}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除岗位失败");
    } finally {
      setDeletingPositionId(null);
    }
  }

  return (
    <main className="grid gap-6 md:grid-cols-[1fr_1.2fr]">
      <section className="panel">
        <div className="mb-5 flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Plus className="h-4 w-4" />
          </div>
          <h2 className="text-lg font-semibold text-foreground">创建岗位</h2>
        </div>
        <form className="space-y-3" onSubmit={handleSubmit}>
          <div className="relative">
            <Briefcase className="absolute left-3.5 top-3 h-4 w-4 text-muted-foreground" />
            <input
              className="input pl-10"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="岗位名称"
            />
          </div>
          <div className="relative">
            <Building2 className="absolute left-3.5 top-3 h-4 w-4 text-muted-foreground" />
            <input
              className="input pl-10"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              placeholder="部门"
            />
          </div>
          <div className="relative">
            <FileText className="absolute left-3.5 top-3 h-4 w-4 text-muted-foreground" />
            <textarea
              className="input min-h-40 pl-10"
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              placeholder="岗位要求"
            />
          </div>
          <button className="button w-full" type="submit" disabled={isCreating}>
            {isCreating ? (
              <span className="flex items-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground" />
                创建中...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Plus className="h-4 w-4" />
                创建岗位
              </span>
            )}
          </button>
        </form>
        {message ? (
          <div className="mt-3 flex items-center gap-2 rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            {message}
          </div>
        ) : null}
        {error ? (
          <div className="mt-3 flex items-center gap-2 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600 dark:bg-red-500/10 dark:text-red-400">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        ) : null}
      </section>

      <section className="panel">
        <div className="mb-5 flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Briefcase className="h-4 w-4" />
          </div>
          <h2 className="text-lg font-semibold text-foreground">岗位列表</h2>
          <span className="ml-auto text-xs text-muted-foreground">
            共 {positions.length} 个岗位
          </span>
        </div>
        <div className="space-y-3">
          {positions.map((position) => (
            <article
              key={position.id}
              className="group rounded-xl border border-border bg-background p-4 transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-elevated"
            >
              <div className="flex items-start justify-between gap-4">
                <Link href={`/positions/${position.id}`} className="min-w-0 flex-1">
                  <h3 className="font-semibold text-foreground transition-colors group-hover:text-primary">
                    {position.title}
                  </h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {position.department || "未填写部门"}
                  </p>
                  <p className="mt-2 line-clamp-3 text-sm text-muted-foreground/80">
                    {position.requirements || "未填写 JD"}
                  </p>
                </Link>
                <button
                  className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs text-red-600 opacity-0 transition-opacity hover:bg-red-50 group-hover:opacity-100 disabled:cursor-not-allowed disabled:opacity-50 dark:text-red-400 dark:hover:bg-red-500/10"
                  type="button"
                  disabled={deletingPositionId !== null}
                  onClick={() => void handleDelete(position)}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  {deletingPositionId === position.id ? "删除中..." : "删除"}
                </button>
              </div>
            </article>
          ))}
          {!positions.length ? (
            <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border py-12 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
                <Inbox className="h-6 w-6 text-muted-foreground" />
              </div>
              <p className="mt-3 text-sm font-medium text-muted-foreground">
                暂无岗位
              </p>
              <p className="mt-1 text-xs text-muted-foreground/70">
                在左侧创建第一个岗位开始体验
              </p>
            </div>
          ) : null}
        </div>
      </section>
    </main>
  );
}
