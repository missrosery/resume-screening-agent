# 数据模型

系统主要使用 PostgreSQL 存储岗位、简历、会话和筛选结果，使用 pgvector 保存向量文档。

## job_positions

岗位表。

| 字段 | 说明 |
| --- | --- |
| `id` | 岗位 ID |
| `title` | 岗位名称 |
| `department` | 部门 |
| `requirements` | 岗位要求 |
| `created_at` | 创建时间 |

## resumes

简历表。

| 字段 | 说明 |
| --- | --- |
| `id` | 简历 ID |
| `position_id` | 所属岗位 |
| `file_name` | 原始文件名 |
| `file_hash` | 文件内容 SHA-256 |
| `file_path` | 服务端文件路径 |
| `file_type` | `pdf` 或 `docx` |
| `raw_text` | 提取出的原始文本 |
| `parse_status` | `pending` / `parsing` / `parsed` / `failed` |
| `parsed_data` | LLM 结构化解析结果 |
| `parse_error` | 解析失败原因 |
| `created_at` | 创建时间 |

## screening_sessions

Agent 对话会话表。

| 字段 | 说明 |
| --- | --- |
| `id` | 会话 ID |
| `position_id` | 绑定岗位 |
| `title` | 会话标题 |
| `created_at` | 创建时间 |

## screening_results

筛选结果表，当前主要用于预留落库和删除清理。

| 字段 | 说明 |
| --- | --- |
| `id` | 结果 ID |
| `session_id` | 关联会话 |
| `resume_id` | 关联简历 |
| `match_score` | 匹配分 |
| `match_reasons` | 匹配理由 |
| `weaknesses` | 风险或短板 |
| `created_at` | 创建时间 |

## langchain_pg_embedding

LangChain PGVector 自动维护的向量表。系统把 `resume_id` 和 `position_id` 写入 metadata，便于按岗位检索和删除时清理。

## 去重策略

系统通过 `position_id + file_hash` 判断同一岗位下是否重复上传同一份简历。

为防止并发上传时重复插入，后端使用 PostgreSQL advisory lock 对同一岗位、同一 hash 加锁。
