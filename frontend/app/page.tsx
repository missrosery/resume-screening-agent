import Link from "next/link";

export default function HomePage() {
  return (
    <main className="grid gap-6 md:grid-cols-[1.4fr_1fr]">
      <section className="panel bg-gradient-to-br from-white to-teal-50">
        <p className="mb-3 text-sm uppercase tracking-[0.2em] text-slate-500">Project Demo</p>
        <h2 className="mb-4 text-4xl font-semibold leading-tight">
          面向校招求职包装的 AI 招聘助手
        </h2>
        <p className="max-w-2xl text-slate-600">
          支持岗位管理、简历上传、结构化解析、候选人推荐、候选人对比、面试题生成，以及基于自然语言的简版 Agent 调用。
        </p>
        <div className="mt-6 flex gap-3">
          <Link className="button" href="/positions">
            进入岗位管理
          </Link>
        </div>
      </section>
      <section className="panel">
        <h3 className="mb-4 text-xl font-semibold">亮点</h3>
        <ul className="space-y-3 text-sm text-slate-600">
          <li>LLM 结构化解析简历</li>
          <li>查询增强 + 向量召回 + LLM 精排</li>
          <li>自然语言触发搜索、对比、面试题生成</li>
          <li>流式展示 Agent 输出</li>
        </ul>
      </section>
    </main>
  );
}
