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
