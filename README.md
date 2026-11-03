# AI 智慧课堂工作台

华为 ICT 大赛云赛道 **赛题17（AI 智慧课堂工作台实践）** 的参评作品。

一条命令跑通 **备课 → 出题 → 批改 → 学情分析** 的教学闭环，四个环节用 JSON 串起来，零第三方依赖。

## 四个子命令

```bash
python3 classroom.py lesson --topic "循环与迭代" --grade 高一 --minutes 45   # 备课：给时间分配
python3 classroom.py quiz   --topic "循环与迭代" --count 5 --out quiz.json   # 出题：按题型抽
python3 classroom.py grade  --quiz quiz.json --answers ans.json             # 批改：rubric 命中率
python3 classroom.py report --grades grades.json                            # 学情：给教学建议
```

## 关键设计

- **备课给的是时间分配**（导入 11% / 讲解 27% / 例题 20% / 练习 29% / 小结 13%），不是知识点罗列
- **批改返回 `missing`**：不只给分，还告诉学生哪条要点没写到
- **学情输出教学动作**：题型均分最低的优先专项训练，未覆盖人次最多的优先回讲

实际输出见 [AI智慧课堂工作台实践.md](AI智慧课堂工作台实践.md)。

## 自测

```bash
python3 classroom.py lesson --topic "循环与迭代"
python3 classroom.py quiz --topic "函数与参数" --count 2
```
