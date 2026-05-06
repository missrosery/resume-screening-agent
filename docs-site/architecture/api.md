# API 参考

后端 API 基于 FastAPI，默认本地地址为：

```text
http://localhost:8000
```

生产环境通过 Nginx 代理到：

```text
/api
```

## Health

### GET `/health`

检查后端是否可用。

```json
{"status":"ok"}
```

## Positions

### POST `/positions`

创建岗位。

```json
{
  "title": "AI Agent 应用开发工程师",
  "department": "研发部",
  "requirements": "熟悉 Python、RAG、Agent 工具调用。"
}
```

### GET `/positions`

返回岗位列表。

### GET `/positions/{position_id}`

返回岗位详情。

### DELETE `/positions/{position_id}`

删除岗位及其关联简历、筛选结果、会话和向量文档。

## Resumes

### POST `/positions/{position_id}/resumes/upload`

批量上传简历。请求类型为 `multipart/form-data`。

返回值是简历记录列表。新上传的简历通常先返回 `parse_status: "parsing"`，后台解析完成后变为 `parsed`。

### GET `/positions/{position_id}/resumes`

返回某个岗位下的简历列表。

### GET `/resumes/{resume_id}`

返回单份简历详情。

### DELETE `/resumes/{resume_id}`

删除单份简历，同时清理筛选结果、向量文档和本地上传文件。

## Screening

### POST `/positions/{position_id}/screen`

筛选候选人。

```json
{
  "query": "找有 RAG 和 Agent 项目经验的候选人",
  "top_n": 5
}
```

### POST `/resumes/compare`

多人对比。

```json
{
  "resume_ids": [
    "resume-id-1",
    "resume-id-2",
    "resume-id-3"
  ],
  "criteria": "综合匹配度"
}
```

### POST `/resumes/{resume_id}/interview-questions`

基于候选人简历生成面试题。

## Agent

### POST `/positions/{position_id}/sessions`

创建 Agent 对话会话。

### POST `/sessions/{session_id}/chat`

发送 Agent 消息。响应为 NDJSON 流，每行是一个消息对象。

消息类型包括：

- `thinking`
- `tool_call`
- `resume_card`
- `text`
- `done`
- `error`
