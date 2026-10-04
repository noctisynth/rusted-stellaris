# Rusted Stellaris

《群星》题材的《铁锈战争》非官方同人模组，仍在开发中。完整范围和完成情况分别见 `.agents/DESIGN.md` 与 `.agents/TODO.md`。

当前开发版已有三种帝国开局、原生 `$` 能量经济、科技与舰船生产、星港升级、舰队学院、巨构、巨像三种行星结局，以及三张专用星域地图。内容能够在本机游戏 1.15 载入并用于实际试玩；尚未完成完整对局、平衡、多人及移动端验收。

玩家操作与已知限制见 [试玩指南](docs/试玩指南.md)。模组源文件位于 `mod/rusted-stellaris/`，三张地图位于 `maps/`，打包文件由 `python tools/build_mod.py` 生成到 `build/rusted-stellaris-dev.rwmod`。

## 构建含原创配乐的开发包

安装 Python、FFmpeg（包含 `ffprobe`）和音频构建依赖后执行：

```text
python -m pip install -r tools/music/requirements.txt
python tools/build_music.py
python tools/build_mod.py
```

首次构建按固定版本与 SHA-256 下载 CC0 乐器采样；后续复用本机缓存。四首原创配乐由版本化的作曲源码生成，OGG 位于 `build/music/`，由打包脚本加入 `.rwmod`。`work/` 内的采样、试听与渲染文件，`build/` 内的 OGG、包及验证结果均不提交。直接复制 `mod/` 目录不会带上生成的音乐；目录安装时应解压构建完成的 `.rwmod`。

## 自动检查、打包与发布

[GitHub Actions](https://github.com/noctisynth/rusted-stellaris/actions) 使用与 `armillae` 相同的 Semifold 发布流程。工具固定为 **Semifold 0.3.4**，配置在 `.changes/config.toml`。`package.json` 仅作为模组版本清单，由内置 `nodejs` resolver 修改；`private: true`、`publish = false` 和空发布命令禁止 npm 发布，无需安装 Node.js。

- 在 Windows 和 Linux 上检查单位配置、贴图引用、地图及 Git 产物忽略状态。
- 检查成功后，在 Linux 上从源码生成四首配乐并打包完整 `.rwmod`。CC0 采样有缓存，每次构建仍核验其 SHA-256；生成音乐不复用缓存。
- **Quality** 在 PR 或手动触发时运行，也被主分支的 **Semifold CI** 复用。成功后上传保留 30 天的 `rusted-stellaris-<commit>` 附件，包含 `.rwmod`、`SHA256SUMS.txt` 和版本/提交信息。打开成功运行的 **Artifacts** 下载，解压外层 ZIP 后安装其中的 `.rwmod`。联机双方使用同一份包，可比较 SHA-256 确认。
- **Semifold Status** 在 PR 中预览版本计划并模拟版本提升，仅使用读取权限，不自动评论。
- **Semifold CI** 在 `main` 上先完成同一提交的全部质量检查和打包，再执行 `semifold ci`：有 changeset 时维护独立的 `release` 分支和版本 PR，更新版本与 `CHANGELOG.md`；合并版本 PR 后，没有待消费 changeset 时发布 GitHub Release，并上传已经验证的安装包及校验信息。首次 changeset 计划发布 `0.1.0-alpha.1`。
- 模组保持 `alpha` 通道，Semifold 自动创建预发布，标签形如 `rusted-stellaris-v0.1.0-alpha.1`。完成实测后再合并版本 PR；合并是发布入口，不再手工推送 `v*` 标签或创建 Release 草稿。不要手动修改版本或提前消费 changeset。

日常开发完成后创建并提交 changeset，例如：

```text
semifold commit --name improve-fleet --package rusted-stellaris=patch --tag fix --summary "修复舰队行为"
semifold status
semifold version --dry-run
```

工作流使用 GitHub 提供的临时令牌，无需配置个人访问令牌或 registry token。只有 Semifold CI 的发布作业具有仓库和 PR 写权限；构建、采样、日志均不写回 Git。首次启用需把配置推送到 GitHub，并在仓库 **Settings → Actions → General** 允许 Actions 创建 Pull Request。GitHub 临时令牌创建的版本 PR 不会自动触发新的 PR workflow；可在 Quality 页面选择 `release` 分支手动检查，合并后仍会强制运行主分支质量门禁。

CI 不包含商业游戏程序，也不执行游戏内载入、建造、战斗、完整对局或联机测试。这些仍需本机验收，移动端单独记录。工作流配置见 `.github/workflows/quality.yaml`、`semifold-ci.yaml` 和 `semifold-status.yaml`。
