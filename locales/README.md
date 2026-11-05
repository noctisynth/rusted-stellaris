# 中英文翻译

`zh.json` 和 `en.json` 是当前模组文案的权威来源，按稳定的语义键管理；`bindings.json` 将 `相对文件路径::配置段::字段` 绑定到翻译键。相同文案可共享一个键。已有键不随文案修改而改名。

覆盖单位/建筑/行星名称与说明、资源名称、按钮、科技与建造限制、放置提示，以及本方、敌方、盟友和全体事件公告。技术 ID、标签、地图文件名、动作名和数值不翻译。音乐署名文件本来就是中英双语，作品标题和模组品牌保留原名。

## 修改与生成

1. 编辑两个语言 JSON 中的对应键；新增文本时在两个语言表中增加同一个键，并在 `bindings.json` 中增加目标位置。
2. 执行 `uv run --locked python tools/localization.py --write`。
3. 执行 `uv run --locked python tools/localization.py --check`、`uv run --locked python -m unittest discover -s tests`，然后执行现有单位和地图检查。
4. 提交语言表、绑定表及生成后的 INI/TMX。构建拒绝缺译、未收录的新文本、失效绑定、占位符不一致或过期生成结果。

INI 和资源模板里的文案是生成结果，不应手改。无后缀默认值及 `_en` 使用英文，`_zh` 使用简体中文。例如：

```ini
displayText: Corvette
displayText_zh: 护卫舰
displayText_en: Corvette
```

英文回退也覆盖引擎强制英文模式的空语言代码和未翻译语言。中文游戏使用 `zh`。每个子配置明确覆盖自己的语言字段，避免继承父单位的旧翻译。游戏本身支持哪些界面语言由游戏决定，本工具不增加新的语言菜单。

JSON 中写 `\\n` 来表示引擎换行；禁止真实换行注入 INI。`%{self.playerName}`、`${...}` 等运行时占位符必须在两种翻译中保持一致。改名不能修改 `name`、资源键或地图触发器 ID。

`make_planet_states.py`、`make_planet_units.py` 和 `make_maps.py` 在生成内容后同步本地化。行星显示名由语言表读取。旧的 `make_planet_units.py` 入口委托完整状态生成器，防止重建名称时删除行星状态与受击机制。

## 公告、地图和模组信息

RW 1.15 的 `showMessageToPlayer`、`showMessageToAllEnemyPlayers`、`showMessageToAllPlayers` 原生支持 `_zh`、`_en`，保持原来的接收范围与触发逻辑。只在本机显示时选择语言，不按语言分叉同步游戏逻辑。

TMX 文本使用同样的属性后缀：

- `map_info` 对象的 `introText`：关卡简报。
- 触发器的 `globalMessage`：地图公告。
- `type="mapText"` 对象的 `text`：地图上的文字。

地图绑定格式为 `maps/地图文件.tmx::object:对象ID::字段`。例如 `maps/example.tmx::object:1::introText`，生成 `introText`、`introText_zh` 和 `introText_en` 三个属性。对象的 `name`、`id`、`activatedBy` 不变。三张正式星域地图目前没有这三类文本；它们的行星名称及歼星公告来自单位配置，已经全部翻译。未新增任务说明或剧情。

地图文件名没有在本项目核实的模组级本地化机制，因此保持原路径。`mod-info.txt` 的 `title` 与 `description` 是普通字符串：保留品牌，简介由同一翻译表生成中英并列文本，不添加游戏无法消费的语言字段。

## 本机验证

```text
uv run --locked python tools/probe_localization.py --game-dir "D:/SteamLibrary/steamapps/common/Rusted Warfare"
uv run --locked python tools/smoke_game_maps.py --game-dir work/i18n-game
uv run --locked python tools/smoke_game_localization.py --game-dir work/i18n-game
```

首条命令只调用本机游戏的原生解析器，不改动安装目录；需要游戏自带 JDK。它检查全部文案的中英解析、空语言与其他语言回退，并通过真实 TMX 对象解析器验证三类地图文本。后两条必须使用仓库 `work/` 中预先准备的独立游戏副本和完整模组，不能指向日常游玩目录。对局回归临时创建独立探针单位与地图，使用原护卫舰武器；验证排队生产、敌方建筑死亡事件、正常存档和实际单人胜利标记，退出后删除探针文件。

该短局刻意采用免费生产和 1 点生命的无武装靶标，只是本地化改动的生命周期回归，不证明正式经济、平衡或长局体验。测试不应同时使用同一游戏副本。实测范围见 [验证记录](../.agents/spikes/i18n.md)。
