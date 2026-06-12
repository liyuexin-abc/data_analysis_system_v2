/**
 * MySQL 连接池配置
 */
const mysql = require('mysql2/promise');

const pool = mysql.createPool({
  host: process.env.DB_HOST || '127.0.0.1',
  port: Number(process.env.DB_PORT || 3306),
  user: process.env.DB_USER || 'kp_user',
  password: process.env.DB_PASSWORD || 'kp_pass_2026',
  database: process.env.DB_NAME || 'knowledge_platform',
  waitForConnections: true,
  connectionLimit: 10,
  charset: 'utf8mb4',
  namedPlaceholders: true,
  // JSON 字段自动解析由 mysql2 处理
});

module.exports = pool;
