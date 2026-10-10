# Changelog

## v0.2.1

### Bug Fixes

- [`dff1d7f`](https://github.com/noctisynth/rusted-stellaris/commit/dff1d7fef42c6041bdf448183b570441e751d622): 主宰服役播报保留标题与分段换行，删除段落间空白行以减少屏幕遮挡
- [`0555a32`](https://github.com/noctisynth/rusted-stellaris/commit/0555a32be0195a915df86d786b15baa6ec13e4c1): 放大主宰横向移动船坞的显示尺寸，使整体舰体体量明显大于泰坦，保留原贴图与战斗数值
- [`07d5299`](https://github.com/noctisynth/rusted-stellaris/commit/07d5299a6432433f22fc100c0c5827b6bb1c8150): 矿物处理厂的科技要求与单座数量上限分开提示，修复已有建筑时误报缺少科技

### New Features

- [`7158481`](https://github.com/noctisynth/rusted-stellaris/commit/715848161bb207dda0f0f28e611f8ec589a0eafe): 巨像服役采用建造者、敌对帝国及盟友三种文案，盟友接收内部消息并按队伍去重
- [`3480057`](https://github.com/noctisynth/rusted-stellaris/commit/348005795b06c60667868bd7120ee455245917e7): 主宰提供650范围火力指挥光环，同队与盟友作战星舰伤害和射速各提高10%，与学院统一计算，支持撤销与正常存读档

## v0.2.0

### Bug Fixes

- [`722d330`](https://github.com/noctisynth/rusted-stellaris/commit/722d330b2a04bed59f3ed35a211ace46b2069622): 舰队学院限制为每队一座，训练改为保留舰名的原地加成；学院被摧毁或拆除后撤销加成，支持升级和正常存读档，并删除旧精锐舰型
- [`2d87d49`](https://github.com/noctisynth/rusted-stellaris/commit/2d87d49bb2dbebe2daaf39914d177c2507d005cf): 参考原版舰体关系适度调整神秘战巡舰，增强悖论泰坦的耐久、重炮和射程，并同步学院训练数值
- [`7704cd9`](https://github.com/noctisynth/rusted-stellaris/commit/7704cd92bfd080cdbdc1064bd239691ce2579dd9): 修正天机研究所变更集的未配置标签，恢复发布计划加载，并补充标签排错说明
- [`2766393`](https://github.com/noctisynth/rusted-stellaris/commit/27663935560a4270be88fe7696f646d5a8e36902): 将模组安装包改为按正式版本号命名，并同步 GitHub Release 与 Steam 工坊发布流程

### New Features

- [`7704cd9`](https://github.com/noctisynth/rusted-stellaris/commit/7704cd92bfd080cdbdc1064bd239691ce2579dd9): 主宰旁观者完工公告采用帝王的杀手锏文案，与建造者视角分开发送
- [`55b15e1`](https://github.com/noctisynth/rusted-stellaris/commit/55b15e12deda896e06055ba4f6f7066d0dfd8c42): 重绘主宰为横向双翼移动船坞造型
- [`93b51f7`](https://github.com/noctisynth/rusted-stellaris/commit/93b51f7ccdfd4636968259fb9d0cc18939bc2878): 科学枢纽完工后可研究天机工程并建造天机研究所，低概率突破密语护航舰、神秘战巡舰和失落帝国泰坦科技，新增原创立绘、舰船武器及生产入口
- [`321928a`](https://github.com/noctisynth/rusted-stellaris/commit/321928a743d75c4cf454f0eb712da03e91879677): 新增原创 Steam 工坊封面和舰队、巨构、巨像主题展示图。

## v0.1.0

### Chores

- [`2e4012c`](https://github.com/noctisynth/rusted-stellaris/commit/2e4012ca312d282a8bb6d7b5b1383b0c69c3e7dd): 使用 uv 和 pyproject.toml 统一 Python 构建环境、依赖锁定与 Semifold 版本管理，移除占位 package.json 和外部项目文档引用。

### New Features

- [`35e13d7`](https://github.com/noctisynth/rusted-stellaris/commit/35e13d727cf10fd61ce78314a62b6b91b44b0360): 发布 Rusted Stellaris 0.1.0，包含三种帝国开局、星际经济与科技、舰队和星港、巨构与巨像、三张星域地图以及四首原创配乐。

    移除模组名称中的 Development 标记，README 面向玩家介绍模组，开发、构建和发布说明移入贡献者指南。多人及移动端仍待实测。
