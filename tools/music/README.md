# 原创音乐源码

`render_last_light.py` 编排《最后的星光》，`compose_three_voyages.py` 编排其余三首，`orchestra.py` 提供采样演奏和混响。固定随机种子保留配器与演奏细节；`tracks.json` 定义曲目时长及试听确认后的静态增益。

运行入口是 `python tools/build_music.py`，需要 NumPy、`ffmpeg` 和 `ffprobe`。初次构建从 VSCO 2 CE 官方仓库下载 `sample_provenance.json` 指定提交的文件，并核对每个文件的 SHA-256；`instruments.json` 保存相应音高与力度映射。`VSCO2-CC0.txt` 是采样许可。下载缓存和中间 WAV 留在被忽略的 `work/music/astra/`。

构建成品输出到 `build/music/`，使用 Ogg Vorbis、44.1 kHz、双声道和 `[noloop]` 文件名标记。`build-state.json` 保存源码摘要、OGG 摘要及解码信息；`tools/build_mod.py` 检查摘要后才将四首音乐加入包。需要完全重新生成时使用 `python tools/build_music.py --force`。

不要将采样、试听 MP3、WAV、OGG、缓存、事件列表或 `.rwmod` 强制加入 Git。提交包含作曲源码、音色映射、采样来源与哈希、曲目定义、许可和文档即可。此处没有《群星》原版音乐文件或旋律转录。
