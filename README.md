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

[GitHub Actions](https://github.com/noctisynth/rusted-stellaris/actions/workflows/build.yml) 在向 `main` 推送、向 `main` 提交 PR、推送 `v*` 标签时运行，也可在 Actions 页面选择 **Run workflow** 手动构建。

- 在 Windows 和 Linux 上检查单位配置、贴图引用、地图及 Git 产物忽略状态。
- 检查成功后，在 Linux 上从源码生成四首配乐并打包完整 `.rwmod`。CC0 采样有缓存，每次构建仍核验其 SHA-256；生成音乐不复用缓存。
- 每次成功构建上传保留 30 天的 `rusted-stellaris-<commit>` 附件，包含 `.rwmod`、`SHA256SUMS.txt` 和提交/运行信息。打开成功运行的 **Artifacts** 下载，解压外层 ZIP 后安装其中的 `.rwmod`。联机双方使用同一份包，可比较 SHA-256 确认。
- 推送 `v*` 版本标签会将同一份构建产物附加到 **Release 草稿**，标记为预发布；完成游戏实测后在 GitHub 上手动发布。已有同名 Release 时创建步骤会失败，不覆盖已发布附件；需要修订时使用新版本标签。

工作流使用 GitHub 提供的临时令牌，无需配置个人访问令牌。只有标签触发的 Release 作业具有仓库写权限；构建、采样、日志均不写回 Git。首次启用需把工作流提交并推送到 GitHub，仓库须允许 Actions 运行。

CI 不包含商业游戏程序，也不执行游戏内载入、建造、战斗、完整对局或联机测试。这些仍需本机验收，移动端单独记录。工作流配置见 `.github/workflows/build.yml`。
