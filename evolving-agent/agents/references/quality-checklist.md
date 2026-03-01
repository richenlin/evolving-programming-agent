# 代码质量检查清单

代码审查时，使用此清单识别性能问题、错误处理缺陷和边界条件漏洞。

---

## 1. 错误处理

### 吞异常 (Swallowing Exceptions)

- [ ] 是否有空 catch 块或仅打印日志的 catch 块？
  ```python
  # ❌ 吞异常
  try:
      process_data()
  except:
      pass  # 异常被忽略，无法追踪
  
  # ✅ 至少记录日志
  try:
      process_data()
  except Exception as e:
      logger.error(f"Failed to process data: {e}", exc_info=True)
  ```

### 过宽的异常捕获

- [ ] 是否捕获了基类 Exception 而非具体异常？
  ```python
  # ❌ 过宽捕获
  try:
      fetch_user(user_id)
  except Exception:  # 会捕获所有异常，包括 KeyboardInterrupt
      return None
  
  # ✅ 捕获具体异常
  try:
      fetch_user(user_id)
  except (ConnectionError, TimeoutError) as e:
      logger.warning(f"Network error: {e}")
      return None
  ```

### 未处理的 async 错误

- [ ] Promise/async 函数是否缺少错误处理？
  ```javascript
  // ❌ 未处理的 Promise 拒绝
  async function fetchUser(id) {
      const response = await fetch(`/api/users/${id}`);
      return response.json();
  }
  
  // ✅ 添加错误处理
  async function fetchUser(id) {
      try {
          const response = await fetch(`/api/users/${id}`);
          return response.json();
      } catch (error) {
          console.error(`Failed to fetch user ${id}:`, error);
          return null;
      }
  }
  ```

### 错误信息泄露

- [ ] 错误响应是否包含敏感的 stack trace 或内部信息？
  ```python
  # ❌ 泄露 stack trace
  @app.errorhandler(Exception)
  def handle_error(e):
      return str(e), 500  # 可能包含内部路径、数据库结构等
  
  # ✅ 通用错误消息
  @app.errorhandler(Exception)
  def handle_error(e):
      logger.exception("Internal error")
      return {"error": "Internal server error"}, 500
  ```

---

## 2. 性能

### N+1 查询

- [ ] 是否在循环中执行数据库查询？
  ```python
  # ❌ N+1 查询
  users = User.query.all()
  for user in users:
      orders = Order.query.filter_by(user_id=user.id).all()  # 每个用户一次查询
      print(user.name, len(orders))
  
  # ✅ 批量加载（eager loading）
  from sqlalchemy.orm import joinedload
  users = User.query.options(joinedload(User.orders)).all()
  for user in users:
      print(user.name, len(user.orders))
  ```

### 缓存问题

- [ ] 缓存是否设置了 TTL (Time To Live)？
  ```python
  # ❌ 无 TTL，缓存永不过期
  cache.set('user:123', user_data)
  
  # ✅ 设置 TTL
  cache.set('user:123', user_data, ttl=3600)  # 1小时后过期
  ```

- [ ] 缓存键是否包含版本或时间戳以避免键冲突？
  ```python
  # ❌ 缓存键冲突风险
  cache.set('config', config_data)
  
  # ✅ 包含版本
  cache.set(f'config:v{version}', config_data)
  ```

- [ ] 是否有缓存失效策略（主动失效 vs 被动过期）？

### ReDoS (正则表达式拒绝服务)

- [ ] 正则表达式是否在热路径中？
- [ ] 是否包含回溯风险的模式（如嵌套量词 `^(a+)+$`）？
  
  参考 security-checklist.md 中的 ReDoS 章节

### 内存：无界集合增长

- [ ] 集合/列表是否无限增长？
  ```python
  # ❌ 无界增长
  results = []
  for item in large_dataset:
      if condition(item):
          results.append(item)  # 可能无限增长
  
  # ✅ 限制大小
  from collections import deque
  results = deque(maxlen=1000)  # 最多保留 1000 个
  ```

- [ ] 是否使用了生成器而非列表以节省内存？
  ```python
  # ❌ 加载全部到内存
  def read_lines(file_path):
      with open(file_path) as f:
          return f.readlines()  # 全部加载到内存
  
  # ✅ 使用生成器
  def read_lines(file_path):
      with open(file_path) as f:
          for line in f:
              yield line  # 逐行读取
  ```

---

## 3. 边界条件

### Null/Undefined 处理

- [ ] 是否使用了"truthy check"排除了 0 和空字符串？
  ```python
  # ❌ Truthy check 排除 0 和空字符串
  def calculate_discount(price, discount):
      if discount:  # discount=0 会被忽略
          return price * discount
      return price
  
  # ✅ 显式 None 检查
  def calculate_discount(price, discount=None):
      if discount is not None:
          return price * discount
      return price
  ```

- [ ] 访问对象属性前是否检查了对象是否为 None？
  ```python
  # ❌ 空指针风险
  user = get_user(user_id)
  print(user.name)  # user 可能为 None
  
  # ✅ 空值检查
  user = get_user(user_id)
  if user:
      print(user.name)
  ```

### 空集合

- [ ] 是否直接访问数组/列表索引而未检查长度？
  ```python
  # ❌ 索引越界风险
  items = get_items()
  first_item = items[0]  # items 可能为空列表
  
  # ✅ 长度检查
  items = get_items()
  if items:
      first_item = items[0]
  else:
      first_item = None
  ```

- [ ] 是否对空集合调用了 max/min/sum 等函数？
  ```python
  # ❌ 空集合错误
  scores = []
  max_score = max(scores)  # ValueError: max() arg is an empty sequence
  
  # ✅ 提供默认值
  scores = []
  max_score = max(scores, default=0)
  ```

### 数值边界

- [ ] 是否有除以零的风险？
  ```python
  # ❌ 除零错误
  average = total / count  # count 可能为 0
  
  # ✅ 检查除数
  average = total / count if count > 0 else 0
  ```

- [ ] 是否考虑了整数溢出（Python 中较少见，但在其他语言中重要）？

### 字符串边界

- [ ] 是否处理了空字符串或仅空白字符串？
  ```python
  # ❌ 未处理空白字符串
  def greet(name):
      return f"Hello, {name}!"
  
  # ✅ 处理空白
  def greet(name):
      cleaned_name = name.strip() if name else ""
      if not cleaned_name:
          return "Hello, Guest!"
      return f"Hello, {cleaned_name}!"
  ```

- [ ] 是否对超长字符串进行了截断？
  ```python
  # ❌ 未限制长度
  user_input = request.form.get('comment')
  save_comment(user_input)  # 可能存储超长文本
  
  # ✅ 限制长度
  user_input = request.form.get('comment', '')[:1000]  # 最多 1000 字符
  ```

---

## 4. 其他质量检查

### 魔法数字

- [ ] 代码中是否包含未命名的常量？
  ```python
  # ❌ 魔法数字
  if user.age >= 18:
      allow_access()
  
  # ✅ 命名常量
  LEGAL_AGE = 18
  if user.age >= LEGAL_AGE:
      allow_access()
  ```

### 重复代码

- [ ] 是否有 3 行或更多相同/相似的代码块？
  - 使用复制粘贴检测工具（如 CPD、jscpd）

### 未使用的代码

- [ ] 是否有未使用的导入、变量、函数？
  - 使用 linter（如 pylint, eslint）检测

### 复杂度过高

- [ ] 函数圈复杂度（Cyclomatic Complexity）是否 > 10？
  - 使用工具（如 radon, eslint complexity rule）检测

---

## 审查输出格式

发现质量问题时，按以下格式记录：

```markdown
[P2] order_service.py:95 - N+1 查询: 在循环中查询订单
建议: 使用 joinedload 批量加载 orders

[P2] utils.py:42 - 边界条件缺失: 未检查 items 列表是否为空
建议: 添加 if items: 检查或使用 items[0] if items else None

[P3] config.py:15 - 魔法数字: 3600 未命名
建议: 定义常量 CACHE_TTL_SECONDS = 3600
```

---

## 严重级别映射

| 质量类别 | 严重级别 | 说明 |
|---------|---------|------|
| N+1 查询、无界内存增长 | P1 | 严重影响性能，可能导致服务崩溃 |
| 吞异常、错误信息泄露 | P1 | 影响可调试性和安全性 |
| 缓存无 TTL、空指针 | P2 | 可能导致资源泄露或运行时错误 |
| 魔法数字、未使用代码 | P3 | 影响可维护性，但无直接影响 |

---

## 参考资料

- Martin Fowler, "Refactoring: Improving the Design of Existing Code"
- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
- [JavaScript Performance Best Practices](https://developer.mozilla.org/en-US/docs/Web/Performance)
