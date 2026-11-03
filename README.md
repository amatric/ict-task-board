# Git 代码时光机 · 代码版本管理实践

华为 ICT 大赛云赛道 **赛题4（Git-代码时光机掌握代码版本管理）** 的参评作品。

本作品不是一篇文档，而是一个**真实保留了完整 Git 演进历史的仓库**——把版本管理的关键操作都实际做过一遍，并留下可验证的痕迹（分支、合并、冲突解决、回滚、打标签）。

## 仓库里能看到什么

```bash
git log --oneline --graph --decorate --all   # 完整演进图
git branch -a                                 # 全部分支
git tag                                       # 发布标签
```

实际发生过的演进：

| 阶段 | 操作 | 对应命令 |
|:--|:--|:--|
| 初始化 | 主线首个提交 | `git init` / `git commit` |
| 特性分支 | 拉出 `feature/calculator` 独立开发（2 个原子提交） | `git checkout -b` |
| 并行开发 | 同时拉出 `feature/formatter`，与上一条并行 | `git checkout -b` |
| 合并 | 先把 calculator 合回 main | `git merge --no-ff` |
| **冲突解决** | 两条分支改了同一文件，手工解冲突后提交合并 | `git merge` + 手工解 |
| 发布 | 打语义化标签 | `git tag -a v1.0.0` |
| 错误提交 | 改坏了格式化实现（丢了千分位） | `git commit` |
| **回滚** | 用 revert 撤销，历史完整保留 | `git revert` |

演进图（`git log --graph` 实际输出）：

```
* 018786a Revert "refactor(format): 简化 format_number 实现"
* f6615ec refactor(format): 简化 format_number 实现
*   92022dc (tag: v1.0.0) merge: 合并 feature/formatter，解决冲突
|\
| * 6f0d0f1 feat(format): 新增 format_number 数字格式化
* |   a06f7ff merge: 合并 feature/calculator（乘法与除法）
|\ \
| * 0ba3c46 feat(calc): 新增除法 div 并做除零保护
| * 179205b feat(calc): 新增乘法 mul
|/
* deb4526 chore: 初始化仓库与计算工具骨架
```

## 被管理的代码

零依赖 Python 小工具 `calc.py`：

- `add` / `sub` / `mul` / `div`（`div` 有除零保护）
- `format_number`（保留两位小数 + 千分位）

配套 `test_calc.py`，6 个用例覆盖正常与边界：

```bash
python3 test_calc.py     # Ran 6 tests ... OK
```

## 目录结构

```
.
├── calc.py          # 计算工具
├── test_calc.py     # 单元测试
└── README.md
```

## 命令速查（本仓库实践过的）

```bash
# 看拓扑
git log --oneline --graph --decorate --all

# 看某次提交改了什么
git show <commit>

# 撤销已推送的错误提交（安全，保留历史）
git revert <commit>

# 暂存半成品
git stash -u && git stash list && git stash pop

# 合并最近 3 个提交
git rebase -i HEAD~3

# 二分定位引入 bug 的提交
git bisect start && git bisect bad && git bisect good <known-good>
```
