# Gemini API 接口

该模型适配于 Gemini 端侧接口标准

Base Url： [https://maas-openapi.wanjiedata.com/api](https://maas-openapi.wanjiedata.com/api)

获取 [API KEY](https://www.wjark.com/center/api-key)：[https://www.wjark.com/center/api-key](https://www.wjark.com/center/api-key)

- Gemini 端侧接口标准适配模型一览表
  ：
  https://docs.wjark.com/maas/UserGuide/Usage/Google.html

## 基础文本对话

**模型：gemini-2.5-flash-lite**

**流式接口示例**

```shell
POST /v1beta/models/gemini-2.5-flash-lite:generateContent?alt=sse
```

**流式请求示例：**

```shell
export API_KEY="<你的 API KEY>"
export MODEL="gemini-2.5-flash-lite"
curl --location 'https://maas-openapi.wanjiedata.com/api/v1beta/models/gemini-2.5-flash-lite:generateContent?alt=sse' \
--header 'Content-Type: application/json' \
--header 'Authorization: $API_KEY' \
--data '{
    "contents": [
        {
            "parts": [
                {
                    "text": "你好"
                }
            ]
        }
    ]
}'
```

**流式响应示例：**

```shell
{
    "candidates":
        {
            "content": {
                "parts": [
                    {
                        "text": "你好！很高兴为你"
                    }
                ],
                "role": "model"
            },
            "index": 0
        },
    "modelVersion": "gemini-2.5-flash-lite",
    "usageMetadata": {
        "candidatesTokenCount": 5,
        "promptTokenCount": 2,
        "promptTokensDetails": [
            {
                "modality": "TEXT",
                "tokenCount": 2
            }
        ],
        "thoughtsTokenCount": 0,
        "totalTokenCount": 7
        }
}
```

**非流式接口示例**

```shell
POST /v1beta/models/gemini-2.5-flash-lite:generateContent
```

**非流式请求示例：**

```shell
export API_KEY="<你的 API KEY>"
export MODEL="gemini-2.5-flash-lite"
curl --location 'https://maas-openapi.wanjiedata.com/api/v1beta/models/gemini-2.5-flash-lite:generateContent' \
--header 'Content-Type: application/json' \
--header 'Authorization: $API_KEY' \
--data '{
    "contents": [
        {
            "parts": [
                {
                    "text": "你好"
                }
            ]
        }
    ]
}'
```

**非流式响应示例：**

```shell
{
    "candidates":
        {
            "content": {
                "parts": [
                    {
                        "text": "你好！很高兴能与你交流。\n\n请问有什么可以帮你的吗？你可以随时向我提问、寻求建议，或者只是随便聊聊。"
                    }
                ],
                "role": "model"
            },
            "finishReason": "STOP",
            "index": 0,
            "safetyRatings": null
        },
    "model": "gemini-2.5-pro",
    "promptFeedback": {
        "safetyRatings": null,
    "usageMetadata": {
        "candidatesTokenCount": 34,
        "promptTokenCount": 2,
        "promptTokensDetails": [
            {
                "modality": "TEXT",
                "tokenCount": 2
            }
        ],
        "thoughtsTokenCount": 1642,
        "totalTokenCount": 1678
        }
    }
}
```

gemini 系列其他模型同样支持以上请求，如 gemini-2.5-pro、gemini-2.5-flash ；使用时需要将 URL 、model 里的模型名称换成目标模型。

## 图像分析对话

**模型：gemini-2.5-flash-image-preview**

```shell
POST /v1beta/models/gemini-2.5-flash-image-preview:generateContent
```

**请求示例：**

```shell
curl --location 'https://maas-openapi.wanjiedata.com/api/v1beta/models/gemini-2.5-flash-image-preview:generateContent' \
--header 'Content-Type: application/json' \
--header 'Authorization: $API_KEY' \
--data '{
{
  "contents": [
    {
      "parts": [
        {
          "text": "告诉我这张图片里有什么"
        },
        {
          "inline_data": {
            "mime_type": "image/jpeg",
            "data": "$(cat "$TEMP_B64")"
          }
        }
      ]
    }
  ]
}
```

**响应示例：**

```shell
{
    "candidates":
        {
            "content": {
                "parts": [
                    {
                        "text": "这张图片中有一个恐怖的生物头部，它的特征如下：\n\n*   **头颅和面部**：头颅呈苍白色，表面有类似血管或神经的凸起纹路，看起来像是腐烂或变异的组织。面部肌肉和皮肤暴露在外，呈紫红色，有明显的撕裂感。\n*   **眼睛**：眼睛很大，呈黄色，瞳孔是黑色的，散发着凶恶的光芒，显得非常警惕和威胁。\n*   **嘴巴和牙齿**：嘴巴张开，露出尖锐的白色牙齿，像食肉动物的利齿，非常具有攻击性。\n*   **头发/触手**：头部上方和两侧有许多扭曲、缠绕的藤蔓或触手状结构，颜色较深，与周围环境融为一体。\n*   **背景和前景**：背景黑暗模糊，给人一种深邃、幽暗的感觉。前景中散布着一些扭曲的树枝或根系，仿佛这个生物是从地下或森林深处出现。\n\n整体而言，这是一张非常哥特式和恐怖风格的艺术作品，描绘了一个扭曲、怪异的怪物形象。"
                    }
                ],
                "role": "model"
            },
            "finishReason": "STOP",
            "index": 0
        },
    "model": "gemini-2.5-flash-image-preview",
    "modelVersion": "gemini-2.5-flash-image-preview",
    "responseId": "DwDZaLeSPP-UjMcP_5SP4QM",
    "usageMetadata": {
        "candidatesTokenCount": 259,
        "promptTokenCount": 1296,
        "promptTokensDetails": [
            {
                "modality": "TEXT",
                "tokenCount": 6
            },
            {
                "modality": "IMAGE",
                "tokenCount": 1290
            }
        ],
        "totalTokenCount": 1555
        }
}
```

## 文字生成图片

**模型：gemini-3-pro-image-preview**

```shell
POST /v1beta/models/gemini-3-pro-image-preview:generateContent
```

**请求示例：**

```shell
curl --location --request POST 'https://maas-openapi.wanjiedata.com/api/v1beta/models/gemini-3-pro-image-preview:generateContent' \
--header 'Authorization: $API_KEY' \
--header 'Content-Type: application/json' \
--data-raw '{
    "contents": [
        {
            "role": "user",
            "parts": [
                {
                    "text": "输入生成图片要求"
                }
            ]
        }
    ]
}'
```

**响应示例：**

```shell
{
    "candidates": [
        {
            "content": {
                "parts": [
                    {
                        "text": "**Contemplating the Discovery**\n\nI'm imagining a group of explorers stumbling upon a lost city deep in the jungle. I'm focusing on their reactions, the play of sunlight, and the details of the ancient structures and environment. I'm considering the tools they'd be using and the scene's composition.\n\n\n","thought": true
                    },
                    ...
                     {
                        "inlineData": {
                            "data": "iVBORw0KGgoAAAANSUhEUgAABYAAAAMACAIAAAASU1SbAAAAiXpUWHRSYXcgcHJvZmls.....
                            ...wEu+rsw3H7JLY+7jS9q60Lqw8lzhnfpGMfCPvocD/tat/259EXC/F2e30mpqA+w28Hf2aiV/6ehU3sEgUYr96ZSCdIKC/vYFtkkC7dBnyPqMVP8TYbEPvMiCD1"
                    }
                ],
                "role": "model"
            },
            "finishReason": "STOP"
        }
    ],
    "createTime": "2025-12-04T09:54:26.137486Z",
    "model": "gemini-3-pro-image-preview",
    "modelVersion": "gemini-3-pro-image-preview",
    "responseId": "UloxaY6yCIq4694Pi-TTmAk",
    "usageMetadata": {
        "candidatesTokenCount": 1120,
        "candidatesTokensDetails": [
            {
                "modality": "IMAGE",
                "tokenCount": 1120
            }
        ],
        "promptTokenCount": 5,
        "promptTokensDetails": [
            {
                "modality": "TEXT",
                "tokenCount": 5
            }
        ],
        "thoughtsTokenCount": 155,
        "totalTokenCount": 1280,
        "trafficType": "ON_DEMAND"
    }
}
```

## 图片编辑

**模型：gemini-3-pro-image-preview**

```shell
POST /v1beta/models/gemini-3-pro-image-preview:generateContent
```

**请求示例：**

```shell
curl --location --request POST 'https://maas-openapi.wanjiedata.com/api/v1beta/models/gemini-3-pro-image-preview:generateContent' \
--header 'Authorization: $API_KEY' \
--header 'Content-Type: application/json' \
--data-raw '{
    "contents": [
        {
            "parts": [
                {
                    "text": "$输入你的想法"
                },
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": "$图片 base64"
                    }
                }
            ]
        }
    ]
}'
```

**响应示例：**

```shell
{
    "candidates": [
        {
            "content": {
                "parts": [
                    {
                        "text": "![image](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAABYAAAAMACAIAAAASU1SbAAAAiXpUWHRSYXcgcHJvZmlsZSB0eXBlIGlwdGMAAAiZTYwxDgIxDAT7vOKekDjrtV1T0VHwgbtcIiEhgfh/QaDgmGlWW0w6X66n5fl6jNu9p
                        ...
                        ...
                        ...
                        MB4E4LHFlHO/n9xbX6GDMkLigAAAABJRU5ErkJggg==)"
                    }
                ],
                "role": "model"
            },
            "finishReason": "STOP",
            "index": 0,
            "safetyRatings": []
        }
    ],
    "model": "gemini-3-pro-image-preview",
    "usageMetadata": {
        "candidatesTokenCount": 1352,
        "promptTokenCount": 1085,
        "promptTokensDetails": null,
        "thoughtsTokenCount": 0,
        "totalTokenCount": 2437
    }
}
```

## 音频处理

**模型：gemini-2.5-pro**

```shell
POST /v1beta/models/gemini-2.5-pro:generateContent
```

**请求示例：**

```shell
curl --location 'https://maas-openapi.wanjiedata.com/api/v1beta/models/gemini-2.5-pro:generateContent' \
--header 'Content-Type: application/json' \
--header 'Authorization: $API_KEY' \
--data '{
  "contents": [
    {
      "parts": [
        {
          "text": "这个音频文件描述了什么"
        },
        {
          "inline_data": {
            "mime_type": "audio/mpeg",
            "data": "'$AUDIO_B64'"
          }
        }
      ]
    }
  ]
}'
```

**响应示例：**

```shell
{
    "candidates":
        {
            "content": {
                "parts": [
                    {
                        "text": "这个音频文件里，一个清晰的女声说了一句话：\n\n**“两只老虎爱跳舞” (liǎng zhī lǎo hǔ ài tiào wǔ)**\n\n这句话的意思是 **\"Two tigers love to dance\"**。\n\n这是一个充满童趣和想象力的描述，通常出现在儿童歌曲、故事或者可爱的动画场景中。它改编自中国家喻户晓的儿歌《两只老虎》。"
                    }
                ],
                "role": "model"
            },
            "finishReason": "STOP",
            "index": 0,
            "safetyRatings": null
        },
    "model": "gemini-2.5-pro",
    "promptFeedback": {
        "safetyRatings": null,
    "usageMetadata": {
        "candidatesTokenCount": 91,
        "promptTokenCount": 62,
        "promptTokensDetails": [
            {
                "modality": "TEXT",
                "tokenCount": 7
            },
            {
                "modality": "AUDIO",
                "tokenCount": 55
            }
        ],
        "thoughtsTokenCount": 1199,
        "totalTokenCount": 1352
        }
}
}
```

## PDF 处理

**模型：gemini-2.5-pro**

```shell
POST api/v1beta/models/gemini-2.5-pro:generateContent
```

**请求示例：**

```shell
curl --location 'https://maas-openapi.wanjiedata.com/api/v1beta/models/gemini-2.5-pro:generateContent' \
--header 'Content-Type: application/json' \
--header 'Authorization: $API_KEY' \
--data '{
  "contents": [
    {
      "parts": [
        {
          "text": "Can you add a few more lines to this poem?"
        },
        {
          "inline_data": {
            "mime_type": "application/pdf",
            "data": "'$PDF_B64'"}}
      ]
    }]
  }'
```

**响应示例：**

```shell
{
    "candidates":
        {
            "content": {
                "parts": [
                    {
                        "text": "Of course! While this appears to be the user manual for the \"云帆 (Cloud Sail) Learning and Examination System,\" the name itself is quite poetic. Let's add a few lines inspired by the journey of learning outlined in the manual.\n\nHere are a few additions, in the spirit of a modern poem:\n\n**云帆学习考试系统**\n**用户手册**\n**（用户端）**\n\n知识之海，无远弗届，\n数据为舟，代码作帆。\n人脸识别，映求知之容，\n切屏交卷，记专注瞬间。\n指尖轻点，星辰入梦，\n终有一日，证书在手，破浪云帆。\n\n---\n***Translation:***\n\n***Cloud Sail Learning Examination System***\n***User Manual***\n***(User End)***\n\n*The sea of knowledge, reaching beyond horizons,*\n*Data is the boat, code the sail.*\n*Facial recognition reflects the countenance of a seeker,*\n*Switching screens submits the exam, marking a moment of focus.*\n*With a light tap of a finger, stars enter the dream,*\n*Until one day, with certificate in hand, you break the waves on a cloud sail.*"
                    }
                ],
                "role": "model"
            },
            "finishReason": "STOP",
            "index": 0,
            "safetyRatings": null
        },
    "model": "gemini-2.5-pro",
    "promptFeedback": {
        "safetyRatings": null,
    "usageMetadata": {
        "candidatesTokenCount": 261,
        "promptTokenCount": 35100,
        "promptTokensDetails": [
            {
                "modality": "TEXT",
                "tokenCount": 12
            },
            {
                "modality": "DOCUMENT",
                "tokenCount": 35088
            }
        ],
        "thoughtsTokenCount": 1032,
        "totalTokenCount": 36393
        }
}
}
```

## 视频分析

**模型：gemini-3-flash-preview**

**接口示例**

```shell
POST /v1beta/models/gemini-3-flash-preview:generateContent
```

**请求示例：**

```shell
curl --location 'https://maas-openapi.wanjiedata.com/api/v1beta/models/gemini-3-flash-preview:generateContent' \
--header 'Content-Type: application/json' \
--header 'Authorization: $API_KEY' \
--data '{
    "contents": [
        {
            "role": "user",
            "parts": [
                {
                    "fileData": {
                        "mimeType": "video/mp4",
                        "fileUri": "$上传视频URL"
                    }
                },
                {
                    "text": "视频分析关键词"
                }
            ]
        }
    ]
}'
```

**响应示例：**

```shell
{
    "candidates": [
        {
            "content": {
                "parts": [
                    {
                        "text": "这段视频展示了一个宏大的科幻场景，视角位于一艘大型宇宙飞船的背部甲板，正对着前方的深空。以下是逐帧分析：\n\n*   **00:00 - 00:01**：画面开始，展示了飞船精细的金属甲板结构和中央高耸的垂直塔楼。背景是漆黑的太空，散布着繁星。在右侧，可以看到一个明亮的蓝色环状能量场，伴随着流动的电光效果。\n*   **00:02 - 00:03**：在飞船左侧偏上的位置，突然出现了一团极其耀眼的白蓝色强光。这道光迅速扩大，产生了明显的镜头光晕（Lens Flare）效果，遮挡了部分星空。\n*   **00:04 - 00:05**：光晕效果达到顶峰。这团强光看起来像是一个近距离的恒星爆发或者是飞船正在接近某种高能反应堆。此时，右侧原本清晰的能量环变得更加弥散，化作一片幽蓝色的星云状光影。\n*   **00:06 - 00:07**：左侧的强光开始逐渐收敛和减弱，不再刺眼，转而变成了一片柔和的蓝色弧光。飞船甲板上的金属质感在光影变化下显得非常有深度和真实感。\n*   **00:08 - 00:09**：画面趋于平稳。刺眼的强光几乎消失，只在中央塔楼后方留下淡淡的蓝色余晖。背景中的紫色和蓝色星云更加清晰可见，飞船在静谧而深邃的宇宙中缓缓前行（或停驻）。\n\n**总结：**\n这段视频通过光影的剧烈变化，营造出一种宇宙飞船在深空中遭遇某种高能天文现象或开启能量推进系统的视觉冲击感。整体色调以冷峻的灰金属色和迷幻的深蓝色为主，充满了未来感。",
                        "thoughtSignature": "Cs0ZAY89a1/XI2qb/.../EgVZOx5yZfBlhT0OATWzj1F4KAa3VQFqidLfwSkV0cV22tDZe4+K4Ib0hrEY1fXcC5bZeiPx29XY+kDdIbkxA3JiczV5RlcrcRO19lYsKNPEw=="
                    }
                ],
                "role": "model"
            },
            "finishReason": "STOP"
        }
    ],
    "createTime": "2025-12-25T10:37:51.797389Z",
    "model": "gemini-3-flash-preview",
    "modelVersion": "gemini-3-flash-preview",
    "responseId": "_xNNac3VMJvfz7sP5aW16Qs",
    "usageMetadata": {
        "candidatesTokenCount": 444,
        "candidatesTokensDetails": [
            {
                "modality": "TEXT",
                "tokenCount": 444
            }
        ],
        "promptTokenCount": 648,
        "promptTokensDetails": [
            {
                "modality": "TEXT",
                "tokenCount": 8
            },
            {
                "modality": "VIDEO",
                "tokenCount": 640
            }
        ],
        "thoughtsTokenCount": 849,
        "totalTokenCount": 1941,
        "trafficType": "ON_DEMAND"
    }
}
```

# Gemini 端侧接口标准适配模型在客户端的应用

[在 Cherry Studio 中配置 Gemini 端侧接口标准适配模型](https://docs.wjark.com/maas/scenarios/USEGemini/GeminiCherryStudio.html)

[在 Chatbox 中配置 Gemini 端侧接口标准适配模型](https://docs.wjark.com/maas/scenarios/USEGemini/GeminiChatbox.html)

[Gemini API 接口 Java 版本](https://docs.wjark.com/maas/scenarios/USEGemini/Gemini_Java.html)

[Gemini API 接口 python 版本](https://docs.wjark.com/maas/scenarios/USEGemini/Gemini_Python.html)
