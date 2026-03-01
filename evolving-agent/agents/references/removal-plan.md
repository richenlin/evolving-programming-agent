# 移除候选检查清单

代码审查时，使用此清单识别可以安全删除或需要延迟删除的代码。

---

## 1. 识别标准

### 未调用函数

- [ ] 函数是否在代码库中被调用？
  - 使用 grep 或 IDE 搜索函数名
  - 检查是否有动态调用（反射、eval、动态方法名）
  
  ```bash
  # 搜索函数调用
  grep -r "function_name" --include="*.py" .
  grep -r "functionName" --include="*.js" .
  ```

### 已禁用的 Feature Flag 分支

- [ ] 是否有已永久启用的 feature flag 的旧分支？
  ```python
  # ❌ 旧 feature flag 分支
  if feature_flags.get('new_checkout_flow'):
      return new_checkout()
  else:
      return old_checkout()  # feature flag 已永久启用，此分支永不执行
  ```

### 重复逻辑

- [ ] 是否有相似度 > 80% 的代码块？
  - 使用重复代码检测工具（CPD, jscpd）
  - 手动审查相似函数

### 过时注释

- [ ] 注释是否与代码不一致？
  ```python
  # ❌ 过时注释
  # 返回用户列表（已废弃，现在返回字典）
  def get_users():
      return {'users': User.query.all()}
  ```

- [ ] 是否有 TODO/FIXME 超过 6 个月未处理？
  - 使用 `git blame` 检查 TODO 添加时间

### 废弃的依赖导入

- [ ] 是否有导入但未使用的模块？
  - 使用 linter（pylint, eslint）检测未使用导入

### 注释掉的代码

- [ ] 是否有大段注释掉的代码（> 10 行）？
  - Git 历史已保存，可以安全删除

---

## 2. 删除策略判断

### 安全删除 (Safe Deletion)

满足以下**所有**条件时可安全删除：

| 条件 | 检查方法 |
|------|---------|
| ✅ 无外部调用 | grep 搜索无结果，无公开 API 文档引用 |
| ✅ 有测试覆盖 | 删除测试不失败，或测试可以一并删除 |
| ✅ 变更范围局限 | 仅在当前模块/文件内影响 |
| ✅ 无动态调用 | 不存在反射、eval、动态方法名调用 |
| ✅ 不是接口实现 | 不是抽象类/接口的实现 |

**示例：私有工具函数**
```python
# ✅ 安全删除
class UserValidator:
    def _normalize_email(self, email):  # 私有方法，仅内部使用
        return email.lower().strip()
    
    def validate(self, user_data):
        email = self._normalize_email(user_data['email'])
        # ...
```

### 延迟删除 (Deferred Deletion)

满足以下**任意**条件时需延迟删除：

| 条件 | 原因 |
|------|------|
| ⚠️ 公开 API | 外部系统可能依赖，需要版本公告 |
| ⚠️ 跨服务调用 | 其他微服务可能调用，需要协调 |
| ⚠️ 不确定调用方 | 无法确认所有调用方，需要进一步调查 |
| ⚠️ 数据库迁移相关 | 需要先完成数据迁移 |
| ⚠️ 配置/开关控制 | 需要先确认配置状态 |
| ⚠️ 接口实现 | 需要先确认接口是否可以修改 |

**示例：公开 API 端点**
```python
# ⚠️ 延迟删除
@app.route('/api/v1/legacy-endpoint')
def legacy_endpoint():  # 公开 API，可能有外部调用
    return {'status': 'deprecated'}
```

**处理步骤**：
1. 标记为 `@deprecated`
2. 添加文档说明替代方案
3. 通知调用方迁移
4. 等待一个版本周期（如 1-2 个月）
5. 确认无调用后删除

---

## 3. 删除前检查清单

### 代码层面

- [ ] 确认无硬编码字符串引用（如配置文件、数据库存储的类名/方法名）
- [ ] 确认无反射/动态调用
- [ ] 确认无测试依赖（或测试可以一并删除）

### 文档层面

- [ ] 更新 API 文档
- [ ] 更新 CHANGELOG
- [ ] 通知相关团队（如果是公开 API）

### 数据层面

- [ ] 确认无数据库数据依赖（如存储的序列化对象）
- [ ] 确认无缓存键依赖

---

## 4. 输出模板

审查时发现移除候选，按以下格式记录：

### 表格格式

```markdown
## Removal Candidates

| 位置 | 类型 | 理由 | 建议 |
|------|------|------|------|
| `utils.py:42` | 未使用函数 | 无调用者 | 安全删除 |
| `api.py:128` | 废弃 API | 已有新版本 v2 | 标记 @deprecated，下版本删除 |
| `feature.py:95` | Feature flag 旧分支 | flag 已永久启用 | 安全删除旧分支 |
| `models.py:200` | 注释代码 | > 20 行注释代码 | 安全删除 |
| `service.py:50` | 重复逻辑 | 与 `common.py:30` 重复 90% | 合并到 common.py |
```

### 详细格式

```markdown
[P3] utils.py:42 - `unused_helper()` 未使用函数
- 搜索结果: grep 无匹配
- 测试影响: 无相关测试
- 建议: 安全删除

[P2] api.py:128 - `/api/v1/legacy-endpoint` 废弃 API
- 搜索结果: 可能有外部调用（公开 API）
- 替代方案: `/api/v2/endpoint`
- 建议: 标记 @deprecated，添加迁移文档，下个版本删除
```

---

## 5. 工具推荐

### 静态分析

| 工具 | 语言 | 功能 |
|------|------|------|
| `pylint` | Python | 检测未使用变量、导入、函数 |
| `eslint` | JavaScript | 检测未使用变量、导入、函数 |
| `jscpd` | 多语言 | 检测重复代码 |
| `CPD` | 多语言 | 检测重复代码（PMD 工具集） |

### 搜索工具

```bash
# 搜索函数调用（排除注释）
grep -r "function_name" --include="*.py" . | grep -v "^\s*#"

# 搜索 TODO/FIXME
grep -r "TODO\|FIXME" --include="*.py" .

# 使用 git 查找最后修改时间
git log -1 --format="%ai" -- path/to/file.py
```

---

## 6. 删除流程

### 小型删除（< 50 行）

1. 确认安全删除条件
2. 删除代码
3. 删除相关测试
4. 运行测试套件
5. 提交

### 大型删除（≥ 50 行）

1. 确认删除策略（安全/延迟）
2. 如果是延迟删除：
   - 标记 `@deprecated`
   - 更新文档
   - 通知相关方
   - 创建删除任务（scheduled removal）
3. 如果是安全删除：
   - 分批次删除（每次 < 100 行）
   - 每次删除后运行测试
   - 提交并记录理由

---

## 审查输出示例

```markdown
[P3] utils/legacy.py:15-45 - `old_validation()` 未使用函数
- 类型: 未使用函数
- 理由: grep 搜索无调用，已有新版本 `new_validation()`
- 建议: 安全删除

[P2] api/v1/endpoints.py:200-250 - `/api/v1/search` 废弃 API
- 类型: 公开 API
- 理由: 已被 `/api/v2/search` 替代，但可能有外部调用
- 建议: 标记 @deprecated，添加迁移指南，计划在 v3.0 删除
```

---

## 参考资料

- Martin Fowler, "Refactoring: Improving the Design of Existing Code" - Chapter on Removing Dead Code
- [GitHub - Detecting Unused Code](https://github.com/topics/unused-code)
- [Deprecation Best Practices](https://docs.microsoft.com/en-us/azure/architecture/patterns/deprecated-interface)
