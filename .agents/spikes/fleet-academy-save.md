# 舰队学院动态属性存档实验

> 2026-10-01；Rusted Warfare 1.15；隔离副本 `work/game-sandbox`

目标是验证舰队学院能否以 `setUnitStats` 给现役及新造舰船一次性的生命上限与火力加成，并在存档中保留结果。正式模组尚未接入该实现。

1. 隔离配置把护卫舰的训练动作设为自动触发，使用 `@memory`/`setUnitMemory` 记录已训练，再用 `setUnitStats` 提升属性。地图能载入，但 `root.saveGame` 报 `java.lang.NullPointerException`，调用栈经过 `game.units.custom.as.a` 与 `game.units.custom.j.a`。
2. 改用单位 `setFlag=1`/`hasFlag(id=1)` 记录已训练，保留动态属性加成，存档仍报同一空指针。
3. 移除 `setUnitStats` 而仅留单位 flag，存档成功；重新加入最小的 `setUnitStats: maxHp+=100`，同样报空指针。
4. 撤回实验配置，同一隔离地图再次成功保存，生成约 463 KiB 的正常存档。测试进程所需的重复存档文件先删除，避免游戏覆盖重命名失败混淆结论。

因此本机游戏 1.15 的这一条动态属性路径会破坏存档，不能以“能载入地图”作为交付依据。下一步验证独立的训练舰船变体及单位转换；新方案需要同时保持原配装、队伍、生命比例、数量限制、造船菜单和存档。实验中的舰队学院原创源图保留在 `art/generated/fleet_academy-source.png`，正式建筑配置与训练动作已撤回。
