"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { ResumeDetailDrawer } from "@/components/ResumeDetailDrawer";
import { api } from "@/lib/api";
import { InterviewQuestionGroup, Position, RankedResume, Resume } from "@/lib/types";

export function PositionDetail({ positionId }: { positionId: string }) {
  const [position, setPosition] = useState<Position | null>(null);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<RankedResume[]>([]);
  const [files, setFiles] = useState<File[]>([]);
  const [sessionId, setSessionId] = useState<string>("");
  const [compareA, setCompareA] = useState("");
  const [compareB, setCompareB] = useState("");
  const [compareResult, setCompareResult] = useState("");
  const [questionResumeId, setQuestionResumeId] = useState("");
  const [questionGroups, setQuestionGroups] = useState<InterviewQuestionGroup[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isScreening, setIsScreening] = useState(false);
  const [isComparing, setIsComparing] = useState(false);
  const [isGeneratingQuestions, setIsGeneratingQuestions] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [latestResumeIds, setLatestResumeIds] = useState<string[]>([]);
  const [detailResumeId, setDetailResumeId] = useState<string | null>(null);
  const [error, setError] = useState("");

  const resumeStatusMeta = useMemo(
    () => ({
      parsed: "bg-emerald-50 text-emerald-700",
      parsing: "bg-amber-50 text-amber-700",
      failed: "bg-rose-50 text-rose-700",
      pending: "bg-slate-100 text-slate-700",
    }),
    [],
  );

  const candidateResumes = useMemo(
    () => resumes.filter((resume) => resume.parse_status === "parsed" && resume.parsed_data?.name),
    [resumes],
  );

  async function load() {
    try {
      const [positionData, resumeData] = await Promise.all([
        api.getPosition(positionId),
        api.listResumes(positionId),
      ]);
      setPosition(positionData);
      setResumes(resumeData);
      if (!sessionId) {
        const session = await api.createSession(positionId, "Main Session");
        setSessionId(session.id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    }
  }

  useEffect(() => {
    void load();
  }, [positionId]);

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (!files.length) {
      setError("请先选择至少一份 PDF 或 DOCX 简历");
      return;
    }

    setIsUploading(true);
    setUploadMessage(`正在上传并解析 ${files.length} 份简历，请等待...`);
    try {
      const uploaded = await api.uploadResumes(positionId, files);
      setFiles([]);
      setLatestResumeIds(uploaded.map((item) => item.id));
      const duplicateCount = uploaded.filter((item) => item.duplicate).length;
      setUploadMessage(
        duplicateCount > 0
          ? `上传完成，其中 ${duplicateCount} 份为重复简历，系统已直接复用已有解析结果。`
          : `上传完成，返回 ${uploaded.length} 份记录。`,
      );
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setUploadMessage("");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleScreen(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsScreening(true);
    setUploadMessage("正在筛选候选人，请等待检索和精排完成...");
    try {
      const data = await api.screenPosition(positionId, { query, top_n: 5 });
      setResults(data.items);
      setUploadMessage(`筛选完成，已返回 ${data.items.length} 位候选人。`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Screen failed");
      setUploadMessage("");
    } finally {
      setIsScreening(false);
    }
  }

  async function handleCompare() {
    setError("");
    setIsComparing(true);
    setUploadMessage("正在生成候选人对比结论，请等待...");
    try {
      const data = await api.compareResumes(compareA, compareB);
      setCompareResult(data.summary);
      setUploadMessage("候选人对比结论已生成。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Compare failed");
      setUploadMessage("");
    } finally {
      setIsComparing(false);
    }
  }

  async function handleQuestions() {
    setError("");
    setIsGeneratingQuestions(true);
    setUploadMessage("正在生成分组面试题，请等待...");
    try {
      const data = await api.interviewQuestions(questionResumeId);
      setQuestionGroups(data.groups);
      setUploadMessage("分组面试题已生成。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Question generation failed");
      setUploadMessage("");
    } finally {
      setIsGeneratingQuestions(false);
    }
  }

  async function handleDeleteResume(resumeId: string) {
    setError("");
    const removed = resumes.find((item) => item.id === resumeId);
    setResumes((current) => current.filter((item) => item.id !== resumeId));
    setLatestResumeIds((current) => current.filter((item) => item !== resumeId));
    setResults((current) => current.filter((item) => item.resume_id !== resumeId));
    if (compareA === resumeId) setCompareA("");
    if (compareB === resumeId) setCompareB("");
    if (questionResumeId === resumeId) {
      setQuestionResumeId("");
      setQuestionGroups([]);
    }
    if (detailResumeId === resumeId) setDetailResumeId(null);
    setUploadMessage(`已删除简历：${removed?.parsed_data?.name || removed?.file_name || resumeId}`);

    try {
      await api.deleteResume(resumeId);
    } catch (err) {
      if (removed) {
        setResumes((current) => [removed, ...current]);
      }
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  function handlePickForCompare(resumeId: string) {
    if (!compareA) {
      setCompareA(resumeId);
      setUploadMessage("已将该候选人设为对比对象 A。");
      return;
    }
    if (!compareB && compareA !== resumeId) {
      setCompareB(resumeId);
      setUploadMessage("已将该候选人设为对比对象 B。");
      return;
    }
    if (compareA === resumeId || compareB === resumeId) {
      setUploadMessage("该候选人已经在当前对比列表中。");
      return;
    }
    setCompareA(resumeId);
    setCompareB("");
    setUploadMessage("已重置对比选择，并将该候选人设为对比对象 A。");
  }

  async function handleQuickQuestions(resumeId: string) {
    setQuestionResumeId(resumeId);
    setError("");
    setIsGeneratingQuestions(true);
    setUploadMessage("正在为该候选人生成分组面试题，请等待...");
    try {
      const data = await api.interviewQuestions(resumeId);
      setQuestionGroups(data.groups);
      setUploadMessage("已为该候选人生成分组面试题。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Question generation failed");
      setUploadMessage("");
    } finally {
      setIsGeneratingQuestions(false);
    }
  }

  return (
    <>
      <main className="space-y-6">
        <section className="panel">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-2xl font-semibold">{position?.title ?? "Loading..."}</h2>
              <p className="mt-2 max-w-3xl text-sm text-slate-600">{position?.requirements}</p>
            </div>
            {sessionId ? (
              <Link className="button" href={`/screening/${sessionId}`}>
                进入 Agent 对话
              </Link>
            ) : null}
          </div>
        </section>

        <section className="grid gap-6 md:grid-cols-[1fr_1.2fr]">
          <div className="panel">
            <h3 className="mb-3 text-lg font-semibold">上传简历</h3>
            <form className="space-y-3" onSubmit={handleUpload}>
              <input
                className="input"
                multiple
                type="file"
                accept=".pdf,.docx"
                onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
              />
              <button className="button" disabled={isUploading} type="submit">
                {isUploading ? "上传中..." : "上传并解析"}
              </button>
            </form>
            {uploadMessage ? <p className="mt-3 text-sm text-slate-600">{uploadMessage}</p> : null}
            <div className="mt-5 space-y-3">
              {resumes.map((resume) => (
                <div
                  key={resume.id}
                  className={`rounded-xl border p-3 transition ${
                    latestResumeIds.includes(resume.id) ? "border-accent bg-teal-50/40" : "border-slate-200"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <strong>{resume.file_name}</strong>
                      <p className="mt-2 text-sm text-slate-600">
                        {resume.parsed_data?.summary || resume.parse_error || "等待解析结果"}
                      </p>
                      {latestResumeIds.includes(resume.id) ? (
                        <p className="mt-2 text-xs uppercase tracking-[0.2em] text-accent">latest result</p>
                      ) : null}
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <div className="flex items-center gap-2">
                        {resume.duplicate ? (
                          <span className="rounded-full bg-sky-50 px-2 py-1 text-xs text-sky-700">
                            duplicate reused
                          </span>
                        ) : null}
                        <span
                          className={`rounded-full px-2 py-1 text-xs ${
                            resumeStatusMeta[resume.parse_status as keyof typeof resumeStatusMeta] ??
                            "bg-slate-100 text-slate-700"
                          }`}
                        >
                          {resume.parse_status}
                        </span>
                      </div>
                      <div className="flex gap-3 text-xs">
                        {resume.parse_status === "parsed" ? (
                          <button
                            className="text-slate-600 hover:underline"
                            type="button"
                            onClick={() => setDetailResumeId(resume.id)}
                          >
                            查看详情
                          </button>
                        ) : null}
                        <button
                          className="text-rose-600 hover:underline"
                          type="button"
                          onClick={() => handleDeleteResume(resume.id)}
                        >
                          删除
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <h3 className="mb-3 text-lg font-semibold">候选人筛选</h3>
            <form className="space-y-3" onSubmit={handleScreen}>
              <textarea
                className="input min-h-32"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="输入岗位需求或筛选条件"
              />
              <button className="button" disabled={isScreening} type="submit">
                {isScreening ? "筛选中..." : "开始筛选"}
              </button>
            </form>
            {isScreening ? (
              <StatusCard
                title="正在筛选候选人"
                description="系统正在执行查询增强、向量召回和 LLM 精排，这一步通常需要几秒钟。"
              />
            ) : null}
            <div className="mt-5 space-y-3">
              {results.map((item) => (
                <div key={item.resume_id} className="rounded-xl border border-slate-200 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <h4 className="font-semibold">{item.name}</h4>
                    <div className="flex items-center gap-3">
                      <span className="rounded-full bg-teal-50 px-3 py-1 text-sm text-teal-700">
                        {item.match_score}
                      </span>
                    </div>
                  </div>
                  <p className="mt-2 text-sm text-slate-600">
                    学历 {item.highest_degree || "未知"} / 工作年限 {item.work_years ?? "未知"}
                  </p>
                  <p className="mt-2 text-sm text-slate-700">{item.match_reasons.join("；")}</p>
                  <p className="mt-2 text-sm text-amber-700">{item.weaknesses.join("；")}</p>
                  <div className="mt-4 flex flex-wrap gap-3 text-sm">
                    <button
                      className="text-slate-600 hover:underline"
                      type="button"
                      onClick={() => setDetailResumeId(item.resume_id)}
                    >
                      查看详情
                    </button>
                    <button
                      className="text-slate-600 hover:underline"
                      type="button"
                      onClick={() => handlePickForCompare(item.resume_id)}
                    >
                      加入对比
                    </button>
                    <button
                      className="text-slate-600 hover:underline"
                      type="button"
                      onClick={() => void handleQuickQuestions(item.resume_id)}
                    >
                      直接出题
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="grid gap-6 md:grid-cols-2">
          <div className="panel">
            <h3 className="mb-3 text-lg font-semibold">候选人对比</h3>
            <div className="space-y-3">
              <select className="input" value={compareA} onChange={(e) => setCompareA(e.target.value)}>
                <option value="">选择候选人 A</option>
                {candidateResumes.map((resume) => (
                  <option key={resume.id} value={resume.id}>
                    {resume.parsed_data?.name || resume.file_name}
                  </option>
                ))}
              </select>
              <select className="input" value={compareB} onChange={(e) => setCompareB(e.target.value)}>
                <option value="">选择候选人 B</option>
                {candidateResumes.map((resume) => (
                  <option key={resume.id} value={resume.id}>
                    {resume.parsed_data?.name || resume.file_name}
                  </option>
                ))}
              </select>
              <button className="button" type="button" onClick={handleCompare}>
                {isComparing ? "生成中..." : "生成对比结论"}
              </button>
              {isComparing ? (
                <StatusCard
                  title="正在生成对比结论"
                  description="系统正在综合两位候选人的经历、技能和岗位匹配度。"
                />
              ) : null}
              {compareResult ? <p className="whitespace-pre-wrap text-sm text-slate-700">{compareResult}</p> : null}
            </div>
          </div>

          <div className="panel">
            <h3 className="mb-3 text-lg font-semibold">面试题生成</h3>
            <div className="space-y-3">
              <select className="input" value={questionResumeId} onChange={(e) => setQuestionResumeId(e.target.value)}>
                <option value="">选择候选人</option>
                {candidateResumes.map((resume) => (
                  <option key={resume.id} value={resume.id}>
                    {resume.parsed_data?.name || resume.file_name}
                  </option>
                ))}
              </select>
              <button className="button" disabled={isGeneratingQuestions} type="button" onClick={handleQuestions}>
                {isGeneratingQuestions ? "生成中..." : "生成面试题"}
              </button>
              {isGeneratingQuestions ? (
                <StatusCard
                  title="正在生成分组面试题"
                  description="系统正在按技术深挖、项目复盘、行为判断三个维度组织问题。"
                />
              ) : null}
              <div className="space-y-4">
                {questionGroups.map((group) => (
                  <div key={group.category} className="rounded-xl border border-slate-200 p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{group.category}</p>
                    <ol className="mt-3 space-y-2 text-sm text-slate-700">
                      {group.questions.map((question, index) => (
                        <li key={`${group.category}-${index}`}>{index + 1}. {question}</li>
                      ))}
                    </ol>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {error ? <p className="text-sm text-red-600">{error}</p> : null}
      </main>

      <ResumeDetailDrawer
        open={Boolean(detailResumeId)}
        resumeId={detailResumeId}
        onClose={() => setDetailResumeId(null)}
      />
    </>
  );
}

function StatusCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="mt-4 rounded-xl border border-teal-100 bg-teal-50/70 p-4">
      <div className="flex items-start gap-3">
        <div className="mt-1 h-2.5 w-2.5 rounded-full bg-teal-600 animate-pulse" />
        <div>
          <p className="text-sm font-medium text-teal-900">{title}</p>
          <p className="mt-1 text-sm text-teal-800/80">{description}</p>
        </div>
      </div>
    </div>
  );
}
