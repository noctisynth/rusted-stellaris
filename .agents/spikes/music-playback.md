# 原创配乐接入与版本管理验证

> 日期：2026-10-04；本机 Steam 游戏 1.15；隔离实例 `work/music-game/`。

## 已确认

- 本机游戏解析器含 `sourceFolder`、`whenUsingUnitsFromThisMod_playExclusively`、`addToNormalPlaylist`；音乐控制器识别 `[noloop]`。
- 四首原创曲由 `tools/music/` 源码重新渲染。135 个 CC0 来源文件通过固定提交与 SHA-256 校验；OGG 均为可完整解码的 Vorbis、44.1 kHz、双声道，时长分别约 114.67、127、121.68、132.87 秒。
- `tools/build_mod.py` 的包包含四个 `music/*[noloop].ogg`、署名及 CC0 许可，不含 WAV、MP3、采样库或音乐构建脚本。缺少一首 OGG 时打包前检查确实拒绝，恢复后通过。
- 模组单位静态校验为 180 项；三张专用地图分别载入 120×90/23、140×140/41、180×180/75，并进入运行态、找到建造者。
- `tools/smoke_game_music.py --game-dir work/music-game --skip-natural` 实际依次播放了 `nebula_echoes`、`far_shore`、`luminous_departure`、`last_light`。进入专属播放后，没有再出现原版曲目的 `Now playing`。
- 独立自然轮换记录：`work/music-play.stdout.log` 中 15:54:23 播放 `luminous_departure`；无后续换曲命令的情况下，15:56:30 排入 `last_light`，15:56:34 淡入播放，证明完整歌曲结束后可以自动轮换。
- 主菜单初始化确实播放过原版 `music/starting/battletanks1B.ogg`，因此该配置不应宣传为全局替换主菜单音乐。
- 普通图 `Fire Bridge (2p)` 的隔离对局也触发了专属音乐。为压缩测试时间，给 AI 增加资金并使用 `debug.overrideDeltaSpeed(12.0)`；日志记录基地受攻击、单位受伤及 `Player has been wiped out (Team: A)`，即玩家被淘汰。前后存档的自定义对象条目从指挥中心/建造者扩展到发电区、造船厂、合金铸造厂、舰船等，覆盖建造与战斗阶段；该人为加速对局不用于数值平衡结论。原始日志和存档保留在 `work/music-match.*` 与隔离实例中。旧存档检查器不支持该普通图完整对象表，未以其报错结果宣称通过。
- 四首 OGG、署名与许可、`mod-info.txt` 已同步至本机游戏现有 `RustedStellarisDev` 目录。原配置备份在 `work/music-install-backup/`；游戏本体的音乐和全局音量未修改。

## 忽略检查

`git ls-files -ci --exclude-standard` 没有输出，当前索引中也没有 `.rwmod`、WAV、MP3、OGG、ZIP、日志、缓存或游戏测试副本。此前 `build/`、`work/`、`.rwmod` 和 Python 缓存已被正确忽略；这次补充全局音频成品、音色文件、日志和存档规则。已有 `art/generated/*-source.png` 是美术源素材，保留版本管理。

## 边界

该记录证明本机播放器与打包流程有效，不等于移动端或多人验证。完整模组的平衡、胜利条件及其余玩法验收沿用原有待办。音频不会写入游戏的原版音乐目录。
