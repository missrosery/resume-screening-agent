"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

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
  const [deletingPositionId, setDeletingPositionId] = useState<string | null>(null);

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
    const confirmed = window.confirm(
      `确定删除岗位“${position.title}”吗？该岗位下的简历、筛选会话和关联向量文档都会一起删除。`,
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
        <h2 className="mb-4 text-xl font-semibold">创建岗位</h2>
        <form className="space-y-3" onSubmit={handleSubmit}>
          <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="岗位名称" />
          <input className="input" value={department} onChange={(e) => setDepartment(e.target.value)} placeholder="部门" />
          <textarea
            className="input min-h-40"
            value={requirements}
            onChange={(e) => setRequirements(e.target.value)}
            placeholder="岗位要求"
          />
          <button className="button" type="submit" disabled={isCreating}>
            {isCreating ? "创建中..." : "创建岗位"}
          </button>
        </form>
        {message ? <p className="mt-3 text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
      </section>

      <section className="panel">
        <h2 className="mb-4 text-xl font-semibold">岗位列表</h2>
        <div className="space-y-4">
          {positions.map((position) => (
            <article key={position.id} className="rounded-xl border border-slate-200 p-4 transition hover:border-accent">
              <div className="flex items-start justify-between gap-4">
                <Link href={`/positions/${position.id}`} className="min-w-0 flex-1">
                  <h3 className="font-semibold">{position.title}</h3>
                  <p className="text-sm text-slate-500">{position.department || "未填写部门"}</p>
                  <p className="mt-2 line-clamp-3 text-sm text-slate-600">{position.requirements || "未填写 JD"}</p>
                </Link>
                <button
                  className="text-sm text-red-600 hover:text-red-700 disabled:cursor-not-allowed disabled:text-slate-400"
                  type="button"
                  disabled={deletingPositionId === position.id}
                  onClick={() => void handleDelete(position)}
                >
                  {deletingPositionId === position.id ? "删除中..." : "删除"}
                </button>
              </div>
            </article>
          ))}
          {!positions.length ? <p className="text-sm text-slate-500">暂无岗位。</p> : null}
        </div>
      </section>
    </main>
  );
}
