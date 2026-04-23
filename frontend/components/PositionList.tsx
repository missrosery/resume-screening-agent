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

  async function load() {
    try {
      setPositions(await api.listPositions());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    try {
      await api.createPosition({ title, department, requirements });
      setTitle("");
      setDepartment("");
      setRequirements("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create");
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
          <button className="button" type="submit">
            创建岗位
          </button>
        </form>
        {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
      </section>
      <section className="panel">
        <h2 className="mb-4 text-xl font-semibold">岗位列表</h2>
        <div className="space-y-4">
          {positions.map((position) => (
            <Link
              key={position.id}
              href={`/positions/${position.id}`}
              className="block rounded-xl border border-slate-200 p-4 transition hover:border-accent"
            >
              <h3 className="font-semibold">{position.title}</h3>
              <p className="text-sm text-slate-500">{position.department || "未填写部门"}</p>
              <p className="mt-2 line-clamp-3 text-sm text-slate-600">{position.requirements || "未填写 JD"}</p>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
