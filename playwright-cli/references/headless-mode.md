# Headless Mode with playwright-cli

## 基本结论

- `playwright-cli` 默认是 headless；想看见浏览器时才在 `open` 上加 `--headed`
- CLI 没有单独的 `open --headless` 参数，因为默认行为已经是 headless
- 对 coding agent 来说，headless 通常是首选：干扰少、速度稳定、适合在远程环境持续调用

## 推荐工作流

### 模式 1：证据优先

```bash
playwright-cli -s=checkout open https://example.com/checkout
playwright-cli -s=checkout snapshot --filename=01-start.yaml
playwright-cli -s=checkout fill e8 "user@example.com"
playwright-cli -s=checkout screenshot --filename=02-filled.png
playwright-cli -s=checkout console warning
playwright-cli -s=checkout network
```

适合：调试、截图留证、让用户复查。

### 模式 2：固定输出目录

如果一个任务会生成很多 artifact，最好用配置文件固定 headless、viewport 和输出目录：

```json
{
  "browser": {
    "launchOptions": {
      "headless": true
    },
    "contextOptions": {
      "viewport": {
        "width": 1440,
        "height": 900
      }
    }
  },
  "outputDir": ".playwright-cli/headless",
  "outputMode": "file"
}
```

```bash
playwright-cli open https://example.com --config=playwright-cli.json
playwright-cli snapshot
playwright-cli screenshot --filename=home.png
```

适合：CI、远程 shell、批量任务、需要可重复 artifact 的流程。

## 何时从 headless 升级到 headed

这些场景再切 `--headed` 会更省时间：

- 需要人工参与登录、验证码、MFA 或权限弹窗
- 交互依赖复杂 hover、拖拽、动画时序，想实时观察
- 用户明确要求“看着浏览器操作”
- 你已经拿到 `snapshot` / `console` / `network` / `screenshot`，但还缺最后一层可视确认

如果只是想看 session，而不是彻底改成 headed，先试：

```bash
playwright-cli show
```

## 常见坑

- 没看到浏览器窗口就判断失败：默认 headless 正常如此
- 只做交互不存证据：至少保留一个 `snapshot` 和一个命名 `screenshot`
- 依赖 `type` 但没有确认焦点：需要精确定位时优先 `fill <ref> <text>`
- 页面变化后继续用旧 ref：每次结构明显变化后重新 `snapshot`
- artifact 都是时间戳文件：需要交付结果时显式传 `--filename`

## 给 agent 的默认策略

1. 先用 headless 跑通最短路径
2. 在关键节点保存 `snapshot` / `screenshot`
3. 发现异常后追加 `console` / `network`
4. 只有在可视确认明显更快时才切 `--headed`
