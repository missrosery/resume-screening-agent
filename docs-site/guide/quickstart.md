# 快速开始

本页用于在本地启动 Resume Screening Agent，并跑通一条最小业务链路。

## 环境要求

- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- pgvector 扩展
- DashScope API Key

如果只想快速复现生产环境，可以优先使用 Docker Compose。

## 克隆项目

```bash
git clone https://github.com/missrosery/resume-screening-agent.git
cd resume-screening-agent
```

## 配置后端环境变量

复制示例文件：

```bash
cp backend/.env.example backend/.env
```

核心变量如下：

```ini
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/resume_screener
SYNC_DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/resume_screener
DASHSCOPE_API_KEY=your_dashscope_api_key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
EMBEDDING_MODEL=text-embedding-v4
UPLOAD_DIR=./uploads
CORS_ORIGINS=http://localhost:3000
VECTOR_COLLECTION_NAME=resume_documents
VECTOR_RECALL_K=15
RERANK_TOP_N=5
```

## 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端启动后访问：

```bash
curl http://localhost:8000/health
```

期望返回：

```json
{"status":"ok"}
```

## 启动前端

```bash
cd frontend
npm install
npm run dev
```

打开：

```text
http://localhost:3000
```

## 验证主流程

1. 创建岗位。
2. 上传 PDF 或 DOCX 简历。
3. 等待简历状态从 `parsing` 变为 `parsed`。
4. 输入筛选条件并点击筛选。
5. 选择候选人进行多人对比。
6. 选择候选人生成面试题。
7. 进入 Agent 对话页面，尝试自然语言搜索或对比。

## 生产构建检查

本地发布前建议跑一次生产构建：

```bash
cd frontend
npm run build
```

这能提前发现 TypeScript、Next.js 构建和页面路由问题。
