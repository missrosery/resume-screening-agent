"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { Resume } from "@/lib/types";

export function ResumeDetailDrawer({
  resumeId,
  open,
  onClose,
}: {
  resumeId: string | null;
  open: boolean;
  onClose: () => void;
}) {
  const [resume, setResume] = useState<Resume | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open || !resumeId) {
      return;
    }

    const targetResumeId = resumeId;
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const data = await api.getResume(targetResumeId);
        if (!cancelled) {
          setResume(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load resume");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [open, resumeId]);

  if (!open) {
    return null;
  }

  const parsed = resume?.parsed_data;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/30">
      <button className="flex-1 cursor-default" onClick={onClose} type="button" />
      <aside className="h-full w-full max-w-2xl overflow-y-auto bg-white p-6 shadow-2xl">
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Resume Detail</p>
            <h3 className="mt-2 text-2xl font-semibold">
              {parsed?.name || resume?.file_name || "候选人详情"}
            </h3>
            <p className="mt-2 text-sm text-slate-600">{parsed?.summary || resume?.parse_error}</p>
          </div>
          <button className="text-sm text-slate-500 hover:text-slate-900" onClick={onClose} type="button">
            关闭
          </button>
        </div>

        {loading ? <p className="text-sm text-slate-500">正在加载候选人详情...</p> : null}
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}

        {parsed ? (
          <div className="space-y-6">
            <section className="rounded-xl border border-slate-200 p-4">
              <h4 className="text-sm font-semibold uppercase tracking-[0.15em] text-slate-500">基础信息</h4>
              <div className="mt-3 grid gap-3 text-sm md:grid-cols-2">
                <Info label="姓名" value={parsed.name} />
                <Info label="电话" value={parsed.phone} />
                <Info label="邮箱" value={parsed.email} />
                <Info label="城市" value={parsed.city} />
                <Info label="求职意向" value={parsed.job_intention} />
                <Info label="最高学历" value={parsed.highest_degree} />
                <Info label="工作年限" value={parsed.work_years != null ? `${parsed.work_years} 年` : undefined} />
              </div>
            </section>

            <section className="rounded-xl border border-slate-200 p-4">
              <h4 className="text-sm font-semibold uppercase tracking-[0.15em] text-slate-500">技能与证书</h4>
              <div className="mt-3 flex flex-wrap gap-2">
                {(parsed.skills || []).map((skill) => (
                  <span key={skill} className="rounded-full bg-teal-50 px-3 py-1 text-xs text-teal-700">
                    {skill}
                  </span>
                ))}
              </div>
              {(parsed.certifications || []).length > 0 ? (
                <p className="mt-4 text-sm text-slate-600">
                  证书：{parsed.certifications?.join("；")}
                </p>
              ) : null}
            </section>

            {(parsed.education || []).length > 0 ? (
              <section className="rounded-xl border border-slate-200 p-4">
                <h4 className="text-sm font-semibold uppercase tracking-[0.15em] text-slate-500">教育经历</h4>
                <div className="mt-3 space-y-4">
                  {parsed.education?.map((item, index) => (
                    <div key={`${item.school}-${index}`} className="rounded-lg bg-slate-50 p-3 text-sm">
                      <p className="font-medium">{item.school}</p>
                      <p className="mt-1 text-slate-600">
                        {item.degree} / {item.major}
                      </p>
                      <p className="mt-1 text-slate-500">
                        {item.start_date || "未知"} - {item.end_date || "未知"}
                      </p>
                    </div>
                  ))}
                </div>
              </section>
            ) : null}

            {(parsed.work_experience || []).length > 0 ? (
              <section className="rounded-xl border border-slate-200 p-4">
                <h4 className="text-sm font-semibold uppercase tracking-[0.15em] text-slate-500">工作经历</h4>
                <div className="mt-3 space-y-4">
                  {parsed.work_experience?.map((item, index) => (
                    <div key={`${item.company}-${index}`} className="rounded-lg bg-slate-50 p-3 text-sm">
                      <p className="font-medium">
                        {item.company} / {item.position}
                      </p>
                      <p className="mt-1 text-slate-500">{item.duration}</p>
                      {item.responsibilities?.length ? (
                        <div className="mt-3">
                          <p className="font-medium text-slate-700">职责</p>
                          <ul className="mt-1 list-disc space-y-1 pl-5 text-slate-600">
                            {item.responsibilities.map((entry, entryIndex) => (
                              <li key={`${entryIndex}-${entry}`}>{entry}</li>
                            ))}
                          </ul>
                        </div>
                      ) : null}
                      {item.achievements?.length ? (
                        <div className="mt-3">
                          <p className="font-medium text-slate-700">成果</p>
                          <ul className="mt-1 list-disc space-y-1 pl-5 text-slate-600">
                            {item.achievements.map((entry, entryIndex) => (
                              <li key={`${entryIndex}-${entry}`}>{entry}</li>
                            ))}
                          </ul>
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              </section>
            ) : null}
          </div>
        ) : null}
      </aside>
    </div>
  );
}

function Info({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-[0.15em] text-slate-500">{label}</p>
      <p className="mt-1 text-slate-800">{value || "未填写"}</p>
    </div>
  );
}
