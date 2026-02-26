---
name: browser
description: 浏览器自动化技能。当用户需要操作浏览器、访问网页、截图、爬取数据、测试网页、自动化点击或填写表单等任何浏览器相关任务时使用此技能。包括但不限于：打开网页、点击元素、填写表单、截图、获取页面内容、等待元素加载、模拟设备、Cookie/存储操作等。只要涉及浏览器自动化的需求，都必须使用此技能。
---

# Browser 浏览器自动化技能

此技能使用 `agent-browser` 命令行工具进行浏览器自动化操作。

## 前置条件

`agent-browser` 需要浏览器通过 CDP (Chrome DevTools Protocol) 连接。

## 启动浏览器

### 检查 CDP 连接

首先尝试执行 agent-browser 命令。如果出现连接错误（如 "Failed to connect to browser" 或 "ECONNREFUSED"），则需要启动调试模式的浏览器。

### 启动 Chrome 调试模式

当无法通过 CDP 连接时，需要根据操作系统启动对应版本的 Chrome 调试模式浏览器。

#### macOS

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  '--remote-allow-origins=*' \
  --user-data-dir=/tmp/chrome-debug-profile
```

#### Windows (PowerShell)

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --remote-allow-origins=* `
  --user-data-dir=C:\tmp\chrome-debug-profile
```

#### Windows (CMD)

```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --remote-allow-origins=* ^
  --user-data-dir=C:\tmp\chrome-debug-profile
```

#### Linux

```bash
google-chrome \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir=/tmp/chrome-debug-profile
```

如果 `google-chrome` 命令不存在，可尝试以下替代路径：
- `/usr/bin/google-chrome`
- `/usr/bin/chromium`
- `/usr/bin/chromium-browser`

**注意**：
- `--user-data-dir` 使用临时目录，避免影响用户正常浏览器配置
- 默认 CDP 端口为 9222
- 启动后浏览器会保持运行，可随时使用 agent-browser 操作
- Windows 路径可以根据实际安装位置调整（如安装在非默认目录）

## 命令参考

### 核心操作

```bash
# 导航到 URL（别名：goto, navigate）
agent-browser open <url>

# 点击元素
agent-browser click <selector>

# 双击元素
agent-browser dblclick <selector>

# 清空并填写输入框
agent-browser fill <selector> <text>

# 在元素中输入文字（不清空）
agent-browser type <selector> <text>

# 按键（Enter, Tab, Control+a 等）
agent-browser press <key>

# 悬停在元素上
agent-browser hover <selector>

# 选择下拉选项
agent-browser select <selector> <value>

# 勾选复选框
agent-browser check <selector>

# 取消勾选复选框
agent-browser uncheck <selector>

# 滚动（up/down/left/right，可选像素值）
agent-browser scroll <direction> [pixels]

# 截图（--full 表示整页截图）
agent-browser screenshot [path] [--full]

# 获取可访问性树快照（包含元素引用）
agent-browser snapshot

# 执行 JavaScript
agent-browser eval <javascript>

# 关闭浏览器
agent-browser close
```

### 获取信息

```bash
# 获取元素文本内容
agent-browser get text <selector>

# 获取元素 HTML
agent-browser get html <selector>

# 获取输入框的值
agent-browser get value <selector>

# 获取元素属性
agent-browser get attr <selector> <attribute>

# 获取页面标题
agent-browser get title

# 获取当前 URL
agent-browser get url

# 统计匹配元素数量
agent-browser get count <selector>

# 获取元素边界框
agent-browser get box <selector>
```

### 检查状态

```bash
# 检查元素是否可见
agent-browser is visible <selector>

# 检查元素是否启用
agent-browser is enabled <selector>

# 检查复选框是否已勾选
agent-browser is checked <selector>
```

### 查找元素（语义定位）

```bash
# 按角色查找并执行操作
agent-browser find role <role> <action> [--name <name>]

# 按文本查找并执行操作
agent-browser find text <text> <action>

# 按标签查找并执行操作
agent-browser find label <label> <action> [value]

# 按占位符查找并执行操作
agent-browser find placeholder <placeholder> <action> [value]

# 按 test-id 查找并执行操作
agent-browser find testid <id> <action> [value]

# 查找第一个匹配元素
agent-browser find first <selector> <action> [value]

# 查找第 N 个匹配元素
agent-browser find nth <n> <selector> <action> [value]
```

**支持的操作**: `click`, `fill`, `check`, `hover`, `text`

**示例**：
```bash
# 点击名为 "Submit" 的按钮
agent-browser find role button click --name "Submit"

# 填写标签为 "Email" 的输入框
agent-browser find label "Email" fill "test@example.com"

# 点击第一个匹配的元素
agent-browser find first ".item" click
```

### 等待操作

```bash
# 等待元素出现
agent-browser wait <selector>

# 等待指定毫秒数
agent-browser wait <milliseconds>

# 等待页面出现指定文本
agent-browser wait --text "Welcome"

# 等待 URL 匹配模式
agent-browser wait --url "**/dashboard"

# 等待网络空闲状态
agent-browser wait --load networkidle

# 等待 JavaScript 条件为真
agent-browser wait --fn "condition"
```

### 鼠标操作

```bash
# 移动鼠标到指定坐标
agent-browser mouse move <x> <y>

# 按下鼠标按钮
agent-browser mouse down [button]

# 释放鼠标按钮
agent-browser mouse up [button]

# 滚动鼠标滚轮
agent-browser mouse wheel <dy> [dx]
```

### 浏览器设置

```bash
# 设置视口大小
agent-browser set viewport <width> <height>

# 模拟设备（如 "iPhone 14"）
agent-browser set device <device_name>

# 设置地理位置
agent-browser set geo <latitude> <longitude>

# 切换离线模式
agent-browser set offline [on|off]

# 设置额外的 HTTP 请求头
agent-browser set headers <json>

# 设置 HTTP 基本认证
agent-browser set credentials <username> <password>

# 模拟颜色方案（dark/light）
agent-browser set media [dark|light]
```

### Cookie 和存储

```bash
# 获取所有 Cookie
agent-browser cookies

# 设置 Cookie
agent-browser cookies set <name> <value>

# 清除所有 Cookie
agent-browser cookies clear

# 获取所有 localStorage
agent-browser storage local

# 获取指定的 localStorage key
agent-browser storage local <key>

# 设置 localStorage
agent-browser storage local set <key> <value>

# 清除所有 localStorage
agent-browser storage local clear

# sessionStorage 操作同上
agent-browser storage session
```

### 网络请求

```bash
# 拦截请求
agent-browser network route <url_pattern>

# 阻止请求
agent-browser network route <url_pattern> --abort

# 模拟响应
agent-browser network route <url_pattern> --body <json>

# 移除拦截规则
agent-browser network unroute [url_pattern]

# 查看跟踪的请求
agent-browser network requests
```

### 标签页和框架

```bash
# 列出所有标签页
agent-browser tab

# 打开新标签页（可选 URL）
agent-browser tab new [url]

# 切换到指定标签页
agent-browser tab <index>

# 关闭标签页
agent-browser tab close [index]

# 切换到 iframe
agent-browser frame <selector>

# 返回主框架
agent-browser frame main
```

### 调试工具

```bash
# 开始性能跟踪
agent-browser trace start [path]

# 停止并保存跟踪
agent-browser trace stop [path]

# 查看控制台消息
agent-browser console

# 查看页面错误
agent-browser errors

# 高亮显示元素
agent-browser highlight <selector>

# 保存认证状态
agent-browser state save <path>

# 加载认证状态
agent-browser state load <path>
```

### 导航操作

```bash
# 后退
agent-browser back

# 前进
agent-browser forward

# 刷新页面
agent-browser reload
```

## 选择器

支持 CSS 选择器和语义选择器：

| 类型 | 示例 |
|------|------|
| ID | `#submit-btn` |
| 类 | `.btn-primary` |
| 属性 | `[data-testid="submit"]` |
| 组合 | `form.login input[type="email"]` |
| 语义 | `find role button click --name "登录"` |

## 典型工作流程

### 1. 打开网页并截图

```bash
agent-browser open https://example.com
agent-browser wait --load networkidle
agent-browser screenshot /tmp/example.png --full
```

### 2. 填写表单并提交

```bash
agent-browser open https://example.com/login
agent-browser find label "用户名" fill "myuser"
agent-browser find label "密码" fill "mypassword"
agent-browser find role button click --name "登录"
agent-browser wait --text "欢迎"
```

### 3. 爬取页面数据

```bash
agent-browser open https://example.com
agent-browser snapshot  # 获取页面结构
agent-browser get text ".article-title"
agent-browser get attr "a.link" "href"
```

### 4. 等待动态内容

```bash
agent-browser open https://example.com
agent-browser wait ".data-loaded"  # 等待元素出现
agent-browser get text ".result"
```

## 错误处理

- **连接失败**: 检查是否启动了 Chrome 调试模式
- **元素未找到**: 使用 `snapshot` 查看页面结构，检查选择器是否正确
- **超时**: 使用 `wait` 命令等待元素加载后再操作
- **操作失败**: 检查元素是否可见、可点击（使用 `is visible`, `is enabled`）

## 最佳实践

1. **使用等待**: 在操作元素前使用 `wait` 确保元素已加载
2. **语义选择器**: 优先使用 `find role`、`find label` 等语义定位，更稳定
3. **快照调试**: 使用 `snapshot` 查看页面结构，帮助编写正确的选择器
4. **网络空闲**: 对于动态页面，使用 `wait --load networkidle` 等待完全加载
5. **状态保存**: 需要登录的操作，使用 `state save/load` 避免重复登录

## 注意事项

- 浏览器启动后会保持运行，完成后记得使用 `agent-browser close` 关闭
- 使用 `--user-data-dir=/tmp/chrome-debug-profile` 避免影响正常浏览器配置
- 整页截图使用 `--full` 标志
- JavaScript 执行使用 `eval` 命令，返回执行结果
