# 贡献者指南

感谢参与 Rusted Stellaris 的开发。当前设计和实现状态从 `.agents/DESIGN.md` 与 `.agents/TODO.md` 查阅，项目约定见 `AGENTS.md`。

模组源文件位于 `mod/rusted-stellaris/`，地图位于 `maps/`，构建与验证脚本位于 `tools/`。

## 构建含原创配乐的开发包

安装 uv 和 FFmpeg（包含 `ffprobe`），在项目根目录执行：

```text
uv sync --locked
uv run --locked python tools/validate_mod.py
uv run --locked python tools/validate_maps.py
uv run --locked python tools/build_music.py
uv run --locked python tools/build_mod.py
```

首次构建按固定版本与 SHA-256 下载 CC0 乐器采样；后续复用本机缓存。四首原创配乐由版本化的作曲源码生成，OGG 位于 `build/music/`，由打包脚本加入 `.rwmod`。`work/` 内的采样、试听与渲染文件，`build/` 内的 OGG、包及验证结果均不提交。直接复制 `mod/` 目录不会带上生成的音乐；目录安装时应解压构建完成的 `.rwmod`。

## 自动检查、打包与发布

[GitHub Actions](https://github.com/noctisynth/rusted-stellaris/actions) 使用 Semifold 管理版本和发布。工具固定为 **Semifold 0.3.4**，配置在 `.changes/config.toml`。`pyproject.toml` 同时管理模组版本、Python 要求和构建依赖，Semifold 使用内置 `python` resolver。`publish = false` 禁止发布到 PyPI，仅分发 GitHub 上的模组附件。版本提升后执行 `uv lock` 同步锁文件。

本地与 CI 都使用 uv 0.12.23、`.python-version` 指定的 Python 3.12 和 `uv.lock` 锁定依赖。`uv sync --locked` 创建本地 `.venv`，`uv run --locked python ...` 使用该环境，无需手动激活。添加依赖使用 `uv add`，并提交 `pyproject.toml` 和 `uv.lock`；`.venv` 和缓存不提交。FFmpeg 是外部工具，仍需单独安装。

维护者明确要求：**代理不得合并 PR**。目前 `0.1.0` 版本计划仍由待合并的版本 PR 管理，是否合并发布由维护者决定。Python 中的预发布版本使用 PEP 440 表示（例如 `0.1.0a0`），Semifold 将其识别为 `0.1.0-alpha.0`。

- 在 Windows 和 Linux 上检查单位配置、贴图引用、地图及 Git 产物忽略状态。
- 检查成功后，在 Linux 上从源码生成四首配乐并打包完整 `.rwmod`。CC0 采样有缓存，每次构建仍核验其 SHA-256；生成音乐不复用缓存。
- **Quality** 在 PR 或手动触发时运行，也被主分支的 **Semifold CI** 复用。成功后上传保留 30 天的 `rusted-stellaris-<commit>` 附件，包含 `.rwmod`、`SHA256SUMS.txt` 和版本/提交信息。打开成功运行的 **Artifacts** 下载，解压外层 ZIP 后安装其中的 `.rwmod`。联机双方使用同一份包，可比较 SHA-256 确认。
- **Semifold Status** 在 PR 中预览版本计划并模拟版本提升，使用 GitHub 提供的临时令牌更新版本计划评论。
- **Semifold CI** 在 `main` 上先完成同一提交的全部质量检查和打包，再执行 `semifold ci`：有 changeset 时维护独立的 `release` 分支和版本 PR，更新版本与 `CHANGELOG.md`；合并版本 PR 后，没有待消费 changeset 时发布 GitHub Release，并上传已经验证的安装包及校验信息。
- 按维护者 2026-10-05 的发布决定，模组使用稳定通道，首个版本为 `0.1.0`，标签形如 `rusted-stellaris-v0.1.0`。版本号不代表所有玩法、联机及移动端已完成验收。完成实测后再合并版本 PR；合并是发布入口，不再手工推送 `v*` 标签或创建 Release 草稿。不要手动修改版本或提前消费 changeset。

日常开发完成后创建并提交 changeset，例如：

```text
semifold commit --name improve-fleet --package rusted-stellaris=patch --tag fix --summary "修复舰队行为"
semifold status
semifold version --dry-run
```

工作流使用 GitHub 提供的临时令牌，无需配置个人访问令牌或 registry token。Semifold CI 的发布作业具有仓库和 PR 写权限；Semifold Status 有 PR 评论权限；构建、采样、日志均不写回 Git。首次启用需把配置推送到 GitHub，并在仓库 **Settings → Actions → General** 允许 Actions 创建 Pull Request。机器人创建的版本 PR 如显示 CI 等待批准，由维护者在 Actions 页面处理；也可在 Quality 页面选择 `release` 分支手动检查，合并后仍会强制运行主分支质量门禁。

CI 不包含商业游戏程序，也不执行游戏内载入、建造、战斗、完整对局或联机测试。这些仍需本机验收，移动端单独记录。工作流配置见 `.github/workflows/quality.yaml`、`semifold-ci.yaml` 和 `semifold-status.yaml`。

## Steam 创意工坊更新

`Semifold CI` 的 `publish` output 报告 `rusted-stellaris` 发布成功后，同一次工作流才自动更新 Steam 创意工坊。版本 PR 阶段不会上传。Steam 作业使用 output 中的版本号定位 GitHub Release，从该 Release 下载 `.rwmod`、校验 SHA-256 和包内版本，解压完整模组，再通过 Valve SteamCMD 更新 Rusted Warfare（App ID `647960`）的现有条目 `3813493737`。作业在 Windows 运行器上使用由 Windows SteamCMD 生成的登录配置。脚本只在 VDF 中写入固定的现有条目 ID、内容目录和更新说明；封面文件 `mod-thumbnail.png` 存在时才提交封面字段。条目的标题、长篇描述和公开状态由 Steam 网页管理。

首次使用时，由拥有该条目的 Steam 账号在本机用 SteamCMD 登录并完成 Steam Guard 验证，确认之后运行 `steamcmd +login <用户名> +quit` 可直接进入。将该 SteamCMD 目录下 `config/config.vdf` 的原始字节编码为 Base64，在 GitHub 仓库配置两个 Actions Secret：`STEAM_USERNAME`（用户名）与 `STEAM_CONFIG_VDF_BASE64`（Base64 编码后的完整文件）。这个配置包含可复用的登录凭据，只保存在 Secret 中，不提交、上传为 artifact 或打印到日志。认证失效时需要在本机重新登录并更新 Secret。GitHub 的临时运行器不保证刷新后的登录配置能自动回写 Secret。

工作流使用官方 SteamCMD。维护者合并版本 PR 后，Semifold 发布 GitHub Release 并顺序触发 Steam 更新；代理不会合并 PR。如果 GitHub Release 成功而 Steam 上传失败，可以从 Actions 手动运行 `Retry Steam Workshop`，输入已经发布的标签。重试作业使用同一份已发布附件和校验流程，不重新发布 GitHub Release。第一次线上运行时，需确认 SteamCMD 接受该账号授权、`workshop_build_item` 更新原条目且订阅者可以完整载入，并核对页面内容与封面。SteamCMD 运行错误可从 Actions 日志排查；未经过这次实测前，不把云端工坊发布视为已验收。
