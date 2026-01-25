# Evolution Check - 进化检查

**必须**在每个开发/修复循环结束后执行。

## 执行时机

- Full Mode: 开发循环完成后
- Simple Mode: 修复循环完成后
- 会话结束前

## 检查流程

```
检查 .opencode/.evolution_mode_active
    ├─ 存在 → 进化模式激活 → 主动提取
    └─ 不存在 → 被动检查
                ├─ 复杂问题(尝试>1次) → 提取
                ├─ 用户说"记住" → 提取
                └─ 否则 → 正常结束
```

## 触发条件

| 场景 | 触发 |
|------|------|
| 修复失败2次后成功 | 是 |
| 用户说"记住这个" | 是 |
| 发现更优方案 | 是 |
| 特定环境 workaround | 是 |
| 简单修改一行代码 | 否 |
| 用户说"很好"、"ok" | 否 |

## 执行命令

```bash
# 检查状态
python scripts/run.py mode --status

# 触发检测
python scripts/run.py knowledge trigger --input "用户输入描述"

# 归纳存储
echo "{会话摘要}" | python scripts/run.py knowledge summarize --auto-store
```

## 快速存储

```bash
# 存储偏好
python scripts/run.py project store --preference "内容"

# 存储修复方案
python scripts/run.py project store --fix "方案描述"

# 存储技术栈模式
python scripts/run.py project store --tech react --pattern "模式内容"
```

## 示例

### 复杂修复
```
用户: 修复跨域问题
尝试1: 修改 headers - 失败
尝试2: 配置 proxy - 成功

进化检查:
1. 检测尝试次数 > 1 → 触发
2. 提取: "Vite项目跨域需要配置proxy"
3. 存储到知识库
```

### 用户要求
```
用户: 记住以后都用 pnpm

进化检查:
1. 检测"记住" → 触发
2. 提取: "项目使用pnpm"
3. 存储到知识库
```

## 注意事项

- **异步执行**: 使用 Task 工具，不阻塞主交互
- **静默模式**: 只在存储成功后简短通知
- **去重机制**: 知识库自动去重
