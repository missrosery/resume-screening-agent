import { defineConfig } from "vitepress";

export default defineConfig({
  title: "Resume Screening Agent",
  description: "AI 简历筛选 Agent 项目文档",
  base: process.env.DOCS_BASE ?? "/resume-screening-agent/",
  cleanUrls: true,
  lastUpdated: true,
  themeConfig: {
    logo: "/logo.svg",
    nav: [
      { text: "指南", link: "/guide/quickstart" },
      { text: "架构", link: "/architecture/overview" },
      { text: "功能", link: "/features/resume-upload" },
      { text: "GitHub", link: "https://github.com/missrosery/resume-screening-agent" }
    ],
    sidebar: [
      {
        text: "开始",
        items: [
          { text: "项目概览", link: "/" },
          { text: "快速开始", link: "/guide/quickstart" },
          { text: "部署运维", link: "/guide/deployment" },
          { text: "常见问题", link: "/guide/troubleshooting" }
        ]
      },
      {
        text: "系统设计",
        items: [
          { text: "整体架构", link: "/architecture/overview" },
          { text: "数据流", link: "/architecture/data-flow" },
          { text: "API 参考", link: "/architecture/api" },
          { text: "数据模型", link: "/architecture/database" }
        ]
      },
      {
        text: "核心功能",
        items: [
          { text: "简历上传", link: "/features/resume-upload" },
          { text: "简历解析", link: "/features/resume-parsing" },
          { text: "RAG 筛选", link: "/features/rag-screening" },
          { text: "候选人对比", link: "/features/compare" },
          { text: "面试题生成", link: "/features/interview-questions" },
          { text: "Agent 对话", link: "/features/agent-chat" },
          { text: "评估测试", link: "/features/evaluation" }
        ]
      }
    ],
    socialLinks: [
      { icon: "github", link: "https://github.com/missrosery/resume-screening-agent" }
    ],
    outline: {
      level: [2, 3],
      label: "本页目录"
    },
    search: {
      provider: "local"
    },
    docFooter: {
      prev: "上一页",
      next: "下一页"
    },
    lastUpdated: {
      text: "最后更新",
      formatOptions: {
        dateStyle: "medium",
        timeStyle: "short"
      }
    }
  }
});
