# Git 代码时光机 · 代码版本管理实践

华为 ICT 大赛云赛道 **赛题4（Git-代码时光机掌握代码版本管理）** 的参评作品。

本作品不是一篇文档，而是一个**真实保留了完整 Git 演进历史的仓库**——把版本管理的关键操作都实际做过一遍，并留下可验证的痕迹（分支、合并、冲突解决、回滚、暂存）。

## 仓库里能看到什么

```bash
git log --oneline --graph --all      # 完整的演进图
git branch -a                        # 全部分支
git tag                              # 发布标签
```

演进过程：

| 阶段 | 操作 | 对应命令 |
|:--|:--|:--|
| 初始化 | 建立主线和首个提交 | `git init` / `git commit` |
| 特性分支 | 从 main 拉出 `feature/calculator`，独立开发 | `git checkout -b` |
| 迭代提交 | 多个原子的、语义清晰的提交 | `git commit -m` |
| 并行开发 | 再拉 `feature/formatter` 与上一条分支并行 | `git checkout -b` |
| 合并 | 把两条特性分支合回 main | `git merge` |
| 冲突解决 | 两条分支改了同一处，手工解冲突后提交 | `git merge` + 手工解 |
| 发布 | 打上语义化标签 | `git tag -a v1.0.0` |
| 回滚 | 用 revert 撤销一次错误提交（保留历史） | `git revert` |
| 暂存 | 用 stash 暂存半成品，切分支处理紧急问题后再恢复 | `git stash` / `git stash pop` |
| 提交整理 | 用 rebase -i 把草稿提交压成一个 | `git rebase -i` |

## 被管理的代码

一个零依赖的 Python 小工具 `calc.py`，包含：

- `add` / `sub` / `mul` / `div` 四则运算（`div` 有除零保护）
- `format_number` 数字格式化（保留两位小数、千分位）

配套 `test_calc.py` 单元测试，覆盖正常与边界情况。

```bash
python3 test_calc.py
```

## 目录结构

```
.
├── calc.py          # 计算工具
├── test_calc.py     # 单元测试
└── README.md
```

## 关键命令速查（本仓库实践过的）

```bash
# 查看历史与分支拓扑
git log --oneline --graph --all --decorate

# 查看某次提交改了什么
git show <commit>

# 撤销一次已推送的错误提交（安全，保留历史）
git revert <commit>

# 暂存当前改动
git stash -u
git stash list
git stash pop

# 交互式整理最近 3 个提交
git rebase -i HEAD~3

# 找出引入 bug 的那次提交
git bisect start
git bisect bad
git bisect good <known-good>
```
