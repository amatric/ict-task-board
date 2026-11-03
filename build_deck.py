#!/usr/bin/env python3
"""用 python-pptx 按「内容 → 版式函数」的方式生成演示文稿。

用法：python3 build_deck.py
输出：AI开发者空间-PPT制作实践.pptx
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

NAVY = RGBColor(0x0B, 0x12, 0x20)
TEAL = RGBColor(0x5E, 0xEA, 0xD4)
MUTED = RGBColor(0x8B, 0x9A, 0xB8)
WHITE = RGBColor(0xE8, 0xEE, 0xFC)

# ---- 内容层：只描述「讲什么」，不含坐标与字号 ----
DECK = {
    "title": "AI 开发者空间 · PPT 制作实践",
    "subtitle": "用 python-pptx 把结构化内容自动排版成演示文稿",
    "meta": "华为 ICT 大赛云赛道 · 赛题16 参评作品",
    "sections": [
        {"heading": "为什么要自动化出 PPT", "points": [
            "手工排版是一次性工作，做三遍就要重复三次",
            "模板一改，历史稿件全部要重排",
            "内容与版式耦合，改一个字可能挤掉整页",
            "批量产出（周报 / 路演 / 答辩）时最费时间",
        ]},
        {"heading": "方案：内容与版式分离", "points": [
            "内容层：JSON / 字典描述标题、要点、章节",
            "版式层：一组可复用的页面函数（封面 / 要点 / 章节 / 结尾）",
            "渲染层：按内容驱动版式函数，直接产出 .pptx",
            "改主题色只改变量，所有页面同步生效",
        ]},
        {"heading": "四个排版约束", "points": [
            "字号阶梯：42 / 32 / 20 / 16 / 14，只用这几档",
            "留白优先：正文左边界固定，不与标题抢空间",
            "对比优先：深底浅字，强调色只用于数字与关键词",
            "一页一观点：要点不超过 4 条，每条不超过两行",
        ]},
    ],
    "closing": {"headline": "内容驱动，版式复用", "sub": "改内容不动版式，改版式不动内容"},
}

# ---- 版式层 ----
def bg(slide):
    f = slide.background.fill
    f.solid()
    f.fore_color.rgb = NAVY


def accent_bar(slide):
    bar = slide.shapes.add_shape(1, Inches(0.9), Inches(1.55), Inches(1.2), Inches(0.08))
    bar.fill.solid()
    bar.fill.fore_color.rgb = TEAL
    bar.line.fill.background()


def text_box(slide, left, top, width, height, content, size, bold=False,
             color=WHITE, align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = content
    p.alignment = align
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    return tb


def bullet_list(slide, top, items, size=18):
    tb = slide.shapes.add_textbox(Inches(0.9), Inches(top), Inches(11.4), Inches(4.6))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = "· " + it
        p.font.size = Pt(size)
        p.font.color.rgb = WHITE
        p.space_after = Pt(10)


def slide_title(slide, title_text):
    text_box(slide, 0.9, 0.9, 11.5, 0.8, title_text, 32, bold=True)
    accent_bar(slide)


# ---- 渲染层 ----
def build(deck: dict, out: str) -> None:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # 封面
    s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
    text_box(s, 0.9, 2.2, 11.5, 1.2, deck["title"], 42, bold=True)
    text_box(s, 0.9, 3.5, 11.5, 0.8, deck["subtitle"], 20, color=TEAL)
    text_box(s, 0.9, 4.6, 11.5, 0.6, deck["meta"], 14, color=MUTED)
    accent_bar(s)

    # 正文
    for sec in deck["sections"]:
        s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
        slide_title(s, sec["heading"])
        bullet_list(s, 2.1, sec["points"])

    # 结尾
    s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
    text_box(s, 0.9, 2.6, 11.5, 1.0, deck["closing"]["headline"], 40, bold=True, color=TEAL)
    text_box(s, 0.9, 3.9, 11.5, 0.7, deck["closing"]["sub"], 20, color=MUTED)

    prs.save(out)
    print(f"[OK] 生成 {out}，共 {len(prs.slides._sldIdLst)} 页")


if __name__ == "__main__":
    build(DECK, "AI开发者空间-PPT制作实践.pptx")
