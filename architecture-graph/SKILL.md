---
name: architecture-graph
description: "为任何项目创建交互式单页 HTML 架构图。分析项目结构，识别模块和关系，生成带详情页、代码语法高亮和导航的可视化图表。用于：项目架构可视化、入职文档、技术文档、代码审查准备。"
---

# Architecture Graph 技能

## 概述

本技能用于创建专业的交互式架构图，输出为单个 HTML 文件。通过分析项目结构，识别关键模块及其关系，生成分层可视化的交互式图表。

核心特性：
- **模块化架构展示** - 按功能分组组织
- **交互式详情页** - 点击模块查看详细说明
- **导航系统** - 支持返回总览和 ESC 快捷键
- **代码高亮** - 暗色主题代码块
- **可视化图表** - HTML/CSS 架构图
- **单文件交付** - 无外部依赖

## 何时使用

- 可视化项目架构用于技术文档
- 为新成员创建项目导航图
- 代码审查前的架构梳理
- 遗留系统的结构分析
- 技术分享或演示材料

## 使用步骤

### 步骤 1：探索项目结构

首先了解项目的组织方式：

```bash
# 列出源代码文件
find . -type f \( -name "*.ts" -o -name "*.js" -o -name "*.py" -o -name "*.go" -o -name "*.rs" \) | grep -v node_modules | head -50

# 查看项目配置
read package.json / Cargo.toml / pyproject.toml / go.mod

# 查看入口文件
read src/main.* / src/index.* / main.* / app.*

# 查看 README
read README.md
```

### 步骤 2：识别架构模式

根据项目特点，确定如何划分模块组。常见的划分方式包括：

**按功能领域划分**（适合业务系统）：
- 用户认证、订单处理、支付、通知等

**按技术层次划分**（适合分层架构）：
- 表现层、业务逻辑、数据访问、基础设施

**按组件类型划分**（适合组件化项目）：
- 核心组件、UI 组件、工具组件、第三方集成

**按部署边界划分**（适合微服务）：
- 各个服务的模块分组

> **注意**：选择最适合当前项目的划分方式，不强套用固定模板。

### 步骤 3：提取关键模块

对于每个模块组，提取核心模块：

```javascript
// 模块注册表示例结构
const moduleDetails = {
    moduleId: {
        title: '模块名称',
        file: '文件路径',
        description: '一句话描述职责',
        sections: [
            { title: '架构设计', content: '...' },
            { title: '核心功能', content: '...' },
            { title: '使用示例', content: '...' }
        ]
    }
};
```

模块信息来源：
- 文件名和目录结构
- 类/函数/接口定义
- 代码注释和文档
- import 依赖关系

### 步骤 4：生成 HTML 结构

创建包含以下结构的 HTML 文件：

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>项目名称 架构图</title>
    <style>
        /* 样式变量 */
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --text-primary: #e2e8f0;
            --accent: #38bdf8;
        }
        /* 模块卡片、布局等样式 */
    </style>
</head>
<body>
    <!-- 总览页面 -->
    <div id="overview-page">
        <!-- 模块组 1 -->
        <div class="module-group">
            <div class="group-title">组名</div>
            <div class="modules">
                <div class="module-card" onclick="showDetail('moduleId')">
                    <div class="module-title">模块名</div>
                    <div class="module-file">文件路径</div>
                    <div class="module-desc">描述</div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- 详情页面 -->
    <div id="detail-page" style="display:none"></div>
    
    <script>
        const moduleDetails = { /* 模块数据 */ };
        
        function showDetail(moduleId) {
            // 渲染详情页
        }
        
        function showOverview() {
            // 返回总览
        }
        
        // ESC 返回总览
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') showOverview();
        });
    </script>
</body>
</html>
```

为每个模块定义详情内容：

```javascript
const moduleDetails = {
    moduleId: {
        title: '模块名称',
        file: '文件路径',
        description: '模块职责说明',
        sections: [
            {
                title: '架构设计',
                content: '<div class="architecture-diagram">...</div>'
            },
            {
                title: '核心功能',
                content: '<ul class="feature-list">...</ul>'
            },
            {
                title: '使用示例',
                content: '<div class="code-block">...</div>'
            }
        ]
    }
};
```

内容组织建议：
- **架构设计** - 数据流、依赖关系、交互图
- **核心功能** - 关键特性列表
- **使用示例** - 代码片段或调用方式
- **依赖关系** - 引用的其他模块
- **配置说明** - 参数、选项、环境变量

### 步骤 5：添加可视化图表

使用基于 CSS 的架构图：

```html
<div class="architecture-diagram">
    <div class="diagram-box">
        <div class="diagram-title">分组名称</div>
        <ul class="diagram-list">
            <li>元素 1</li>
            <li>元素 2</li>
        </ul>
        <!-- 嵌套结构 -->
        <div class="diagram-nested">
            <div class="diagram-box">...</div>
        </div>
    </div>
</div>
```

### 步骤 6：实现导航

添加导航函数：

```javascript
function showDetail(moduleId) {
    const detail = moduleDetails[moduleId];
    // 构建详情页 HTML
    let content = '...';
    
    document.getElementById('overview-page').style.display = 'none';
    document.getElementById('detail-page').style.display = 'block';
    document.getElementById('detail-page').innerHTML = content;
}

function showOverview() {
    document.getElementById('overview-page').style.display = 'block';
    document.getElementById('detail-page').style.display = 'none';
}

// ESC 键返回
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') showOverview();
});
```

## CSS 样式模式

### 模块卡片模式

```css
.module-card {
    background: linear-gradient(135deg, #1e293b, #334155);
    border: 1px solid #475569;
    border-radius: 12px;
    padding: 16px;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
}

.module-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 30px rgba(56, 189, 248, 0.2);
}
```

### 流程图模式

```css
.flow-diagram {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.flow-item {
    background: #1e293b;
    border: 2px solid #38bdf8;
    border-radius: 8px;
    padding: 12px 20px;
    text-align: center;
}

.flow-arrow-down::after {
    content: '↓';
    color: #38bdf8;
    font-size: 24px;
}
```

### 代码块样式

```css
.code-block {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    border: 1px solid #334155;
    border-radius: 10px;
    overflow: hidden;
}

.code-header {
    background: #1e293b;
    padding: 8px 16px;
    border-bottom: 1px solid #334155;
    display: flex;
    align-items: center;
}

.code-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 6px;
}

.code-dot.red { background: #f87171; }
.code-dot.yellow { background: #fbbf24; }
.code-dot.green { background: #34d399; }

/* 语法高亮 */
.kw { color: #c084fc; }      /* 关键字 */
.str { color: #34d399; }     /* 字符串 */
.num { color: #fbbf24; }     /* 数字 */
.fn { color: #38bdf8; }      /* 函数 */
.cm { color: #64748b; }      /* 注释 */
```

## 自定义指南

### 更改配色方案

```css
:root {
    --bg-primary: #0f172a;      /* 深蓝色 */
    --bg-secondary: #1e293b;    /* 浅蓝色 */
    --accent: #38bdf8;          /* 青色 */
    --success: #34d399;         /* 绿色 */
    --warning: #fbbf24;         /* 黄色 */
    --error: #f87171;           /* 红色 */
}
```

### 添加新模块

1. 在总览网格中添加卡片：
```html
<div class="module-card" onclick="showDetail('newModule')">
    <div class="module-icon">🆕</div>
    <div class="module-title">新模块</div>
    <div class="module-file">src/new/module.ts</div>
</div>
```

2. 添加到 moduleDetails 注册表：
```javascript
newModule: {
    title: '🆕 新模块',
    file: 'src/new/module.ts',
    description: '描述内容',
    sections: [...]
}
```

### 添加新章节类型

```javascript
{
    title: '📊 统计信息',
    content: '<div class="stats-grid">...</div>'
}
```

配合 CSS：
```css
.stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
}
```

## 最佳实践

1. **保持单文件** - 无外部依赖，易于分享
2. **使用语义化 HTML** - 合适的标题、列表、章节
3. **响应式设计** - 使用 flexbox/grid，在移动端测试
4. **键盘导航** - 支持 ESC 返回
5. **渐进增强** - 无 JavaScript 也能工作（显示总览）
6. **性能优化** - 如果模块很多，考虑延迟加载详情内容
7. **无障碍访问** - ARIA 标签、对比度

## 常见陷阱

- **模板字符串冲突** - 避免在 JavaScript 字符串中使用 `${{ }}`（使用拼接）
- **文件过大** - 拆分章节，考虑延迟加载
- **嵌套过深** - 扁平化架构图，避免超过 3 层
- **缺少返回导航** - 始终包含返回按钮
- **硬编码路径** - 使用相对路径或可配置路径

## 输出示例

生成的文件可直接在任何浏览器中打开：

```bash
open architecture.html        # macOS
xdg-open architecture.html    # Linux
start architecture.html       # Windows
```

或通过 HTTP 服务：

```bash
python -m http.server 8080
# 打开 http://localhost:8080/architecture.html
```

## 参考

- [./assets/template.html](./assets/template.html) - 启动 HTML 模板
- [./examples/opencli-architecture.html](./examples/opencli-architecture.html) - 示例输出
