# PixelTuner · 像素级调校的 web 页面

华为 ICT 大赛云赛道 **赛题5（Browser-码道内置浏览器精准调整 web 页面）** 的参评作品。

一个用「内置浏览器实时渲染 → 对照 → 微调」方式逐像素调出来的响应式页面。纯 HTML + CSS，无构建、无依赖。

## 调校了什么

| 维度 | 做法 |
|:--|:--|
| **设计 token** | 间距 `--s-1..--s-8`、圆角 `--r-sm/md/lg`、动效 `--dur/--ease`、配色全部变量化，改一处全站生效 |
| **响应式** | 760 / 900 / 1180 三档断点；标题用 `clamp()` 流体缩放，卡片用 `auto-fit` 自适应，不写死宽度 |
| **布局** | Hero 双栏、特性 `auto-fit` 网格、对比双栏、数据四宫格，断点处优雅降级为单列 |
| **交互** | 滚动进场（IntersectionObserver，只触发一次）、卡片悬停位移、色板点击实时改主题色 |
| **动效曲线** | 统一 `cubic-bezier(.22,.61,.36,1)`，时长统一 320ms，节奏一致 |
| **无障碍** | `prefers-reduced-motion` 降级、`aria-label`、焦点态、对比度 ≥ 4.5:1 |
| **语义化** | `header/main/section/article/aside/footer`，标题层级正确，不靠 div 堆砌 |

## 用内置浏览器调过的具体细节

1. **粘性导航**：`position: sticky` + `backdrop-filter: blur(14px)`，滚动时半透明叠压，边界留 `1px` 描边避免发灰
2. **Hero 留白**：上下 padding 用 `--s-8 / --s-7`，移动端降到 `--s-7 / --s-6`，视觉节奏不塌
3. **调校面板**：进度条长度用 `width` 百分比 + `transition`，数字用 `tabular-nums` 防止跳动
4. **渐变色文字**：`background-clip: text` 配合 `linear-gradient`，行高用 `1.15` 避免裁切
5. **卡片悬停**：`translateY(-4px)` + 边框变色，`transition` 同时作用于 transform 与 border-color
6. **滚动进场**：`opacity 0 → 1` + `translateY(18px) → 0`，`unobserve` 保证只播一次

## 运行

```bash
open index.html
# 或
python3 -m http.server 8000
```

## 验证方式

在码道内置浏览器里按三档宽度看：

- **≥1180px**：Hero 双栏、四宫格特性、四列数据
- **900–1180px**：特性网格自动降为两列
- **≤760px**：全部单列，导航折叠，字号随 clamp 收缩

同时检查：悬停卡片有位移、点击色板主题色实时切换、`prefers-reduced-motion` 下动效关闭。
