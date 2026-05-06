---
layout: home

hero:
  name: Resume Screening Agent
  text: AI 简历筛选 Agent 项目文档
  tagline: 面向招聘场景的全栈 AI 应用，支持简历解析、RAG 筛选、候选人对比、面试题生成和 Agent 对话。
  actions:
    - theme: brand
      text: 快速开始
      link: /guide/quickstart
    - theme: alt
      text: 查看架构
      link: /architecture/overview

features:
  - title: 批量简历上传
    details: 支持 PDF / DOCX，基于文件 hash 去重，上传后进入后台解析队列。
  - title: LLM 结构化解析
    details: 提取姓名、学历、工作年限、技能、项目经历、摘要等结构化字段。
  - title: RAG 候选人筛选
    details: 查询增强、pgvector 向量召回、结构化硬筛、LLM 精排输出可解释结果。
  - title: 多人候选人对比
    details: 支持两人、三人或更多候选人对比，输出优势、风险和最终建议。
  - title: 面试题生成
    details: 基于结构化简历生成技术深挖、项目复盘、行为判断三类问题。
  - title: Agent 对话
    details: 通过自然语言触发搜索、对比、出题，并支持最近候选人引用。
---

## 项目定位

Resume Screening Agent 是一个面向招聘流程的 AI 辅助系统。它不是通用聊天机器人，而是围绕招聘筛选任务，把简历解析、语义检索、候选人排序、多人对比和面试准备串成一条完整链路。

系统的目标是让 HR、招聘负责人或技术面试官能够快速完成这些工作：

- 批量上传候选人简历。
- 自动解析简历中的结构化信息。
- 根据岗位需求或自然语言条件筛选候选人。
- 查看每位候选人的匹配理由和风险点。
- 对多位候选人做横向比较。
- 生成面试追问问题。
- 通过 Agent 对话继续推进筛选流程。

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | Next.js 14, React 18, TypeScript, Tailwind CSS |
| 后端 | FastAPI, SQLAlchemy Async |
| 数据库 | PostgreSQL, pgvector |
| AI 能力 | DashScope / Qwen, OpenAI-compatible SDK |
| 检索 | LangChain PGVector, Embedding |
| 部署 | Docker Compose, Nginx, Certbot |

## 文档导航

- [快速开始](/guide/quickstart)：本地启动前后端并完成第一轮验证。
- [整体架构](/architecture/overview)：了解系统模块和请求链路。
- [简历上传](/features/resume-upload)：文件保存、去重、后台解析和状态轮询。
- [RAG 筛选](/features/rag-screening)：查询增强、向量召回和 LLM 精排。
- [部署运维](/guide/deployment)：服务器、Docker、Nginx 和更新流程。
