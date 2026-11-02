# 任务管理看板（Task Board）

华为 ICT 大赛云赛道 赛题1（AI应用开发-发布作品领取激励）的参评作品。

纯前端单文件实现，无需后端、无需构建，直接打开 `index.html` 即可运行。

## 功能

- **新建任务卡片**：标题、描述、分类（工作 / 学习 / 生活）
- **三列看板**：待办 / 进行中 / 已完成
- **拖拽切换状态**：把卡片拖到目标列即可变更状态
- **按分类筛选**：顶部标签一键筛选，列计数实时更新
- **本地持久化**：数据保存到 `localStorage`，刷新页面不丢失
- **删除任务**：卡片右上角 ×

## 运行方式

```bash
# 方式一：直接打开
open index.html

# 方式二：起一个本地静态服务
python3 -m http.server 8000
# 然后访问 http://localhost:8000
```

## 技术说明

- 原生 HTML + CSS + JavaScript，无任何第三方依赖
- 拖拽基于 HTML5 Drag and Drop API
- 状态存储于 `localStorage` 的 `ict-task-board-v1` 键

## 目录结构

```
.
├── index.html   # 全部界面、样式与逻辑
└── README.md
```
