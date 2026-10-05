# 天机科技原创素材记录

> 2026-10-06；内置 image_gen / imagegen 技能；原创生成并导入项目。

## 原作参考

本机 `D:/SteamLibrary/steamapps/common/Stellaris/gfx/models/ships/fallen_empire_01/` 的 `fallen_empire_small_warship.mesh`、`fallen_empire_large_warship.mesh`、`fallen_empire_titan.mesh` 用于核对三舰轮廓。简体中文 `machine_age_l_simp_chinese.yml` 中的两项科技名称为“密语护航舰”和“神秘战巡舰”。模型的俯视研究图仅留在忽略目录 `work/fallen-original-model-study.png`，没有模型、原版纹理或研究图进入安装包。

本次生成使用原版轮廓研究图作为参考输入，制作原创象牙白/香槟金装甲、石墨凹槽、青色发光结构。泰坦统一尖锐舰艏朝上；三舰和研究所均采用正交俯视、透明背景。不是将原版模型渲染图缩小当作交付贴图。

## 交付文件

| 素材 | 源图 | 游戏纹理/残骸 | 世界显示尺寸 |
|---|---|---|---:|
| 密语护航舰 | art/generated/riddle_escort-source.png | units/riddle_escort{,_dead}.png | 64 |
| 神秘战巡舰 | art/generated/enigma_battlecruiser-source.png | units/enigma_battlecruiser{,_dead}.png | 96 |
| 失落帝国泰坦 | art/generated/fallen_titan-source.png | units/fallen_titan{,_dead}.png | 112 |
| 天机研究所 | art/generated/tianji_institute-source.png | units/tianji_institute{,_dead}.png | 64 |

游戏纹理按既有 `tools/make_sprites.py` 的 alpha 裁切与居中导出流程生成，保留透明通道，尺寸不超过 384。残骸使用项目已有灰暗化流程。生成源图的四个角透明，三舰 1024×1536 RGBA，建筑 1254×1254 RGBA。全部原图保留在仓库中，游戏安装包只带导出纹理。

## 生成提示集

三舰公共提示：

```text
Create an ORIGINAL production game sprite for Rusted Stellaris, inspired by the design language of the Stellaris base game's fallen empire fleet. The provided image is an IGNORE-output reference study of the original ship silhouettes: left=escort, middle=battlecruiser, right=titan. Do not copy its polygons or texture; create a new detailed design. Strict ORTHOGRAPHIC directly overhead top view, nose points straight UP at 12 o'clock, bilateral symmetry, no perspective, no tilt, entire ship visible centered with 12% margin. Antique ivory and champagne metallic hull plating, dark graphite recesses and fine turquoise emissive circuitry, advanced ancient restrained high-tech ceremonial architecture, beautiful crisp manufactured beveled panels, realistic rendered metal, clear silhouette at RTS scale. No text, labels, stars, backdrop, frame or ground shadow. One ship only. Transparent background with genuine alpha. Preserve shape readability, avoid huge exhaust flames or detached pieces.
```

每舰追加提示：

```text
Asset: 密语护航舰 / Riddle Escort. Refer to LEFT silhouette. Slender elongated double-pointed dart body, long narrow tapered bow, compact diamond waist with four small swept fin shoulders, tapering stern. Compact high-tech escort, twin tiny azure engine ports at stern. Fine gold armor strips along long taper. Bow upward.

Asset: 神秘战巡舰 / Enigma Battlecruiser. Refer to MIDDLE silhouette. Broader and heavier elongated diamond warship with distinctive TWO closely spaced long pointed forward prongs, central filled command citadel at the broad angular waist, small outward wing shoulders, tapering stern with paired engine nozzles. Solid hull, no huge empty loop or hole. Two spinal cannon sockets integrated along the front prongs. Bow upward.

Asset: 失落帝国泰坦 / Fallen Empire Titan. Refer to RIGHT silhouette. Very long imposing capital ship, narrow needle-shaped long forebody and powerful axial cannon at upper tip, a broad swept pair of angular shoulder blades around the middle, narrow armored central keel, wider clustered stern citadel with layered buttresses and 3 restrained small blue engine ports at the bottom. Rotate reference design as necessary so sharp slender NOSE points UP. Longer and more majestic than battlecruiser, no hollow center, no gigantic engines. One original titan sprite.
```

研究所提示：

```text
Create an original high quality RTS science-building sprite, orthographic DIRECTLY OVERHEAD TOP VIEW, single structure centered isolated on genuine transparent background. 天机研究所, an advanced ancient-technology institute in a science fiction Stellaris-inspired mod. Solid octagonal ivory and champagne metal research complex, four symmetric angular lab wings around a filled central cyan-glowing enigmatic crystalline computation chamber, an inner delicate gold ring and small turquoise energy conduits, graphite recesses, restrained ancient lost-empire design language. Dense architectural surface detail but strong readable silhouette at 64 game pixels. No spaceships, no flying loose pieces, no ground, no space scene, no text, no symbols resembling writing, no shadow outside structure, no perspective tilt. Whole building inside canvas with 12% margins, game asset production render.
```
