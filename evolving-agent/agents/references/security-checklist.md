# 安全检查清单

代码审查时，使用此清单识别安全漏洞和风险。

---

## 1. Input/Output 安全

### SQL 注入 (SQL Injection)

- [ ] 是否使用参数化查询而非字符串拼接？
  ```python
  # ❌ SQL 注入风险
  query = f"SELECT * FROM users WHERE id = {user_input}"
  
  # ✅ 参数化查询
  cursor.execute("SELECT * FROM users WHERE id = ?", (user_input,))
  ```

- [ ] ORM 使用是否正确？是否避免了原生 SQL 拼接？

### XSS (跨站脚本攻击)

- [ ] 用户输入是否在输出前进行了转义/编码？
  ```javascript
  // ❌ XSS 风险
  element.innerHTML = userInput
  
  // ✅ 安全输出
  element.textContent = userInput
  ```

- [ ] 是否使用了框架的自动转义机制（如 React 的 JSX、Vue 的模板）？

### SSRF (服务器端请求伪造)

- [ ] 是否验证了用户提供的 URL？
  ```python
  # ❌ SSRF 风险
  url = request.args.get('url')
  response = requests.get(url)
  
  # ✅ URL 白名单验证
  from urllib.parse import urlparse
  allowed_domains = ['api.example.com', 'cdn.example.com']
  parsed = urlparse(url)
  if parsed.netloc not in allowed_domains:
      raise ValueError("Invalid URL")
  ```

- [ ] 是否限制了请求协议（仅允许 http/https）？

### Path Traversal (路径穿越)

- [ ] 文件路径是否包含用户输入？
  ```python
  # ❌ 路径穿越风险
  file_path = f"/uploads/{user_input}"
  
  # ✅ 路径规范化
  import os
  base_dir = "/uploads"
  file_path = os.path.realpath(os.path.join(base_dir, user_input))
  if not file_path.startswith(base_dir):
      raise ValueError("Invalid path")
  ```

### Prototype Pollution (原型污染)

- [ ] 是否对用户输入的对象进行深拷贝时验证了键名？
  ```javascript
  // ❌ 原型污染风险
  const config = { ...userInput }
  
  // ✅ 白名单键名
  const allowedKeys = ['name', 'email']
  const config = {}
  for (const key of allowedKeys) {
      if (key in userInput) {
          config[key] = userInput[key]
      }
  }
  ```

---

## 2. 认证与授权 (AuthN/AuthZ)

### IDOR (不安全的直接对象引用)

- [ ] 是否验证了当前用户有权访问请求的资源？
  ```python
  # ❌ IDOR 风险
  order = Order.query.get(request.args.get('order_id'))
  
  # ✅ 所有权验证
  order = Order.query.get(request.args.get('order_id'))
  if order.user_id != current_user.id:
      raise ForbiddenError()
  ```

### RBAC (基于角色的访问控制)

- [ ] 是否在路由/函数级别检查用户角色？
  ```python
  # ❌ 缺少权限检查
  @app.route('/admin/users')
  def list_users():
      return User.query.all()
  
  # ✅ 角色检查
  @app.route('/admin/users')
  @require_role('admin')
  def list_users():
      return User.query.all()
  ```

### Session 管理

- [ ] Session ID 是否使用加密安全的随机数生成？
- [ ] Session 是否设置了合理的过期时间？
- [ ] 是否在敏感操作（修改密码、邮箱）后重新生成 Session？

---

## 3. JWT 安全

### Algorithm Confusion (算法混淆攻击)

- [ ] 是否强制指定算法而非使用 `none` 或允许切换？
  ```python
  # ❌ 算法混淆风险
  decoded = jwt.decode(token, key, algorithms=['HS256', 'RS256', 'none'])
  
  # ✅ 强制单一算法
  decoded = jwt.decode(token, key, algorithms=['HS256'])
  ```

### 过期验证 (exp claim)

- [ ] 是否验证了 `exp` 声明？
  ```python
  # ❌ 缺少过期验证
  decoded = jwt.decode(token, verify=False)
  
  # ✅ 验证过期时间
  decoded = jwt.decode(token, key, algorithms=['HS256'])
  # 默认会验证 exp
  ```

### Payload 敏感数据

- [ ] JWT payload 是否包含敏感信息（密码、密钥）？
  - ⚠️ JWT 是 base64 编码，非加密，任何人都能解码读取

---

## 4. Race Conditions (竞态条件)

### TOCTOU (Time-of-Check-Time-of-Use)

- [ ] 是否在检查后、使用前资源状态可能被修改？
  ```python
  # ❌ TOCTOU 漏洞
  if os.path.exists(file_path):
      # 文件可能在此刻被删除
      with open(file_path) as f:
          content = f.read()
  
  # ✅ 原子操作
  try:
      with open(file_path) as f:
          content = f.read()
  except FileNotFoundError:
      pass
  ```

### Check-Then-Act

- [ ] 是否存在"检查-执行"分离导致的问题？
  ```python
  # ❌ Check-Then-Act 漏洞
  if user.balance >= amount:
      user.balance -= amount  # 余额可能在此刻被其他请求修改
  
  # ✅ 数据库原子操作
  UPDATE users SET balance = balance - ? WHERE id = ? AND balance >= ?
  ```

### 数据库并发

- [ ] 是否使用了事务（Transaction）保证原子性？
- [ ] 是否使用了乐观锁（version 字段）或悲观锁（SELECT FOR UPDATE）？

### Shared State

- [ ] 共享变量是否使用了锁保护？
  ```python
  # ❌ 竞态条件
  counter += 1
  
  # ✅ 线程安全
  import threading
  lock = threading.Lock()
  with lock:
      counter += 1
  ```

---

## 5. Secrets & PII (敏感信息)

### 硬编码密钥

- [ ] 代码中是否包含硬编码的密钥/密码/Token？
  ```python
  # ❌ 硬编码密钥
  API_KEY = "sk-1234567890abcdef"
  
  # ✅ 环境变量
  import os
  API_KEY = os.environ.get('API_KEY')
  ```

### 日志泄露

- [ ] 日志是否记录了敏感信息（密码、Token、PII）？
  ```python
  # ❌ 日志泄露
  logger.info(f"User login: {username}, password: {password}")
  
  # ✅ 脱敏日志
  logger.info(f"User login: {username}")
  ```

### Git History

- [ ] 是否有敏感文件被提交到 Git？
  - 检查 `.gitignore` 是否包含 `.env`, `credentials.json`, `id_rsa` 等

---

## 6. 运行时风险

### 无限循环

- [ ] 是否有未设置终止条件的循环？
  ```python
  # ❌ 无限循环风险
  while True:
      process_data()
  
  # ✅ 添加超时或计数器
  max_iterations = 1000
  count = 0
  while count < max_iterations:
      process_data()
      count += 1
  ```

### 缺少超时

- [ ] 网络请求/数据库查询是否设置了超时？
  ```python
  # ❌ 缺少超时
  response = requests.get(url)
  
  # ✅ 设置超时
  response = requests.get(url, timeout=30)
  ```

### ReDoS (正则表达式拒绝服务)

- [ ] 正则表达式是否包含重复量词嵌套？
  ```python
  # ❌ ReDoS 风险
  pattern = r'^(a+)+$'  # 输入 "aaaaaaaaaaaaaaaaaaaaa!" 会导致指数级回溯
  
  # ✅ 使用原子组或避免嵌套量词
  pattern = r'^(a+)$'
  ```

---

## 7. 其他安全检查

### CORS (跨源资源共享)

- [ ] 是否限制了允许的源而非使用 `*`？
  ```python
  # ❌ 不安全的 CORS
  @app.after_request
  def add_cors_headers(response):
      response.headers['Access-Control-Allow-Origin'] = '*'
      return response
  
  # ✅ 白名单源
  ALLOWED_ORIGINS = ['https://example.com', 'https://app.example.com']
  @app.after_request
  def add_cors_headers(response):
      origin = request.headers.get('Origin')
      if origin in ALLOWED_ORIGINS:
          response.headers['Access-Control-Allow-Origin'] = origin
      return response
  ```

### CSRF (跨站请求伪造)

- [ ] 状态改变操作（POST/PUT/DELETE）是否验证 CSRF Token？

### 依赖安全

- [ ] 是否定期扫描依赖漏洞（`npm audit`, `pip-audit`, `safety`）？

---

## 审查输出格式

发现安全问题时，按以下格式记录：

```markdown
[P0] auth.py:42 - SQL 注入风险: 使用字符串拼接构建查询
建议: 使用参数化查询 cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

[P1] api.py:128 - SSRF 风险: 未验证用户提供的 URL
建议: 添加 URL 白名单验证，限制允许的域名和协议

[P2] utils.py:95 - ReDoS 风险: 正则表达式包含嵌套重复量词
建议: 简化正则为 r'^(a+)$'
```

---

## 严重级别映射

| 安全类别 | 严重级别 | 说明 |
|---------|---------|------|
| SQL 注入、XSS、SSRF、硬编码密钥 | P0 | 可直接导致数据泄露或系统被控 |
| IDOR、CSRF、竞态条件 | P1 | 可导致越权访问或数据不一致 |
| JWT 配置错误、日志泄露 | P2 | 需要特定条件才能利用 |
| 缺少超时、ReDoS | P2 | 可导致服务拒绝，但难以利用 |

---

## 参考资料

- [OWASP Top 10](https://owasp.org/Top10/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [CWE - Common Weakness Enumeration](https://cwe.mitre.org/)
