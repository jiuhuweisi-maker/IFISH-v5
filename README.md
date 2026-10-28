# IFISH · V5

**有想法，就有办法。**

83 秒角色概念宣传片，1920 × 1080、60 fps。包含成片、GPT 生图素材、二维运动设计、完整渲染代码与检查记录。

![IFISH](output/IFISH_v5_cover.jpg)

## 观看与下载

- [完整视频 · 83 秒 / 1080p60](output/IFISH_v5_83s_1080p60.mp4)
- [开场预览 · 14.4 秒](output/IFISH_v5_motion_review.mp4)
- [镜头总览](output/IFISH_v5_storyboard.jpg)
- [鲸鱼标志 SVG](output/IFISH_mark.svg) / [透明 PNG](output/IFISH_mark.png)

## 影片内容

| 时间 | 内容 |
| --- | --- |
| 0–8.61 秒 | 二维圆点、对话气泡、圆环、彩边扇形、三色胶囊连续变化 |
| 8.61–13.83 秒 | 角色揭晓：“不止可爱” |
| 13.83–24.28 秒 | 推理与解题：合并算式，得到 180 |
| 24.28–34.72 秒 | 写作与改写：从初稿与词语进入最终文案 |
| 34.72–45.16 秒 | 编程与运行：代码生成、操作与对应折线输出 |
| 45.16–53.37 秒 | 中英翻译：词组沿轨迹进入排版 |
| 53.37–60.08 秒 | 深海蓝、暮砂棕、云瓷白，三款配色 |
| 60.08–70.52 秒 | “大白饭”划掉，改成“大米饭”，吃饭桥段 |
| 70.52–83 秒 | 功能收束、原创鲸鱼标志与 IFISH 字标 |

三项新动作素材（引导、吃饭、编程）由内置 GPT 生图工具生成，三色基础图沿用同系列内置生图素材。使用中的六张图均在 `assets/`，完整提示词见 [native_prompts_v5.json](work/native_prompts_v5.json)。

动画使用平面路径形变、动态排字、移动图形遮罩和角色局部二维网格形变；角色保留收藏公仔的摄影质感。渲染采用 8 倍空间抗锯齿、每帧 3 个时间采样。九处段落交接均采用 1.12 秒移动遮罩。

## 工程目录

```text
assets/                  六张角色素材
output/                  完整视频、开场预览、封面、镜头总览、标志
source/                  渲染所需的参考原音轨与来源说明
work/render_v5.py        影片编排与输出
work/kinetic_engine.py   角色形变与场景合成
work/flat_engine.py      平面图形、路径和文字绘制
work/export_mark.py      标志导出
work/verify_v5.py        时长、解码、音轨与逐帧检查
work/timeline_v5.json    精确时码
work/qa/                 最终编码抽帧、检查结果与审看记录
```

## 重渲染

制作环境为 Windows、Python 3.11+、支持 OpenGL 3.3 的显卡、带 NVIDIA NVENC 的 FFmpeg。字体使用 Windows 系统字体；FFmpeg 和 FFprobe 需要位于 PATH。已记录制作时使用的 Python 依赖版本。

```powershell
python -m pip install -r requirements.txt

# 只生成镜头总览和封面
python work/render_v5.py --preview-only

# 输出完整 83 秒影片
python work/render_v5.py

# 检查成片
python work/verify_v5.py

# 重新导出标志
python work/export_mark.py
```

重渲染只使用仓库中的素材与音轨，不调用生图服务，不需要 API 密钥。生成的临时音频、逐帧预览、日志和 Python 缓存已通过 `.gitignore` 排除。

## 检查记录

成片为 83.000 秒、4980 帧，完整解码无错误；保留参考片连续原音轨。详见 [编码与逐帧检查](work/qa/verification_v5.json) 和 [最终审看记录](work/qa/final_review.md)。`SHA256SUMS.txt` 记录本次交付文件的哈希。

## 参考与素材来源

视觉与配乐参考：[用户指定的 Bilibili 影片](https://www.bilibili.com/video/BV1dBpRzsEsd/)，上传者为二月山_Estrella；配乐为 Terror Jr《3 Strikes》，影片使用该参考音轨的前 83 秒。

二维图形衔接的补充参考：[Apple / Wonderful Tools 作品说明](https://www.oneclub.org/awards/adcawards/-award/35295/wonderful-tools/)。功能方向参考 [DeepSeek-R1](https://github.com/deepseek-ai/DeepSeek-R1) 与 [DeepSeek-V3](https://github.com/deepseek-ai/DeepSeek-V3) 官方说明；片中算式、文案、代码与翻译为概念演示。

角色原始形象来自用户提供的 DeepSeek、Claude、GPT 人形图片。原始角色和第三方音乐的权利归其各自权利人；仓库公开不代表第三方素材具有开放授权。
