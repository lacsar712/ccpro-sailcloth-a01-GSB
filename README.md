# SailCloth-01 · 帆布浸渍防水台

帆布间布卷与浸渍固化台账基线项目（Django 5 + DRF + Vue 3 SPA）。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Django 5 · DRF · SimpleJWT · django-cors-headers · Gunicorn |
| 前端 | Vue 3 · Vite · Pinia · Vue Router |
| 数据库 | PostgreSQL 15 |
| 部署 | Docker Compose · Nginx（前端反代 `/api`） |

## 路径与端口

- **项目路径**：`d:\work\document\bytecode\claudeCodePro\SailCloth\SailCloth-01`
- **前端**：http://localhost:3740
- **API**：http://localhost:8740
- **PostgreSQL**：localhost:6140

## 演示账号

| 用户名 | 密码 | 角色 |
| --- | --- | --- |
| `admin` | `123456` | 管理员 |
| `worker` | `123456` | 操作工 |

登录页已预填 `admin` / `123456`。后端 entrypoint 执行 migrate + seed。

## 业务规则

布卷状态不可设为「已固化」（`cured`），除非同时满足：

1. 该卷**最近一条** `DipRun` 的 `cureHours` 已记录且 **≥ 12**；
2. 该卷存在至少一张**未作废**且**起泡级数为 0** 的盐雾试片合格条（`SaltSprayCoupon`）。

盐雾试片条字段：布卷、条号（从 1 起）、起泡级数（仅 0–5 整数）、检验时刻、检验人、作废时刻（可空）。
同卷未作废条号唯一（数据库部分唯一约束兜底并发）；操作工可建条，作废仅管理员。

规则实现：`backend/core/rules.py`

## 快速启动

```bash
cd d:\work\document\bytecode\claudeCodePro\SailCloth\SailCloth-01
docker compose up --build
```

浏览器打开 http://localhost:3740

## SPA 信息架构

- **登录** → 进入主工作面
- 顶部导航栏：**晾晒架** · **盐雾试片** · 布卷台账 · 浸渍台账
- **`/` 帆布间晾晒架（主）**：按帆布间挂布卷芯片（挂签状态 `raw` / `dipping` / `cured`）；点击打开右侧面板登记 `DipRun`、切换固化状态、查看本卷盐雾试片；架下为浸渍流水次要信息流
- **`/coupons` 盐雾试片（专页）**：按卷筛选、新建检验条、管理员作废
- **`/rolls` · `/dips`（次要台账）**：保留列表/表单 CRUD，非主路径

API 契约不变（JWT、`/api/lofts|rolls|dips|coupons|dashboard/`）。

## 配色

海军蓝（navy）+ 帆布米色（canvas），与温室绿主题区分。
