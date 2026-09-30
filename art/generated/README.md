# 第一批原创舰船与建筑素材

这四张透明源图由内置 ImageGen 生成，用于本模组的原创俯视 2D 太空单位；没有复制《群星》或第三方模组素材。工具接口未返回底层模型的具体版本，因此这里不声称已确认使用 `gpt-image-2`。

| 源图 | 游戏素材 | 目标尺寸 | 设计要点 |
|---|---|---:|---|
| `corvette-source.png` | `corvette.png` | 32×32 | 细长箭形船体、单炮塔、双推进器 |
| `destroyer-source.png` | `destroyer.png` | 48×48 | 叉形舰首、两组点防御炮、短后翼 |
| `battleship-source.png` | `battleship.png` | 80×80 | 装甲楔形舰首、侧置引擎舱、双重炮 |
| `titan-source.png` | `titan.png` | 96×96 | 纵贯式主炮、阶梯装甲堡垒、多组引擎 |
| `cruiser-source.png` | `cruiser.png` | 64×64 | 细长舰脊、后掠侧翼、多组侧炮 |
| `starbase-source.png` | `starbase.png` | 64×64 | 环状主枢纽、四组船坞与防御臂 |
| `shipyard-source.png` | `shipyard.png` | 64×64 | 开放式中央船位、两侧造船架和吊臂 |
| `generator-source.png` | `generator.png` | 48×48 | 金色反应堆、四组蓝色集能翼 |
| `mining_station-source.png` | `mining_station.png` | 48×48 | 钻臂与矿物储舱、工业核心 |

共同提示词约束：原创科幻设计，严格俯视正投影，主体居中，透明背景；蓝灰色金属装甲、青色能量导管和少量暖金色核心；在游戏小尺寸下有可辨认的外形；无场景、文字、标志或水印。其余几张图使用前一张已生成图作为风格参考，但各自保留不同轮廓。`tools/make_sprites.py` 从源图的非透明区域裁切、等比缩小并居中，同时导出灰暗残骸图；动能护卫舰、动能驱逐舰、导弹巡洋舰和导弹战列舰的变体也基于新图导出。

当前仅完成这九种主体的替换。其他建筑、舰船、阵营外观、炮塔、弹道和音效仍按内容规范继续制作。视觉可读性已在原生贴图尺寸的合成预览中检查；实际对局中的辨识度仍需测试。
