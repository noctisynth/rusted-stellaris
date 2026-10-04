# rusted-stellaris 设计索引

> 状态：Active
> 更新：2026-09-30  
> 作用：记录模组目标、权威文档及设计成熟度

## 目标

制作贴近《群星》原作名称与世界观的《铁锈战争》太空整合模组。开工前确定完整内容范围，包括阵营、经济、科技、建筑、舰船、巨构、地图、素材和验收标准。电脑版为首个验证环境，手机版兼容性以实测为准。

## 文档地图

| 文档 | 状态 | 用途 |
|---|---|---|
| [完整模组范围](rfcs/0001-complete-mod-scope.md) | Accepted RFC | 完整交付范围与验收标准 |
| [普通地图中子灭杀](rfcs/0002-ordinary-map-neutron.md) | Accepted RFC | 地面清除、建筑中立与舰队豁免的目标及验证边界 |
| [内容清单](specs/content-roster.md) | Active Spec | 建筑、舰船、阵营和科技的逐项交付清单 |
| [基础生产链](specs/core-loop.md) | Active Spec | 首批可独立验证的生产链，不改变完整目标 |
| [星域地图基础结构](specs/starfield-maps.md) | Active Spec | 三张地图的地形、出生与基础资源，不代替行星机制 |
| [行星与巨像](specs/planets-and-colossus.md) | Active Spec | 行星状态、三种终局武器及验收条件 |
| [舰队对地与平衡](specs/combat-balance.md) | Active Spec | 轨道轰炸与对原版单位的首轮数值基线 |
| [原创配乐](specs/music.md) | Active Spec | 四首纯音乐、模组专属播放及音频构建边界 |
| [本机参考资料](spikes/local-references.md) | 已核对 | 游戏安装、内置示例及已安装模组的位置与可用性 |
| [舰队学院存档实验](spikes/fleet-academy-save.md) | 已核对 | 动态属性训练导致游戏 1.15 存档失败；后续应改验证可保存的机制 |
| [实施清单索引](TODO.md) | Discovery | 等范围确认后建立分项清单 |

完整范围已按用户继续完成全部设计预期的要求接受。当前基础生产链和星域地图底稿已有实现，内容清单负责追踪其余交付项。技术可行性未验证的机制要在对应验证记录中保持明确状态。
