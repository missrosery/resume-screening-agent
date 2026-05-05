"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  Upload,
  Search,
  GitCompare,
  HelpCircle,
  FileText,
  Trash2,
  Eye,
  MessageSquarePlus,
  Sparkles,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Clock,
  X,
  User,
} from "lucide-react";

import { ResumeDetailDrawer } from "@/components/ResumeDetailDrawer";
import { api } from "@/lib/api";
import {
  InterviewQuestionGroup,
  Position,
  RankedResume,
  Resume,
} from "@/lib/types";

export function PositionDetail({ positionId }: { positionId: string }) {
  const router = useRouter();
  const sessionRequestRef = useRef<Promise<string> | null>(null);
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
  const [isOpeningAgent, setIsOpeningAgent] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [latestResumeIds, setLatestResumeIds] = useState<string[]>([]);
  const [detailResumeId, setDetailResumeId] = useState<string | null>(null);
  const [error, setError] = useState("");

  const resumeStatusMeta = useMemo(
    () => ({
      parsed:
        "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400",
      parsing:
        "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400",
      failed:
        "bg-red-50 text-red-700 dark:bg-red-500/10 dark:text-red-400",
      pending: "bg-muted text-muted-foreground",
    }),
    [],
  );

  const candidateResumes = useMemo(
    () =>
      resumes.filter(
        (resume) => resume.parse_status === "parsed" && resume.parsed_data?.name,
      ),
    [resumes],
  );

  const ensureSession = useCallback(async () => {
    if (sessionRequestRef.current) {
      return sessionRequestRef.current;
    }

    sessionRequestRef.current = api
      .createSession(positionId, "Main Session")
      .then((session) => {
        setSessionId(session.id);
        return session.id;
      })
      .catch((err) => {
        sessionRequestRef.current = null;
        throw err;
      });

    return sessionRequestRef.current;
  }, [positionId]);

  const prefetchAgentRoute = useCallback(
    (id: string) => {
      router.prefetch(`/screening/${id}`);
    },
    [router],
  );

  const load = useCallback(async () => {
    try {
      const [positionData, resumeData, preparedSessionId] = await Promise.all([
        api.getPosition(positionId),
        api.listResumes(positionId),
        ensureSession(),
      ]);
      setPosition(positionData);
      setResumes(resumeData);
      prefetchAgentRoute(preparedSessionId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    }
  }, [ensureSession, positionId, prefetchAgentRoute]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (sessionId) {
      prefetchAgentRoute(sessionId);
    }
  }, [prefetchAgentRoute, sessionId]);

  useEffect(() => {
    setIsOpeningAgent(false);
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
    setResults((current) =>
      current.filter((item) => item.resume_id !== resumeId),
    );
    if (compareA === resumeId) setCompareA("");
    if (compareB === resumeId) setCompareB("");
    if (questionResumeId === resumeId) {
      setQuestionResumeId("");
      setQuestionGroups([]);
    }
    if (detailResumeId === resumeId) setDetailResumeId(null);
    setUploadMessage(
      `已删除简历：${removed?.parsed_data?.name || removed?.file_name || resumeId}`,
    );

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
        {/* 岗位头部 */}
        <section className="panel">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-primary" />
                <p className="text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">
                  岗位详情
                </p>
              </div>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">
                {position?.title ?? "Loading..."}
              </h2>
              <p className="mt-2 max-w-3xl text-sm leading-relaxed text-muted-foreground">
                {position?.requirements}
              </p>
            </div>
            {sessionId ? (
              <Link
                className="button shrink-0"
                href={`/screening/${sessionId}`}
                onClick={() => setIsOpeningAgent(true)}
                onFocus={() => prefetchAgentRoute(sessionId)}
                onMouseEnter={() => prefetchAgentRoute(sessionId)}
                prefetch
              >
                {isOpeningAgent ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <MessageSquarePlus className="mr-2 h-4 w-4" />
                )}
                {isOpeningAgent ? "打开中..." : "进入 Agent 对话"}
              </Link>
            ) : null}
          </div>
        </section>

        {/* 上传 + 筛选 */}
        <section className="grid gap-6 md:grid-cols-[1fr_1.2fr]">
          {/* 左侧：上传简历 */}
          <div className="panel">
            <div className="mb-4 flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Upload className="h-4 w-4" />
              </div>
              <h3 className="text-lg font-semibold text-foreground">
                上传简历
              </h3>
            </div>
            <form className="space-y-3" onSubmit={handleUpload}>
              <input
                className="input cursor-pointer file:mr-3 file:rounded-lg file:border-0 file:bg-primary/10 file:px-3 file:py-1 file:text-xs file:font-medium file:text-primary hover:file:bg-primary/20"
                multiple
                type="file"
                accept=".pdf,.docx"
                onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
              />
              <button className="button w-full" disabled={isUploading} type="submit">
                {isUploading ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    上传中...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Upload className="h-4 w-4" />
                    上传并解析
                  </span>
                )}
              </button>
            </form>
            {uploadMessage ? (
              <div className="mt-3 flex items-start gap-2 rounded-xl bg-secondary px-4 py-3 text-sm text-secondary-foreground">
                <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                {uploadMessage}
              </div>
            ) : null}
            <div className="mt-5 space-y-3">
              {resumes.map((resume) => (
                <div
                  key={resume.id}
                  className={`group rounded-xl border p-3 transition-all duration-200 ${
                    latestResumeIds.includes(resume.id)
                      ? "border-primary bg-primary/5"
                      : "border-border bg-background hover:border-primary/30 hover:shadow-card"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                        <strong className="truncate text-sm font-medium text-foreground">
                          {resume.file_name}
                        </strong>
                      </div>
                      <p className="mt-2 text-sm text-muted-foreground">
                        {resume.parsed_data?.summary ||
                          resume.parse_error ||
                          "等待解析结果"}
                      </p>
                      {latestResumeIds.includes(resume.id) ? (
                        <p className="mt-2 text-xs font-semibold uppercase tracking-[0.2em] text-primary">
                          latest result
                        </p>
                      ) : null}
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <div className="flex items-center gap-2">
                        {resume.duplicate ? (
                          <span className="badge bg-sky-50 text-sky-700 dark:bg-sky-500/10 dark:text-sky-400">
                            duplicate reused
                          </span>
                        ) : null}
                        <span
                          className={`badge ${
                            resumeStatusMeta[
                              resume.parse_status as keyof typeof resumeStatusMeta
                            ] ?? "bg-muted text-muted-foreground"
                          }`}
                        >
                          {resume.parse_status === "parsed" && (
                            <CheckCircle2 className="mr-1 h-3 w-3" />
                          )}
                          {resume.parse_status === "parsing" && (
                            <Clock className="mr-1 h-3 w-3" />
                          )}
                          {resume.parse_status === "failed" && (
                            <X className="mr-1 h-3 w-3" />
                          )}
                          {resume.parse_status}
                        </span>
                      </div>
                      <div className="flex gap-3 text-xs">
                        {resume.parse_status === "parsed" ? (
                          <button
                            className="flex items-center gap-1 text-muted-foreground transition-colors hover:text-primary"
                            type="button"
                            onClick={() => setDetailResumeId(resume.id)}
                          >
                            <Eye className="h-3.5 w-3.5" />
                            查看详情
                          </button>
                        ) : null}
                        <button
                          className="flex items-center gap-1 text-red-600 transition-colors hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                          type="button"
                          onClick={() => handleDeleteResume(resume.id)}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                          删除
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 右侧：候选人筛选 */}
          <div className="panel">
            <div className="mb-4 flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Search className="h-4 w-4" />
              </div>
              <h3 className="text-lg font-semibold text-foreground">
                候选人筛选
              </h3>
            </div>
            <form className="space-y-3" onSubmit={handleScreen}>
              <textarea
                className="input min-h-32"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="输入岗位需求或筛选条件"
              />
              <button className="button w-full" disabled={isScreening} type="submit">
                {isScreening ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    筛选中...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Search className="h-4 w-4" />
                    开始筛选
                  </span>
                )}
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
                <div
                  key={item.resume_id}
                  className="group rounded-xl border border-border bg-background p-4 transition-all duration-200 hover:border-primary/30 hover:shadow-card"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <User className="h-4 w-4 text-muted-foreground" />
                      <h4 className="font-semibold text-foreground">
                        {item.name}
                      </h4>
                    </div>
                    <span className="rounded-full bg-indigo-50 px-3 py-1 text-sm font-semibold text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-400">
                      {item.match_score}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">
                    学历 {item.highest_degree || "未知"} / 工作年限{" "}
                    {item.work_years ?? "未知"}
                  </p>
                  <p className="mt-2 text-sm text-foreground">
                    {item.match_reasons.join("；")}
                  </p>
                  <p className="mt-2 text-sm text-amber-700 dark:text-amber-400">
                    {item.weaknesses.join("；")}
                  </p>
                  <div className="mt-4 flex flex-wrap gap-3 text-sm">
                    <button
                      className="flex items-center gap-1 text-muted-foreground transition-colors hover:text-primary"
                      type="button"
                      onClick={() => setDetailResumeId(item.resume_id)}
                    >
                      <Eye className="h-3.5 w-3.5" />
                      查看详情
                    </button>
                    <button
                      className="flex items-center gap-1 text-muted-foreground transition-colors hover:text-primary"
                      type="button"
                      onClick={() => handlePickForCompare(item.resume_id)}
                    >
                      <GitCompare className="h-3.5 w-3.5" />
                      加入对比
                    </button>
                    <button
                      className="flex items-center gap-1 text-muted-foreground transition-colors hover:text-primary"
                      type="button"
                      onClick={() => void handleQuickQuestions(item.resume_id)}
                    >
                      <HelpCircle className="h-3.5 w-3.5" />
                      直接出题
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* 对比 + 面试题 */}
        <section className="grid gap-6 md:grid-cols-2">
          <div className="panel">
            <div className="mb-4 flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <GitCompare className="h-4 w-4" />
              </div>
              <h3 className="text-lg font-semibold text-foreground">
                候选人对比
              </h3>
            </div>
            <div className="space-y-3">
              <select
                className="input"
                value={compareA}
                onChange={(e) => setCompareA(e.target.value)}
              >
                <option value="">选择候选人 A</option>
                {candidateResumes.map((resume) => (
                  <option key={resume.id} value={resume.id}>
                    {resume.parsed_data?.name || resume.file_name}
                  </option>
                ))}
              </select>
              <select
                className="input"
                value={compareB}
                onChange={(e) => setCompareB(e.target.value)}
              >
                <option value="">选择候选人 B</option>
                {candidateResumes.map((resume) => (
                  <option key={resume.id} value={resume.id}>
                    {resume.parsed_data?.name || resume.file_name}
                  </option>
                ))}
              </select>
              <button className="button w-full" type="button" onClick={handleCompare}>
                {isComparing ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    生成中...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <GitCompare className="h-4 w-4" />
                    生成对比结论
                  </span>
                )}
              </button>
              {isComparing ? (
                <StatusCard
                  title="正在生成对比结论"
                  description="系统正在综合两位候选人的经历、技能和岗位匹配度。"
                />
              ) : null}
              {compareResult ? (
                <div className="mt-3 rounded-xl border border-border bg-secondary/50 p-4">
                  <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">
                    {compareResult}
                  </p>
                </div>
              ) : null}
            </div>
          </div>

          <div className="panel">
            <div className="mb-4 flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <HelpCircle className="h-4 w-4" />
              </div>
              <h3 className="text-lg font-semibold text-foreground">
                面试题生成
              </h3>
            </div>
            <div className="space-y-3">
              <select
                className="input"
                value={questionResumeId}
                onChange={(e) => setQuestionResumeId(e.target.value)}
              >
                <option value="">选择候选人</option>
                {candidateResumes.map((resume) => (
                  <option key={resume.id} value={resume.id}>
                    {resume.parsed_data?.name || resume.file_name}
                  </option>
                ))}
              </select>
              <button
                className="button w-full"
                disabled={isGeneratingQuestions}
                type="button"
                onClick={handleQuestions}
              >
                {isGeneratingQuestions ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    生成中...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4" />
                    生成面试题
                  </span>
                )}
              </button>
              {isGeneratingQuestions ? (
                <StatusCard
                  title="正在生成分组面试题"
                  description="系统正在按技术深挖、项目复盘、行为判断三个维度组织问题。"
                />
              ) : null}
              <div className="space-y-4">
                {questionGroups.map((group) => (
                  <div
                    key={group.category}
                    className="rounded-xl border border-border bg-background p-4"
                  >
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                      {group.category}
                    </p>
                    <ol className="mt-3 space-y-2 text-sm text-foreground">
                      {group.questions.map((question, index) => (
                        <li key={`${group.category}-${index}`} className="flex gap-2">
                          <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
                            {index + 1}
                          </span>
                          <span className="text-muted-foreground">{question}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {error ? (
          <div className="flex items-center gap-2 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600 dark:bg-red-500/10 dark:text-red-400">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        ) : null}
      </main>

      <ResumeDetailDrawer
        open={Boolean(detailResumeId)}
        resumeId={detailResumeId}
        onClose={() => setDetailResumeId(null)}
      />
    </>
  );
}

function StatusCard({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="mt-4 rounded-xl border border-primary/20 bg-primary/5 p-4 dark:bg-primary/5">
      <div className="flex items-start gap-3">
        <div className="mt-1 h-2.5 w-2.5 rounded-full bg-primary animate-pulse-glow" />
        <div>
          <p className="text-sm font-medium text-foreground">{title}</p>
          <p className="mt-1 text-sm text-muted-foreground">{description}</p>
        </div>
      </div>
    </div>
  );
}
