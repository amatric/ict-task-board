# AI 开发者空间 · PPT 制作实践

华为 ICT 大赛云赛道 **赛题16（基于 AI 开发者空间的 PPT 制作实践）** 的参评作品。

用 `python-pptx` 把**结构化内容 + 可复用版式函数**渲染成演示文稿：改内容不动版式，改版式不动内容。

## 产出

- `AI开发者空间-PPT制作实践.pptx` —— 5 页成品（封面 / 3 个正文页 / 结尾）
- `build_deck.py` —— 生成脚本（内容层 + 版式层 + 渲染层）
- `基于AI开发者空间的PPT制作实践.md` —— 实践文档

## 运行

```bash
pip install python-pptx
python3 build_deck.py
# [OK] 生成 AI开发者空间-PPT制作实践.pptx，共 5 页
```

## 三层结构

```python
# 内容层：只说讲什么
DECK = {
    "title": "...", "subtitle": "...", "meta": "...",
    "sections": [{"heading": "...", "points": [...]}, ...],
    "closing": {"headline": "...", "sub": "..."},
}

# 版式层：6 个可复用函数
bg(slide) / accent_bar(slide) / text_box(...) / bullet_list(...) / slide_title(...) / build(deck, out)
```

## 四个排版约束

1. 字号阶梯只有 42 / 32 / 20 / 16 / 14
2. 正文左边界固定，不与标题抢空间
3. 深底浅字，强调色只给关键信息
4. 一页一观点，要点 ≤ 4 条

详见 [基于AI开发者空间的PPT制作实践.md](基于AI开发者空间的PPT制作实践.md)。
