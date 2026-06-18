# Claude Code × Antigravity IDE 桥接配置指南

> 本文以 **AG** 作为 Antigravity IDE 的简称，以 **CC** 作为 Claude Code 的简称。

在 [Antigravity IDE](https://antigravity.dev) 里使用 Claude Sonnet / Opus 4.6。Gemini Pro 订阅用户每月有免费的 Claude 额度，不需要另外购买 Anthropic 订阅。

---

## 本指南涵盖的内容

- 在 Antigravity IDE 切换为 Claude 模型
- 通过 `GEMINI.md` 设置持久系统提示词（等价于 Claude Code 的 `CLAUDE.md`）
- 添加安全规则，补足 AG 没有 hook 层硬性拦截的缺口
- *(可选)* 若同时使用 Claude Code，双向同步 memory
- *(可选)* 若同时使用 Claude Code，同步 Skill / slash command

---

## 前置条件

| 需求 | 说明 |
|---|---|
| **Gemini Pro 订阅** | 获取 AG 内置的 Claude 免费额度 |
| **Antigravity IDE** | 从 [antigravity.dev](https://antigravity.dev) 下载 |
| **Python 3.9+** | 仅 memory / skill 同步脚本需要 |
| **Claude Code** | 可选，只有需要 CC↔AG 同步时才需要 |

---

## Claude 在 Antigravity IDE 的实际额度

Gemini Pro 内置 Claude 额度，但使用前请先建立正确预期。

根据实际使用体感（2026-06-18）：

- AG 每个 5 小时 Claude session 的额度，约为 Claude Pro 用户在 Claude Code 里的 **3%**
- Antigravity IDE 每周提供 **3 个**这样的 session
- 换算下来，AG 一周的 Claude 总用量约等于 Claude Code 单一 5 小时窗口的 **10%**

**这个配置实际上适合谁：**

1. **Gemini Pro 用户且没有 Claude Pro 的人** — 零额外费用就能用到 Claude，搭配本指南的配置后，体验接近完整的 Claude Code 环境（memory、skill、系统提示词都能带过去）
2. **Claude Code 用户额度用完的时候** — session 跑完还有零碎任务没收尾，AG 提供一个小缓冲，不用切换心理上下文

需要完整 Claude 用量的话，在 AG 设置里填入自己的 Anthropic API Key，就不受内置额度限制，改走标准 API 计费。

---

## Part 1 — 切换为 Claude 并配置工作区

### 1.1 在 Antigravity IDE 选择 Claude 模型

打开 Antigravity IDE，在模型选择器选 **Claude Sonnet 4.6** 或 **Claude Opus 4.6**。

Gemini Pro 订阅包含每月的 Claude 额度。用完后可在 Settings → API Keys 填入自己的 Anthropic API Key。

### 1.2 设置 `GEMINI.md` 为系统提示词

Antigravity IDE 在每次对话开始时，会自动读取工作区根目录的 `GEMINI.md`，作为持久系统提示词。

从本 repo 复制起始模板：

```bash
cp templates/GEMINI.md /你的工作区路径/GEMINI.md
```

然后编辑 `GEMINI.md`，填入自己的项目规则、代码风格要求等。

### 1.3 在 `GEMINI.md` 添加安全规则

Claude Code 通过 OS 层的 shell hook 做硬性安全防护，AG 没有等效机制，只能靠 `GEMINI.md` 软性规则。请在 `GEMINI.md` 添加以下内容：

```markdown
## 安全规则

绝对不能读取、打印、检视或传递以下任何文件的内容：
- `~/.clasprc.json` 及所有 `~/.clasprc*.json`
- `.env`、`.env.*`（任何环境变量文件）
- 任何命名为 `credentials.json` 或 `service-account.json` 的文件
- 任何文件名包含 `secret`、`token`、`key`、`credential` 的文件

执行 `git push` 前，确认暂存的 diff 不含：
- API key 格式字符串：`sk-ant-`、`sk-proj-`、`AIza`、`ghp_`、`github_pat_`、`-----BEGIN PRIVATE KEY`
- 以上列出的任何敏感文件名

若检测到违规，立即停下并询问确认再继续。
```

> 注意：这些是 AI 执行的软性规则，不是系统层硬性拦截。对高风险操作请使用 Claude Code。

---

## Part 2 — 与 Claude Code 同步（可选）

不同时使用 Claude Code 的话，可跳过这一整节。

### 2.1 同步系统提示词（symlink）

若已有 `CLAUDE.md`，建立 symlink 取代独立维护：

```bash
ln -s /你的工作区/CLAUDE.md /你的工作区/GEMINI.md
```

### 2.2 同步 memory（CC ↔ AG 双向）

**Step 1** — 找出你的 Claude Code 项目 hash：

```bash
ls ~/.claude/projects/
```

目录名称是工作区路径把 `/` 换成 `-` 的结果。

**Step 2** — 编辑 `scripts/memory_sync.py` 顶部的 CONFIG 区段：

```python
CC_MEMORY_DIR = Path.home() / ".claude" / "projects" / "你的 PROJECT HASH" / "memory"
AG_KI_DIR     = Path.home() / ".gemini" / "antigravity-ide" / "knowledge"
```

**Step 3** — 测试同步：

```bash
python3 scripts/memory_sync.py
```

**Step 4** — 设置 launchd 自动定时（macOS）：

```bash
cp scripts/com.username.memory-sync.plist.template \
   ~/Library/LaunchAgents/com.你的名字.memory-sync.plist

launchctl load ~/Library/LaunchAgents/com.你的名字.memory-sync.plist
```

### 2.3 同步 skill / slash command

**Step 1** — 编辑 `scripts/skill_sync_setup.py` 顶部的 CONFIG 区段：

```python
SKILL_DIR  = Path("/你的 skill 文件夹路径")
PLUGIN_DIR = Path.home() / ".gemini" / "config" / "plugins" / "personal-skills"
```

**Step 2** — 执行：

```bash
python3 scripts/skill_sync_setup.py
```

脚本是 idempotent，新增 skill 时重跑即可，不需要重启 AG。

---

## MCP 工具的跨 IDE 情况

| MCP 类型 | AG 是否可用 | 做法 |
|---|---|---|
| API Key 型（如 TrueNorth） | 是 | 在 `~/.gemini/config/mcp_config.json` 填入相同 key |
| OAuth 型（Gmail、Calendar、Drive） | 是，但需分别设置 | 各 IDE 各走一次 OAuth flow |
| Claude.ai 云端 MCP（`mcp__claude_ai_*`） | 否 | AG 不支持 claude.ai 认证层；用 `gws-*` Google Workspace MCP 替代 |

---

## 与 Claude Code 的功能差距

| 功能 | Claude Code | Antigravity IDE |
|---|---|---|
| 系统提示词 | `CLAUDE.md` | `GEMINI.md` |
| 持久 memory | 原生 | 脚本同步（最多 5 分钟延迟） |
| Slash command / skill | 原生 | symlink 同步 |
| Hook 层安全拦截 | 硬性（OS 层） | 仅软性规则（GEMINI.md） |
| .gs 文件自动 clasp push | Hook 自动化 | 需手动执行 `clasp push` |
| Python 写完自动跑测试 | Hook 自动化 | 不支持 |
| MCP：API Key 服务器 | 完整支持 | 需手动写配置 |
| MCP：OAuth 服务器 | 完整支持 | 需各自走 OAuth |

---

## 实际验证

本配置方式来自真实运行中的 CC + AG 双 IDE 环境：
- 21 个个人 skill 已同步
- 138 条 memory 双向同步中
- launchd 自动同步自 2026-06-18 上线至今
