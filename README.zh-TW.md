# Claude Code × Antigravity IDE 橋接設定指南

> 本文以 **AG** 作為 Antigravity IDE 的簡稱，以 **CC** 作為 Claude Code 的簡稱。

在 [Antigravity IDE](https://antigravity.dev) 裡使用 Claude Sonnet / Opus 4.6。Gemini Pro 訂閱用戶每月有免費的 Claude 額度，不需要另外購買 Anthropic 訂閱。

---

## 這份指南涵蓋的內容

- 在 Antigravity IDE 切換為 Claude 模型
- 透過 `GEMINI.md` 設定持久系統提示詞（等價於 Claude Code 的 `CLAUDE.md`）
- 加入安全規則，補足 AG 沒有 hook 層硬性攔截的缺口
- *(選用)* 若你同時使用 Claude Code，雙向同步 memory
- *(選用)* 若你同時使用 Claude Code，同步 Skill / slash command

---

## 前置條件

| 需求 | 說明 |
|---|---|
| **Gemini Pro 訂閱** | 取得 AG 內建的 Claude 免費額度；已有 Anthropic API Key 者可跳過 |
| **Antigravity IDE** | 從 [antigravity.dev](https://antigravity.dev) 下載 |
| **Python 3.9+** | 僅 memory / skill 同步腳本需要 |
| **Claude Code** | 選用，只有需要 CC↔AG 同步時才需要 |

---

## Claude 在 Antigravity IDE 的實際額度

Gemini Pro 內建 Claude 額度，但在使用前請先建立正確預期。

根據實際使用體感（2026-06-18）：

- AG 每個 5 小時 Claude session 的額度，約為 Claude Pro 用戶在 Claude Code 裡的 **3%**
- Antigravity IDE 每週提供 **3 個** 這樣的 session
- 換算下來，AG 一週的 Claude 總用量約等於 Claude Code 單一 5 小時視窗的 **10%**

Google AI Pro 訂閱用戶另有每月 **1,000 AI Credits**。開啟 **Settings → Models → Enable Overages** 後，session 配額耗盡時會自動消耗 Credits。Credits 與 Claude token 的換算比例未公開，實際能多用多少不確定。

**這個設定實際上適合誰：**

1. **Gemini Pro 用戶且沒有 Claude Pro 的人** — 零額外費用就能用到 Claude，搭配本指南的設定後，體驗接近完整的 Claude Code 環境（memory、skill、系統提示詞都能帶過去）
2. **Claude Code 用戶額度用完的時候** — session 跑完還有零碎任務沒收尾，AG 提供一個小緩衝，不用切換心理上下文

需要完整 Claude 用量的話，在 AG 設定裡填入自己的 Anthropic API Key，就不受內建額度限制，改走標準 API 計費。

---

## Part 1 — 切換為 Claude 並設定工作區

### 1.1 在 Antigravity IDE 選擇 Claude 模型

開啟 Antigravity IDE，在模型選擇器選 **Claude Sonnet 4.6** 或 **Claude Opus 4.6**。

Gemini Pro 訂閱包含每月的 Claude 額度。用完後可在 Settings → API Keys 填入自己的 Anthropic API Key。

### 1.2 設定 `GEMINI.md` 為系統提示詞

Antigravity IDE 在每次對話開始時，會自動讀取工作區根目錄的 `GEMINI.md`，作為持久系統提示詞。

從本 repo 複製起始模板：

```bash
cp templates/GEMINI.md /你的工作區路徑/GEMINI.md
```

然後編輯 `GEMINI.md`，填入自己的專案規則、程式碼風格要求等。

### 1.3 在 `GEMINI.md` 加入安全規則

Claude Code 透過 OS 層的 shell hook 做硬性安全防護，AG 沒有等效機制，只能靠 `GEMINI.md` 軟性規則。請在 `GEMINI.md` 加入以下區塊：

```markdown
## 安全規則

絕對不能讀取、列印、檢視或傳遞以下任何檔案的內容：
- `~/.clasprc.json` 及所有 `~/.clasprc*.json`
- `.env`、`.env.*`（任何環境變數檔）
- 任何命名為 `credentials.json` 或 `service-account.json` 的檔案
- 任何檔名包含 `secret`、`token`、`key`、`credential` 的檔案

執行 `git push` 前，確認暫存的 diff 不含：
- API key 格式字串：`sk-ant-`、`sk-proj-`、`AIza`、`ghp_`、`github_pat_`、`-----BEGIN PRIVATE KEY`
- 以上列出的任何敏感檔名

若偵測到違規，立即停下並詢問確認再繼續。
```

> 注意：這些是 AI 執行的軟性規則，不是系統層硬性攔截。對高風險操作請使用 Claude Code。

---

## Part 2 — 與 Claude Code 同步（選用）

不同時使用 Claude Code 的話，可跳過這一整節。

### 2.1 同步系統提示詞（symlink）

若已有 `CLAUDE.md`，建立 symlink 取代獨立維護：

```bash
ln -s /你的工作區/CLAUDE.md /你的工作區/GEMINI.md
```

確認 symlink：
```bash
ls -la /你的工作區/GEMINI.md
# 正確輸出：GEMINI.md -> /你的工作區/CLAUDE.md
```

### 2.2 同步 memory（CC ↔ AG 雙向）

Claude Code 的 memory 存在：
```
~/.claude/projects/<project-hash>/memory/
```

Antigravity IDE 的 memory（Knowledge Items）存在：
```
~/.gemini/antigravity-ide/knowledge/<ki-name>/
```

兩者格式不相容，`scripts/memory_sync.py` 負責雙向轉換。

#### 設定步驟

**Step 1** — 找出你的 Claude Code 專案 hash：

```bash
ls ~/.claude/projects/
```

目錄名稱是工作區路徑把 `/` 換成 `-` 的結果。例如 `/Users/alice/my-project` → `-Users-alice-my-project`。

**Step 2** — 編輯 `scripts/memory_sync.py` 頂部的 CONFIG 區段：

```python
CC_MEMORY_DIR = Path.home() / ".claude" / "projects" / "你的 PROJECT HASH" / "memory"
AG_KI_DIR     = Path.home() / ".gemini" / "antigravity-ide" / "knowledge"
```

**Step 3** — 測試同步：

```bash
python3 scripts/memory_sync.py
```

**Step 4** — 設定 launchd 自動排程（macOS）：

```bash
cp scripts/com.username.memory-sync.plist.template \
   ~/Library/LaunchAgents/com.你的名字.memory-sync.plist

# 編輯 plist，填入實際路徑後：
launchctl load ~/Library/LaunchAgents/com.你的名字.memory-sync.plist
```

預設每 5 分鐘同步一次，修改 plist 的 `StartInterval` 可調整。

#### 疑難排解

**job 有載入但沒反應，或 error log 出現 `Operation not permitted`：**
`/usr/bin/python3` 是 Apple Command Line Tools 內建的 Python，沒有 Full Disk Access。如果你把這個 repo clone 到受保護的資料夾（`~/Desktop`、`~/Documents`、`~/Downloads`），launchd 就讀不到 `memory_sync.py`。兩種修法擇一：
- 到「系統設定 → 隱私權與安全性 → 完整磁碟取用權」把那支 Python 加入授權，或
- 把 plist 裡的 `/usr/bin/python3` 換成你自己的直譯器，用 `which python3` 查（Apple Silicon 的 Homebrew 通常是 `/opt/homebrew/bin/python3`，Intel 是 `/usr/local/bin/python3`）。

**job 完全不啟動，或靜默載入失敗：**
plist 是 XML，用 `plutil -lint <plist>` 驗證。如果你的絕對路徑含有 `&`、`<`、`>`，必須跳脫成 `&amp;`、`&lt;`、`&gt;`，一個沒跳脫的 `&` 就會讓整份 plist 解析失敗、靜默不跑。

#### 防循環設計

CC 同步過來的 KI 統一加 `claude-memory-` 前綴。AG→CC 方向只處理沒有此前綴的 KI，所以 CC 來的 memory 不會被誤判為 AG 原生 KI 再同步回去。

#### 常用指令

```bash
# 確認同步排程狀態
launchctl list | grep memory-sync

# 查看最近同步紀錄
tail -50 ~/.gemini/antigravity-ide/sync_memory_to_ki.log

# 手動觸發同步
python3 scripts/memory_sync.py

# 停止自動同步
launchctl unload ~/Library/LaunchAgents/com.你的名字.memory-sync.plist
```

### 2.3 同步 skill / slash command

Claude Code 讀取 `~/.claude/commands/` 的 slash command。
Antigravity IDE 讀取 `~/.gemini/config/plugins/<plugin-name>/skills/` 的 skill。

`scripts/skill_sync_setup.py` 建立 symlink，讓兩個 IDE 讀同一份來源檔案。

#### 前置條件：YAML frontmatter

每個 skill 的 `.md` 檔頂部需要有 frontmatter：

```markdown
---
name: my-skill
description: 一句話說明這個 skill 做什麼
---

（skill 內容從這裡開始）
```

#### 設定步驟

**Step 1** — 編輯 `scripts/skill_sync_setup.py` 頂部的 CONFIG 區段：

```python
SKILL_DIR  = Path("/你的 skill 資料夾路徑")
PLUGIN_DIR = Path.home() / ".gemini" / "config" / "plugins" / "personal-skills"
```

**Step 2** — 為沒有 frontmatter 的 skill 檔手動加上後執行：

```bash
python3 scripts/skill_sync_setup.py
```

腳本是 idempotent，新增 skill 時重跑即可，不需要重啟 AG。

---

## MCP 工具的跨 IDE 情況

| MCP 類型 | AG 是否可用 | 做法 |
|---|---|---|
| API Key 型（如 Perplexity Search） | 是 | 在 `~/.gemini/config/mcp_config.json` 填入相同 key |
| OAuth 型（Gmail、Calendar、Drive） | 是，但需分別設定 | 各 IDE 各走一次 OAuth flow |
| Claude.ai 雲端 MCP（`mcp__claude_ai_*`） | 否 | AG 不支援 claude.ai 認證層；用 `gws-*` Google Workspace MCP 取代 |

---

## 與 Claude Code 的功能差距

| 功能 | Claude Code | Antigravity IDE |
|---|---|---|
| 系統提示詞 | `CLAUDE.md` | `GEMINI.md` |
| 持久 memory | 原生 | 腳本同步（最多 5 分鐘延遲） |
| Slash command / skill | 原生 | symlink 同步 |
| Hook 層安全攔截 | 硬性（OS 層） | 僅軟性規則（GEMINI.md） |
| .gs 檔自動 clasp push | Hook 自動化 | 需手動執行 `clasp push` |
| Python 寫完自動跑測試 | Hook 自動化 | 不支援 |
| MCP：API Key 伺服器 | 完整支援 | 需手動寫設定 |
| MCP：OAuth 伺服器 | 完整支援 | 需各自走 OAuth |

---

## 實際驗證

本設定方式來自真實運行中的 CC + AG 雙 IDE 環境：
- 21 個個人 skill 已同步
- 138 筆 memory 雙向同步中
- launchd 自動同步自 2026-06-18 上線至今
