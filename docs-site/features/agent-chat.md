# Agent 对话

Agent 对话提供自然语言入口，让用户不用手动点击每个功能，也可以完成搜索、对比和出题。

## 支持能力

- 自然语言搜索候选人。
- 对比候选人。
- 给候选人生成面试题。
- 引用最近推荐结果。

## 工具路由

Agent 不直接回答所有问题，而是先判断应该调用哪个工具：

- `search_resumes`
- `compare_resumes`
- `generate_interview_questions`

## 会话记忆

系统在内存中保存最近候选人列表和对比别名。

因此用户可以说：

```text
对比刚才前两个候选人
```

或：

```text
给第一个候选人生成面试题
```

## 流式响应

后端通过 NDJSON 流式返回消息，前端逐条渲染。

消息类型包括：

- `thinking`
- `tool_call`
- `resume_card`
- `text`
- `done`
- `error`
