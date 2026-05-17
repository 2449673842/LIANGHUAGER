# GitHub 发布说明

当前目录还不是 Git 仓库，发布到 GitHub 前需要先初始化仓库并绑定远程地址。

## 方式 A：发布到已有 GitHub 仓库

在你提供仓库地址后，可以执行：

```powershell
cd E:\codex版本实盘回测
git init
git add .
git commit -m "docs: publish upgraded workbench documentation"
git branch -M main
git remote add origin https://github.com/<owner>/<repo>.git
git push -u origin main
```

## 方式 B：先创建 GitHub 仓库

如果还没有仓库：

1. 在 GitHub 新建一个空仓库。
2. 不要勾选自动生成 README、`.gitignore` 或 License。
3. 把仓库地址发给我。
4. 我再帮你初始化、提交并推送。

## GitHub Pages

如果要把 `docs` 目录作为文档站：

1. 进入 GitHub 仓库页面。
2. 打开 `Settings -> Pages`。
3. Source 选择 `Deploy from a branch`。
4. Branch 选择 `main`。
5. Folder 选择 `/docs`。
6. 保存后等待 GitHub Pages 构建。

文档首页是：

```text
docs/index.md
```

## 发布前建议

- 不要提交 `node_modules`、`dist`、`__pycache__`、`.env`。
- 如要公开仓库，确认没有 OKX API Key、Secret、Passphrase 或邮箱授权码。
- 如果后续要接真实交易，实盘配置必须留在本地环境变量或私有配置中。
