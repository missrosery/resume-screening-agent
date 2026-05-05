import Link from "next/link";
import type { ReactNode } from "react";
import { Sparkles, FileText, MessageSquare, Zap } from "lucide-react";

export default function HomePage() {
  return (
    <main className="relative overflow-hidden rounded-3xl border border-border bg-card shadow-elevated">
      {/* 几何背景 */}
      <div className="absolute inset-0 overflow-hidden rounded-3xl">
        <div className="absolute -left-20 -top-20 h-72 w-72 rounded-full bg-indigo-400/10 blur-3xl animate-float" />
        <div className="absolute -right-20 top-40 h-96 w-96 rounded-full bg-violet-400/10 blur-3xl animate-float-delayed" />
        <div className="absolute bottom-0 left-1/3 h-64 w-64 rounded-full bg-indigo-300/10 blur-3xl animate-float-slow" />
      </div>

      <div className="relative grid gap-8 p-8 md:grid-cols-[1.4fr_1fr] md:p-12">
        <section className="flex flex-col justify-center">
          <div className="inline-flex w-fit items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-medium text-primary">
            <Sparkles className="h-3.5 w-3.5" />
            Project Demo
          </div>
          <h2 className="mt-6 text-4xl font-semibold leading-tight tracking-tight text-foreground md:text-5xl">
            面向校招智能筛选的
            <br />
            <span className="text-primary">AI 招聘助手</span>
          </h2>
          <p className="mt-5 max-w-lg text-base leading-relaxed text-muted-foreground">
            支持岗位管理、简历上传、结构化解析、候选人推荐、候选人对比、面试题生成，以及基于自然语言的简版 Agent 调用。
          </p>
          <div className="mt-8 flex gap-3">
            <Link className="button" href="/positions">
              进入岗位管理
            </Link>
          </div>
        </section>

        <section className="flex flex-col justify-center">
          <div className="space-y-4">
            <FeatureCard
              icon={<FileText className="h-5 w-5" />}
              title="LLM 结构化解析简历"
              description="自动提取教育、技能、工作经历等关键信息"
            />
            <FeatureCard
              icon={<Zap className="h-5 w-5" />}
              title="查询增强 + 向量召回 + LLM 精排"
              description="多阶段智能检索，精准匹配候选人"
            />
            <FeatureCard
              icon={<MessageSquare className="h-5 w-5" />}
              title="自然语言触发搜索、对比、面试题生成"
              description="一句话完成复杂招聘流程"
            />
            <FeatureCard
              icon={<Sparkles className="h-5 w-5" />}
              title="流式展示 Agent 输出"
              description="实时查看 AI 思考与执行过程"
            />
          </div>
        </section>
      </div>
    </main>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="group flex items-start gap-4 rounded-xl border border-border bg-card/60 p-4 backdrop-blur-sm transition-all duration-200 hover:border-primary/30 hover:bg-card hover:shadow-elevated">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
        {icon}
      </div>
      <div>
        <h3 className="font-medium text-foreground">{title}</h3>
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}
