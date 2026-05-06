# 整体架构

Resume Screening Agent 采用前后端分离架构：

```text
Next.js Frontend
  |
  | HTTP / NDJSON Stream
  v
FastAPI Backend
  |
  | SQLAlchemy Async
  v
PostgreSQL + pgvector

FastAPI Backend
  |
  | OpenAI-compatible API
  v
DashScope / Qwen
```

## 模块划分

### Frontend

前端位于 `frontend/`：

- `app/`：Next.js App Router 页面。
- `components/`：岗位、简历、筛选、对比、Agent 对话等 UI 组件。
- `lib/api.ts`：后端 API 调用封装。
- `lib/stream.ts`：Agent 流式响应解析。
- `lib/types.ts`：前端类型定义。

### Backend

后端位于 `backend/app/`：

- `api/`：FastAPI 路由。
- `services/`：业务服务层。
- `rag/`：查询增强、向量检索、筛选排序。
- `agents/`：Agent 工具路由与流式输出。
- `models/`：数据库模型和 Pydantic Schema。
- `infrastructure/`：数据库、LLM、会话记忆等基础设施。

## 核心链路

### 简历处理

```text
上传文件
  -> 计算 file_hash 去重
  -> 保存文件
  -> 创建 parsing 状态记录
  -> 后台解析
  -> LLM 结构化解析
  -> 写入 PostgreSQL
  -> 写入 pgvector
```

### 筛选候选人

```text
岗位需求 / 自然语言查询
  -> 查询增强
  -> pgvector 向量召回
  -> 按 resume_id / file_hash 去重
  -> 学历 / 年限 / Agent 经验硬筛
  -> LLM 精排
  -> 输出匹配分、理由、短板
```

### Agent 对话

```text
用户消息
  -> LLM 判断工具
  -> 搜索 / 对比 / 出题
  -> NDJSON 流式输出
  -> 前端增量渲染
```

## 设计取舍

- 简历解析放在后台执行，避免批量上传时触发 Nginx 504。
- 数据库中保存结构化解析结果，后续对比和出题不重复读取原始 PDF。
- 向量库保存摘要和工作经历文本块，提高召回粒度。
- 候选人筛选输出可解释信息，方便人工复核。
