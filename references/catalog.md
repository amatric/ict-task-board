# 华为云能力目录（与 skills_index.json 同源）

共 17 条。用 `scripts/search_skills.py` 检索。

## 计算（2）
- **弹性云服务器 ECS** `ecs-basic` — 通用计算实例，用于部署后端服务、网站、数据库客户端。
  - 关键词：服务器, 虚拟机, 主机, 部署, 跑服务, ecs
  - 接入：`控制台 / API: POST /v1/{project_id}/cloudservers`
- **函数工作流 FunctionGraph** `fgs-func` — 按需执行的事件驱动计算，适合定时任务、Webhook、轻量 API。
  - 关键词：函数, serverless, 定时, 事件, 轻量, fgs, 按需
  - 接入：`控制台 / API: POST /v2/{project_id}/fgs/functions`

## 存储（1）
- **对象存储 OBS + 生命周期** `obs-lifecycle` — 海量非结构化存储，生命周期规则可自动把冷数据转低频/归档，显著降本。
  - 关键词：存储, 对象存储, 归档, 日志, 图片, 备份, 便宜, obs
  - 接入：`obsutil / API: PUT /?lifecycle`

## 数据库（4）
- **云数据库 RDS for MySQL** `rds-mysql` — 托管 MySQL，自带主备、备份、只读实例与参数模板。
  - 关键词：数据库, mysql, 关系型, 读写分离, 备份, 高可用
  - 接入：`控制台 / API: POST /v3/{project_id}/instances`
- **数据复制服务 DRS** `drs-migration` — 在线迁移/实时同步，支持 MySQL/PG/GaussDB 等，先预检查再全量+增量。
  - 关键词：迁移, 同步, 上云, 数据搬迁, drs
  - 接入：`控制台 → 数据复制服务 → 创建迁移任务`
- **数据仓库 DWS / GaussDB(DWS)** `dws-olap` — 列存 MPP 数仓，适合海量数据聚合分析与报表。
  - 关键词：数仓, olap, 分析, 报表, 大数据, dws, 海量
  - 接入：`控制台 / API: POST /v1.0/{project_id}/clusters`
- **云搜索服务 CSS** `css-search` — 托管 Elasticsearch/OpenSearch，做全文检索与日志分析。
  - 关键词：搜索, 全文检索, elasticsearch, 日志检索, css, opensearch
  - 接入：`REST: PUT /{index}`

## AI（3）
- **ModelArts 模型训练与部署** `modelarts-train` — 托管训练作业 + 在线服务部署，支持自定义镜像与自动学习。
  - 关键词：训练, 模型, 推理, 部署, ai, modelarts, 微调
  - 接入：`控制台 / SDK: modelarts.session.Session`
- **MaaS 模型即服务** `maas-llm` — 按 token 计费直接调大模型推理接口，兼容 OpenAI 风格。
  - 关键词：大模型, llm, 推理, api, 问答, 对话, deepseek
  - 接入：`POST /v1/chat/completions`
- **文字识别 OCR** `ocr-text` — 从图片/PDF 中提取文字，支持通用表格、票据、证件等专用模板。
  - 关键词：图片, 文字识别, ocr, 票据, 身份证, 截图, 提取文字
  - 接入：`控制台 / API: POST /v2/{project_id}/ocr/general-text`

## 容器（1）
- **云容器引擎 CCE** `cce-k8s` — 托管 K8s 集群，支持节点池、弹性伸缩、负载均衡 Ingress。
  - 关键词：容器, kubernetes, k8s, 编排, 微服务, cce
  - 接入：`控制台 / kubectl`

## 网络（1）
- **弹性负载均衡 ELB + 弹性伸缩 AS** `elb-ha` — ELB 分发流量，AS 按 CPU/定时策略自动增减实例，组合成弹性架构。
  - 关键词：负载均衡, 高可用, 扩容, 流量, elb, as
  - 接入：`控制台 / API: POST /v2/{project_id}/elb/loadbalancers`

## 安全（2）
- **IAM 委托与 STS 临时凭证** `iam-sts` — 用委托 + AssumeAgency 换 900 秒 STS 临时凭证，避免长期 AK/SK 落盘。
  - 关键词：权限, 凭证, 临时, 安全, sts, 委托, iam
  - 接入：`hcloud sts AssumeAgency / IAM API`
- **WAF + DDoS 高防** `waf-ddos` — WAF 拦应用层攻击，DDoS 高防抗流量攻击。
  - 关键词：防护, 攻击, ddos, waf, 安全, cc攻击, 网站防护
  - 接入：`控制台 → WAF → 添加防护域名`

## 运维（2）
- **云运维中心 COC 批量命令** `coc-runcommand` — 对多台 ECS 批量下发脚本/命令，适合巡检与批量变更。
  - 关键词：批量, 命令, 运维, 脚本, 巡检, coc
  - 接入：`控制台 / API: POST /v1/{project_id}/coc/commands`
- **应用运维管理 AOM 监控告警** `aom-monitor` — 指标/日志/告警统一入口，可对 ECS、容器、自定义指标设阈值告警。
  - 关键词：监控, 告警, 日志, 指标, aom, 可观测
  - 接入：`控制台 / API: POST /v2/{project_id}/aom/alarm-rules`

## 研发（1）
- **CodeArts 流水线** `codearts-pipeline` — 代码检查→构建→测试→部署全链路，支持容器镜像推送与灰度。
  - 关键词：ci, cd, 流水线, 构建, 发布, codearts
  - 接入：`控制台 / CodeArts Pipeline`
