# API 说明

后端默认地址：`http://127.0.0.1:8100`

所有业务接口统一挂在 `/api` 下，响应形状为：

```json
{
  "success": true,
  "data": {}
}
```

## 健康检查

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/health` | 后端健康检查 |

## 行情

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/market/candles` | 获取 K 线数据 |
| `GET` | `/api/market/snapshot` | 获取行情快照和盘口 |

`/api/market/candles` 参数：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `instrument_id` | `BTC-USDT` | 交易对 |
| `timeframe` | `15m` | K 线周期 |
| `limit` | `160` | 返回条数，范围 50-500 |

## 总览工作台

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/workbench/overview` | 首页总览数据 |
| `GET` | `/api/watchlist` | 获取自选列表 |
| `POST` | `/api/watchlist` | 添加自选 |
| `DELETE` | `/api/watchlist` | 删除自选 |
| `GET` | `/api/monitoring/state` | 获取监控状态 |
| `POST` | `/api/monitoring/state` | 设置监控状态 |

添加自选请求体：

```json
{
  "symbol": "ETH-USDT"
}
```

设置监控状态请求体：

```json
{
  "running": true
}
```

## 模拟/实盘

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/execution/state` | 执行页完整状态 |
| `GET` | `/api/execution/accounts` | 获取账户列表 |
| `POST` | `/api/execution/accounts` | 新增账户 |
| `GET` | `/api/execution/queues` | 获取执行队列 |
| `POST` | `/api/execution/queues` | 新增执行队列任务 |

新增账户请求体：

```json
{
  "name": "OKX 主账户",
  "venue": "OKX",
  "equity": "100000 USDT",
  "status": "待确认"
}
```

新增执行任务请求体：

```json
{
  "strategy": "趋势跟随-A",
  "symbol": "BTC-USDT",
  "action": "开多",
  "reason": "15m 突破确认"
}
```

## 回测

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/backtests/workbench` | 回测工作台数据 |
| `POST` | `/api/backtests/run` | 按参数运行回测 |

运行回测请求体：

```json
{
  "period": "3M"
}
```

当前 `period` 支持：`1M`、`3M`、`6M`、`1Y`。

## 策略

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/strategies/board` | 策略中心列表 |
| `POST` | `/api/strategies/import` | 导入策略模板 |

策略导入当前使用查询参数：

```text
POST /api/strategies/import?label=趋势跟随-B&instrumentId=BTC-USDT&timeframe=15m
```

## 数据来源标识

多数工作台接口会返回 `source` 和 `upstreamConnected`：

| source | 含义 |
| --- | --- |
| `okx-cli` | 来自 OKX Agent CLI |
| `okx-public` | 来自 OKX 公共 REST |
| `upstream` | 来自旧 `quant_platform` 上游 |
| `fallback` | 来自本地兜底数据 |
