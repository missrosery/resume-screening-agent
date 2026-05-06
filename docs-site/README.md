# Resume Screening Agent Docs

这是 Resume Screening Agent 的 VitePress 文档站。

## 本地预览

```bash
cd docs-site
npm install
npm run docs:dev
```

默认地址：

```text
http://localhost:5173/resume-screening-agent/
```

如果想在本地用根路径预览：

```bash
DOCS_BASE=/ npm run docs:dev
```

## 构建

```bash
npm run docs:build
```

构建产物位于：

```text
docs-site/.vitepress/dist
```

## GitHub Pages

如果部署到项目仓库的 GitHub Pages，默认 base 为：

```text
/resume-screening-agent/
```

如果部署到自定义域名根路径，可以设置：

```bash
DOCS_BASE=/ npm run docs:build
```
