/**
 * 际华国际知识平台 - Node.js 主服务
 * 端口: 8000
 * 职责: 知识对象 CRUD / 生命周期 / 图谱构建与查询 / 规则引擎 / 知识治理 / 业务数据查询
 * AI 能力(问数/归因/RAG) 通过 /api/ai 代理至 Python 服务(8100)
 */
const express = require('express');
const cors = require('cors');
const path = require('path');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = process.env.PORT || 8000;
const AI_BASE = process.env.AI_SERVICE_URL || 'http://127.0.0.1:8100';

app.use(cors());

// AI 服务代理(置于 body parser 之前，避免流被消费)
app.use('/api/ai', createProxyMiddleware({
  target: AI_BASE,
  changeOrigin: true,
  pathRewrite: { '^/': '/api/ai/' },
  proxyTimeout: 180000,
  timeout: 180000,
}));

app.use(express.json({ limit: '10mb' }));

// 健康检查
app.get('/api/health', (req, res) => res.json({ code: 0, message: 'ok', service: 'kp-backend-node', time: new Date().toISOString() }));

// 路由
app.use('/api/ontology', require('./routes/ontology'));
app.use('/api/graph', require('./routes/graph'));
app.use('/api', require('./routes/knowledge'));        // /terms /metrics /rules /methods /skills
app.use('/api/rag', require('./routes/document'));     // /rag/documents
app.use('/api/governance', require('./routes/governance'));
app.use('/api/biz', require('./routes/biz'));

// 前端静态文件(生产构建产物)
const distDir = path.join(__dirname, '../../frontend/dist');
app.use(express.static(distDir));
app.get(/^(?!\/api).*/, (req, res, next) => {
  res.sendFile(path.join(distDir, 'index.html'), (err) => { if (err) next(); });
});

// 统一错误处理
app.use((err, req, res, next) => {
  console.error('[ERROR]', req.method, req.path, err.message);
  res.status(err.status || 500).json({ code: 1, message: err.message || '服务器内部错误', data: null });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`知识平台主服务已启动: http://0.0.0.0:${PORT}`);
});
