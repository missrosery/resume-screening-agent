# 常见问题

## 上传多份简历出现 504

现象：

```html
504 Gateway Time-out
nginx/1.18.0
```

原因通常是上传请求里包含了耗时解析、LLM 调用和向量写入，超过 Nginx 超时时间。

当前实现已经改为：

1. 上传接口先保存文件并创建 `parsing` 记录。
2. HTTP 请求快速返回。
3. 后端后台逐份解析。
4. 前端轮询列表，自动更新 `parsed` 或 `failed` 状态。

## 简历状态是 parsed，但页面显示等待解析结果

原因是 `parsed_data.summary` 可能为空。前端已经做了兜底展示，会显示姓名、学历、年限、技能等结构化字段。

## 重复上传导致简历重复

系统使用文件内容的 SHA-256 hash 判断重复。为了防止并发请求同时插入，上传流程使用 PostgreSQL advisory lock 对同一岗位、同一 hash 做串行化处理。

如果历史数据已经重复，可以在前端逐个删除重复简历。删除接口会同步清理：

- `resumes`
- `screening_results`
- pgvector 中对应向量文档
- 上传目录中的文件

## 删除岗位后列表突然为空

如果后端日志出现 SQLAlchemy connection pool timeout，通常是删除流程占用连接太久或请求并发过多。当前删除流程已经把数据库删除和文件系统清理拆开，尽量提前释放数据库连接。

## 本地很慢，服务器较快

常见原因：

- 本地使用 `next dev`，首次打开页面会按路由编译。
- 本地到 DashScope 或数据库链路更慢。
- 本地有旧的 Node / Python / Uvicorn 进程残留。
- 生产环境已构建，Next.js 页面无需开发模式编译。

本地可用生产构建验证：

```bash
cd frontend
npm run build
npm run start
```

## 筛选结果不准确

排查顺序：

1. 简历是否 `parsed`。
2. `parsed_data` 中学历、年限、技能是否正确。
3. 向量文档是否写入成功。
4. 查询是否过于宽泛或过于口语化。
5. LLM 精排结果是否返回了 0 分候选人。
