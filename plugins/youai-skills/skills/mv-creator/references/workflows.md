# 工作流：导出、映射与排查

## 需要哪些工作流

| 类型 | 文件 | 必需 | 来源（ComfyUI 菜单 Workflow → Browse Templates） |
| --- | --- | --- | --- |
| `music` | `music.api.json` | 是 | MiniMax Music 3 音乐生成模板 |
| `i2v` | `i2v.api.json` | 是 | Wan2.2 14B Image to Video 模板 |
| `flf2v` | `flf2v.api.json` | 否 | Wan2.2 14B First-Last Frame to Video 模板（只有分镜用到首尾帧转场时需要） |
| 其他 | `<kind>.api.json` | 否 | 补帧、超分等，用 `comfy-run` 通用命令调用 |

导出的 `<kind>.api.json` 放在工作区的 `workflows/` 目录（`init-config` 会创建，可用配置 `workflows_dir` 修改）。参数映射 `<kind>.params.json` 随 skill 提供（`<SKILL_DIR>/workflows/`），一般不用动；需要自定义时，复制一份到工作区的 `workflows/` 再改，工作区的版本优先。

## 导出步骤

1. 在 ComfyUI 中打开模板，按提示下载模型，**先在界面里手动跑通一次**，确认模型、显存和效果都没问题。
2. 加速 LoRA、分辨率、步数等在界面里调好；脚本只会改下表中的参数，其余保持你导出时的设置。
3. 菜单 Workflow → **Export (API)**，保存为 `<kind>.api.json` 放进工作区的 `workflows/` 目录。注意不是普通的 Save/Export，普通格式会被脚本拒绝。
4. 运行 `mv.py comfy-validate`，全部 `[OK]` 即可使用。

模板更新、换模型后重新导出覆盖即可；只要节点结构不变，映射文件不用改。

## 脚本会注入的参数

| 类型 | 参数 | 默认怎么找节点 |
| --- | --- | --- |
| music | `caption` `lyrics` `max_duration` | `MiniMaxMusic3TextEncode` 节点的同名输入 |
| music | `seed` | 编码节点的 `seed`（若有），以及标题为 `@seed` 的节点 |
| i2v | `image` | 唯一的 `LoadImage` 节点 |
| i2v | `positive` / `negative` | 连到 `WanImageToVideo` 的 positive / negative 的 `CLIPTextEncode` |
| i2v | `width` `height` `length` | `WanImageToVideo` 节点 |
| i2v / flf2v | `seed` | 所有 `KSamplerAdvanced.noise_seed`（以及 `KSampler.seed`） |
| flf2v | `start_image` / `end_image` | 连到 `WanFirstLastFrameToVideo` 的 start_image / end_image 的 `LoadImage` |
| 全部 | `filename_prefix` | `SaveAudio*` / `SaveVideo` / `VHS_VideoCombine` 节点 |

## 自动找不到节点时：用标题标记

工作流改过结构（中间插了别的节点、有多个同类节点）时，`comfy-validate` 会报"匹配到多个节点"或"没有匹配到节点"。这时在 ComfyUI 里**把对应节点的标题改成约定名**再导出，标题优先于自动查找：

`@caption` `@lyrics` `@duration` `@seed` `@image` `@start_image` `@end_image` `@positive` `@negative` `@size`（宽高帧数所在节点） `@output`（保存节点）

查看工作流里有哪些节点、标题和参数：

```powershell
python <SKILL_DIR>\scripts\mv.py comfy-inspect workflows\i2v.api.json
```

## 映射文件格式（`<kind>.params.json`）

```json
{
  "workflow": "i2v.api.json",
  "output_ext": [".mp4"],
  "params": {
    "positive": {
      "required": true,
      "targets": [
        {"title": "@positive", "input": "text"},
        {"class_type": "CLIPTextEncode", "upstream": {"class_type": "WanImageToVideo", "input": "positive"}, "input": "text"}
      ]
    }
  }
}
```

- `targets` 是候选位置。`mode` 为 `first`（默认）时用第一个能匹配上的；为 `all` 时写入所有匹配到的位置（如两个采样器的 seed）。
- 选择器字段可组合：`id`（节点编号）、`title`（节点标题）、`class_type`（字符串或列表）、`upstream`（连到某节点某输入的上游节点）、`where`（输入值等于给定值）。
- 一个选择器匹配到多个节点会报错，除非写 `"multi": true`。
- `required` 表示调用时必须提供；`optional` 表示工作流里没有该节点时跳过。
- 输入如果由 Primitive 节点连线提供，脚本会改写那个 Primitive 节点的值。

新增其他工作流（如补帧）：在工作区 `workflows/` 里放 `post.params.json` 和 `post.api.json`，然后：

```powershell
python <SKILL_DIR>\scripts\mv.py comfy-run post --upload video=projects\xx\clips\S01\take-1.mp4 --set filename_prefix=mv-creator/post --out projects\xx\clips\S01 --name take-1-post
```

## 运行时报错排查

| 报错 | 常见原因 |
| --- | --- |
| `Value not in list: ckpt_name/unet_name ...` | 工作流里的模型文件名在这台 ComfyUI 上不存在：在界面里改成已有模型后重新导出 |
| `ComfyUI 缺少这些节点` | 自定义节点没装；用 Manager 安装或更新 ComfyUI |
| `执行失败 ... out of memory` | 降低分辨率/帧数，或在工作流里换 fp8/GGUF 模型、开启分块解码后重新导出 |
| 任务完成但没有输出文件 | 保存节点被禁用或换成了预览节点；`output_ext` 不包含实际扩展名 |
| 等待超时 | 任务仍在 ComfyUI 队列中，可在界面查看；需要时调大 `comfyui.timeout_sec` |

不要为了"跑通"擅自修改用户工作流中的模型、采样器或步数，先把报错告诉用户。
