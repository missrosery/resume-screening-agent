"use client";

import { useEffect, useState, type ReactNode } from "react";
import { X, GraduationCap, Briefcase, Award, MapPin, Phone, Mail, Target, Calendar } from "lucide-react";

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
    <div className="fixed inset-0 z-50 flex justify-end bg-foreground/30 backdrop-blur-sm">
      <button
        className="flex-1 cursor-default"
        onClick={onClose}
        type="button"
      />
      <aside className="h-full w-full max-w-2xl overflow-y-auto bg-card shadow-2xl">
        <div className="sticky top-0 z-10 border-b border-border bg-card/95 px-6 py-4 backdrop-blur-sm">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                Resume Detail
              </p>
              <h3 className="mt-1 text-2xl font-semibold tracking-tight text-foreground">
                {parsed?.name || resume?.file_name || "候选人详情"}
              </h3>
              <p className="mt-1 text-sm text-muted-foreground">
                {parsed?.summary || resume?.parse_error}
              </p>
            </div>
            <button
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-border text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              onClick={onClose}
              type="button"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="px-6 py-6">
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-muted-foreground/30 border-t-muted-foreground" />
              正在加载候选人详情...
            </div>
          ) : null}
          {error ? (
            <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600 dark:bg-red-500/10 dark:text-red-400">
              {error}
            </div>
          ) : null}

          {parsed ? (
            <div className="space-y-6">
              {/* 基础信息 */}
              <section className="rounded-xl border border-border bg-background p-5">
                <div className="mb-4 flex items-center gap-2">
                  <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary/10">
                    <Target className="h-3.5 w-3.5 text-primary" />
                  </div>
                  <h4 className="text-sm font-semibold uppercase tracking-[0.15em] text-muted-foreground">
                    基础信息
                  </h4>
                </div>
                <div className="grid gap-4 text-sm md:grid-cols-2">
                  <Info label="姓名" value={parsed.name} icon={<Target className="h-3.5 w-3.5" />} />
                  <Info label="电话" value={parsed.phone} icon={<Phone className="h-3.5 w-3.5" />} />
                  <Info label="邮箱" value={parsed.email} icon={<Mail className="h-3.5 w-3.5" />} />
                  <Info label="城市" value={parsed.city} icon={<MapPin className="h-3.5 w-3.5" />} />
                  <Info label="求职意向" value={parsed.job_intention} icon={<Briefcase className="h-3.5 w-3.5" />} />
                  <Info label="最高学历" value={parsed.highest_degree} icon={<GraduationCap className="h-3.5 w-3.5" />} />
                  <Info
                    label="工作年限"
                    value={
                      parsed.work_years != null
                        ? `${parsed.work_years} 年`
                        : undefined
                    }
                    icon={<Calendar className="h-3.5 w-3.5" />}
                  />
                </div>
              </section>

              {/* 技能与证书 */}
              <section className="rounded-xl border border-border bg-background p-5">
                <div className="mb-4 flex items-center gap-2">
                  <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary/10">
                    <Award className="h-3.5 w-3.5 text-primary" />
                  </div>
                  <h4 className="text-sm font-semibold uppercase tracking-[0.15em] text-muted-foreground">
                    技能与证书
                  </h4>
                </div>
                <div className="flex flex-wrap gap-2">
                  {(parsed.skills || []).map((skill) => (
                    <span
                      key={skill}
                      className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary transition-colors hover:bg-primary hover:text-primary-foreground"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
                {(parsed.certifications || []).length > 0 ? (
                  <p className="mt-4 text-sm text-muted-foreground">
                    证书：{parsed.certifications?.join("；")}
                  </p>
                ) : null}
              </section>

              {/* 教育经历 */}
              {(parsed.education || []).length > 0 ? (
                <section className="rounded-xl border border-border bg-background p-5">
                  <div className="mb-4 flex items-center gap-2">
                    <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary/10">
                      <GraduationCap className="h-3.5 w-3.5 text-primary" />
                    </div>
                    <h4 className="text-sm font-semibold uppercase tracking-[0.15em] text-muted-foreground">
                      教育经历
                    </h4>
                  </div>
                  <div className="space-y-3">
                    {parsed.education?.map((item, index) => (
                      <div
                        key={`${item.school}-${index}`}
                        className="rounded-xl border border-border bg-secondary/50 p-4"
                      >
                        <p className="font-medium text-foreground">
                          {item.school}
                        </p>
                        <p className="mt-1 text-sm text-muted-foreground">
                          {item.degree} / {item.major}
                        </p>
                        <p className="mt-1 text-xs text-muted-foreground/70">
                          {item.start_date || "未知"} -{" "}
                          {item.end_date || "未知"}
                        </p>
                      </div>
                    ))}
                  </div>
                </section>
              ) : null}

              {/* 工作经历 */}
              {(parsed.work_experience || []).length > 0 ? (
                <section className="rounded-xl border border-border bg-background p-5">
                  <div className="mb-4 flex items-center gap-2">
                    <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary/10">
                      <Briefcase className="h-3.5 w-3.5 text-primary" />
                    </div>
                    <h4 className="text-sm font-semibold uppercase tracking-[0.15em] text-muted-foreground">
                      工作经历
                    </h4>
                  </div>
                  <div className="space-y-4">
                    {parsed.work_experience?.map((item, index) => (
                      <div
                        key={`${item.company}-${index}`}
                        className="rounded-xl border border-border bg-secondary/50 p-4"
                      >
                        <p className="font-medium text-foreground">
                          {item.company} / {item.position}
                        </p>
                        <p className="mt-1 text-xs text-muted-foreground/70">
                          {item.duration}
                        </p>
                        {item.responsibilities?.length ? (
                          <div className="mt-3">
                            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                              职责
                            </p>
                            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                              {item.responsibilities.map((entry, entryIndex) => (
                                <li key={`${entryIndex}-${entry}`}>{entry}</li>
                              ))}
                            </ul>
                          </div>
                        ) : null}
                        {item.achievements?.length ? (
                          <div className="mt-3">
                            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                              成果
                            </p>
                            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
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
        </div>
      </aside>
    </div>
  );
}

function Info({
  label,
  value,
  icon,
}: {
  label: string;
  value?: string | null;
  icon?: ReactNode;
}) {
  return (
    <div className="flex items-start gap-2">
      {icon ? (
        <span className="mt-0.5 text-muted-foreground/60">{icon}</span>
      ) : null}
      <div>
        <p className="text-xs font-medium uppercase tracking-[0.15em] text-muted-foreground">
          {label}
        </p>
        <p className="mt-0.5 font-medium text-foreground">
          {value || "未填写"}
        </p>
      </div>
    </div>
  );
}
