# 简历解析

简历解析把非结构化 PDF / DOCX 转换为后续筛选、对比和出题可直接使用的结构化数据。

## 处理步骤

1. 提取原始文本。
2. 清理 NUL 字节和不可见控制字符。
3. 调用 LLM 输出结构化 JSON。
4. 保存 `raw_text` 和 `parsed_data`。
5. 构造向量检索文档。
6. 写入 pgvector。

## 结构化字段

`parsed_data` 主要包含：

- `name`
- `phone`
- `email`
- `city`
- `job_intention`
- `education`
- `highest_degree`
- `work_years`
- `work_experience`
- `skills`
- `certifications`
- `summary`

## 向量文档

系统不会直接把整份简历作为一个向量文档，而是把摘要、技能、工作经历等拆成更适合检索的文本块。

这样做的好处是：

- 召回粒度更细。
- 工作经历中的项目关键词更容易命中。
- 后续可以按 `position_id` 限定检索范围。

## 失败处理

如果某份简历解析失败，系统不会让整个批次失败，而是把该简历状态标记为 `failed`，并保存 `parse_error`。

前端会继续展示其他成功解析的简历。
