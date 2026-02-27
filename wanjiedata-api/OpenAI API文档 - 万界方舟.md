# OpenAI API 接口

该模型适配于 OpenAI 端侧接口标准

Base Url： [https://maas-openapi.wanjiedata.com/api](https://maas-openapi.wanjiedata.com/api)

获取 [API KEY](https://www.wjark.com/center/api-key)：[https://www.wjark.com/center/api-key](https://www.wjark.com/center/api-key)

- OpenAI 端侧接口标准适配模型一览表
  ：
  https://docs.wjark.com/maas/UserGuide/Usage/OpenAI.html

```shell
POST /api/v1/chat/completions
```

## 基础文本对话

**非流式请求示例**：

```shell
export API_KEY="<你的 API KEY>"
export MODEL="<OpenAI 端侧接口标准适配模型>"
curl --location --request POST 'https://maas-openapi.wanjiedata.com/api/v1/chat/completions' \
--header "Authorization: Bearer $API_KEY" \
--header 'Content-Type: application/json' \
--data-raw '{
    "model": "'$MODEL'",
    "messages": [{"role": "user", "content": "请用一句话介绍自己"}],
    "stream": false
}'
```

```python
import requests
url = "https://maas-openapi.wanjiedata.com/api/v1/chat/completions"
headers = {
    "Authorization": "Bearer {}".format("API_KEY"),  # 请将 API_KEY 替换为你的实际密钥
    "Content-Type": "application/json"
}
data = {
    "model": "MODEL",  # 请将 MODEL 替换为OpenAI 端侧接口标准适配模型
    "messages": [{"role": "user", "content": "请用一句话介绍自己"}],
    "stream": False
}
response = requests.post(url, headers=headers, json=data)
print(response.text)
```

```javascript
fetch('https://maas-openapi.wanjiedata.com/api/v1/chat/completions', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer 你的APIKey',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        model: ' OpenAI 接口标准适用模型',
        messages: [{ role: 'user', content: '请用一句话介绍自己' }],
        stream: false
    })
})
    .then(res => res.json())
    .then(data => {
        const reply = data.choices?.[0]?.message?.content || '';
        console.log('回复内容:', reply);
        console.log(data);
    })
    .catch(console.error);
```

**非流式响应示例**

```shell
{
    "id": "chatcmpl-Cct0tR2gzMsixFQns4Z0s3LbmEfek",
    "object": "chat.completion",
    "created": 1763383971,
    "model": "GPT-4.1",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "我是由 OpenAI 开发的智能助手，能够帮助你解答问题、提供信息和支持各种文本写作需求。",
                "tool_calls": null
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 13,
        "completion_tokens": 27,
        "total_tokens": 40
    },
    "system_fingerprint": "fp_f99638a8d7"
}
```

```python
{
  "id":"chatcmpl-Ccj1HgXyB5HQb6AT4kxA2Gv9iQkwB","object":"chat.completion",
  "created":1763345555,"model":"GPT-4.1",
  "choices":[{
    "index":0,
    "message":{
      "role":"assistant","content":"我是 ChatGPT，一款由 OpenAI 开发的智能对话 AI 助手，很高兴为你提供帮助！","tool_calls":null
      },
      "finish_reason":"stop"}
      ],
      "usage":{"prompt_tokens":13,"completion_tokens":24,"total_tokens":37},
      "system_fingerprint":"fp_f99638a8d7"}
```

```javascript
回复内容: 我是ChatGPT，一款由OpenAI开发的智能对话助手，能够帮助你解答问题、提供建议和创作内容。
{
    id: 'chatcmpl-CckB5i7otsyx3qxWJiEZdGYAM3iVW',
        object: 'chat.completion',
    created: 1763350007,
    model: 'GPT-4.1',
    choices: [ { index: 0, message: [Object], finish_reason: 'stop' } ],
    usage: { prompt_tokens: 13, completion_tokens: 30, total_tokens: 43 },
    system_fingerprint: 'fp_f99638a8d7'
}
```

**流式请求示例**

```shell
# 调用聊天对话请求示例
export API_KEY="<你的 API KEY>"
export MODEL="<OpenAI 端侧接口标准适配模型>"
# 授权模型名称：在授权模型列表中模型名称复制名称获取。
curl --location --request POST 'https://maas-openapi.wanjiedata.com/api/v1/chat/completions' \
--header "Authorization: Bearer $API_KEY" \
--header 'Content-Type: application/json' \
--data-raw '{
    "model": "'$MODEL'",
    "messages": [{"role": "user", "content": "请用一句话介绍自己"}],
    "stream": true
}'
```

```python
import requests

url = "https://maas-openapi.wanjiedata.com/api/v1/chat/completions"

headers = {
    "Authorization": "Bearer $API_KEY",
    "Content-Type": "application/json"
}

data = {
    "model": "$MODEL",
    "messages": [
        {"role": "user", "content": "请用一句话介绍自己"}
    ],
    "stream": True
}

response = requests.post(url, headers=headers, json=data)
print(response.text)
```

```javascript
fetch('https://maas-openapi.wanjiedata.com/api/v1/chat/completions', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer $API_KEY',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        model: '$MODEL',
        messages: [{ role: 'user', content: '请用一句话介绍自己' }],
        stream: true
    })
})
    .then(res => res.body)
    .then(body => {
        const reader = body.getReader();
        const decoder = new TextDecoder();
        function read() {
            reader.read().then(({ done, value }) => {
                if (done) return;
                console.log(decoder.decode(value));
                read();
            });
        }
        read();
    })
    .catch(console.error);
```

**流式响应示例**

```shell
{
    "id": "chatcmpl-CdAoolTjqXY1Ip5sMFPN4buGPgW1V",
    "object": "chat.completion.chunk",
    "created": 1763452414,
    "model": "GPT-4.1",
    "system_fingerprint": "fp_f99638a8d7",
    "choices": [],
    "usage": {
        "prompt_tokens": 13,
        "completion_tokens": 30,
        "total_tokens": 43,
        "prompt_tokens_details": {
            "cached_tokens": 0,
            "audio_tokens": 0
        },
        "completion_tokens_details": {
            "reasoning_tokens": 0,
            "audio_tokens": 0,
            "accepted_prediction_tokens": 0,
            "rejected_prediction_tokens": 0
        }
    }
}
```

```python
id: 0
data: {"id":"chatcmpl-CdBkqaNlBzKQS31mZAMEBduz1WuVO","object":"chat.completion.chunk","created":1763456012,"model":"GPT-4.1","system_fingerprint":"fp_433e8c8649","choices":[{"index":0,"delta":{"role":"assistant","content":null,"reasoning_content":"","refusal":null,"tool_calls":null},"logprobs":null,"finish_reason":null}],"usage":null}

id: 1
data: {"id":"chatcmpl-CdBkqaNlBzKQS31mZAMEBduz1WuVO","object":"chat.completion.chunk","created":1763456012,"model":"GPT-4.1","system_fingerprint":"fp_433e8c8649","choices":[{"index":0,"delta":{"role":"assistant","content":"ææ¯","reasoning_content":"","refusal":null,"tool_calls":null},"logprobs":null,"finish_reason":null}],"usage":null}
...
...
id: 26
data: {"id":"chatcmpl-CdBkqaNlBzKQS31mZAMEBduz1WuVO","object":"chat.completion.chunk","created":1763456012,"model":"GPT-4.1","system_fingerprint":"fp_433e8c8649","choices":[],"usage":{"prompt_tokens":13,"completion_tokens":24,"total_tokens":37,"prompt_tokens_details":{"cached_tokens":0,"audio_tokens":0},"completion_tokens_details":{"reasoning_tokens":0,"audio_tokens":0,"accepted_prediction_tokens":0,"rejected_prediction_tokens":0}}}

id: 27
data: [DONE]
```

```javascript
id: 0
data: {"id":"chatcmpl-CdBmDOXRAJjS3yNOwWWKdFPseydfV","object":"chat.completion.chunk","created":1763456097,"model":"GPT-4.1","system_fingerprint":"fp_f99638a8d7","choices":[{"index":0,"delta":{"role":"assistant","content":null,"reasoning_content":"","refusal":null,"tool_calls":null},"logprobs":null,"finish_reason":null}],"usage":null}

id: 1
data: {"id":"chatcmpl-CdBmDOXRAJjS3yNOwWWKdFPseydfV","object":"chat.completion.chunk","created":1763456097,"model":"GPT-4.1","system_fingerprint":"fp_f99638a8d7","choices":[{"index":0,"delta":{"role":"assistant","content":"我是","reasoning_content":"","refusal":null,"tool_calls":null},"logprobs":null,"finish_reason":null}],"usage":null}
...
...
id: 27
data: {"id":"chatcmpl-CdBmDOXRAJjS3yNOwWWKdFPseydfV","object":"chat.completion.chunk","created":1763456097,"model":"GPT-4.1","system_fingerprint":"fp_f99638a8d7","choices":[],"usage":{"prompt_tokens":13,"completion_tokens":26,"total_tokens":39,"prompt_tokens_details":{"cached_tokens":0,"audio_tokens":0},"completion_tokens_details":{"reasoning_tokens":0,"audio_tokens":0,"accepted_prediction_tokens":0,"rejected_prediction_tokens":0}}}

id: 28
data: [DONE]
```

## 文生视频接口

- 支持的模型：sora-2、veo3.1-fast、veo3.1-pro、veo3.1

```shell
POST /v1/chat/completions
```

```shell
curl --location 'https://maas-openapi.wanjiedata.com/api/v1/chat/completions' \
--header 'Authorization: Bearer $API_KEY' \
--header 'Content-Type: application/json' \
--data '{
    "model": "$MODEL",
    "messages": [
        {
            "role": "user",
            "content": "武汉文旅    "
        }
    ],
    "stream": true
}'
```

```python
import requests
API_KEY = "<你的 API KEY>"
MODEL = "sora-2"
url = "https://maas-openapi.wanjiedata.com/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
payload = {
    "model": MODEL,
    "messages": [
        {
            "role": "user",
            "content": "武汉文旅视频"
        }
    ],
    "stream": True
}
response = requests.post(url, headers=headers, json=payload, stream=True)
if response.status_code == 200:
    for line in response.iter_lines(decode_unicode=True):
        if line:
            print("收到分块：", line)
else:
    print("请求失败:", response.status_code)
    print(response.text)
```

```javascript
import axios from 'axios';

const apiKey = '<你的 API KEY>';
const model = '<你的授权文生视频模型名称>';

const url = 'https://maas-openapi.wanjiedata.com/api/v1/chat/completions';

const headers = {
    Authorization: `Bearer ${apiKey}`,
    'Content-Type': 'application/json'
};

const data = {
    model,
    messages: [
        { role: 'user', content: '武汉文旅视频' }
    ],
    stream: true
};

axios.post(url, data, { headers })
    .then(res => console.log(res.data))
    .catch(err => console.error(err.response ? err.response.data : err.message));
```

**响应示例**

```shell
{
    "id": "",
    "object": "chat.completion.chunk",
    "created": 0,
    "model": "sora-2",
    "choices": [
        {
            "index": 0,
            "delta": {
                "role": "assistant"
            },
            "finish_reason": null
        }
    ]
}
```

```python
收到分块： data: {"id":"","object":"chat.completion.chunk","created":0,"model":"sora-2","choices":[{"index":0,"delta":{"content":"```json\n{\n    \"prompt\": \"武汉文旅视频\",\n    \"mode\": \"横屏模式\"\n}\n```\n\n"},"finish_reason":null}]}
收到分块： data: {"id":"","object":"chat.completion.chunk","created":0,"model":"sora-2","choices":[{"index":0,"delta":{"content":"\u003e ⌛️ 任务正在队列中，请耐心等待...\n\n"},"finish_reason":null}]]}
收到分块： data: {"id":"","object":"chat.completion.chunk","created":0,"model":"sora-2","choices":[{"index":0,"delta":{"content":"\u003e ✅ 视频生成成功，[点击这里](https://static.aiclound.vip/sora/3b69194c-f7f0-40f8-b13b-b6008f73570f.mp4) 查看视频~~~\n\n"},"finish_reason":null}]}
收到分块： data: {"id":"","object":"chat.completion.chunk","created":0,"model":"sora-2","choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":{"prompt_tokens":14,"completion_tokens":240,"total_tokens":254}}
收到分块： data: [DONE]
```

```javascript
data: {"id":"","object":"chat.completion.chunk","created":0,"model":"sora-2","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"","object":"chat.completion.chunk","created":0,"model":"sora-2","choices":[{"index":0,"delta":{"content":"```json\n{\n    \"prompt\": \"武汉文旅视频\",\n    \"mode\": \"横屏模式\"\n}\n```\n\n"},"finish_reason":null}]}

data: {"id":"","object":"chat.completion.chunk","created":0,"model":"sora-2","choices":[{"index":0,"delta":{"content":"\u003e ✅ 视频生成成功，[点击这里](https://static.aiclound.vip/sora/f794fa3f-0b7c-4540-93b7-27476d35a571.mp4) 查看视频~~~\n\n"},"finish_reason":null}]}

data: {"id":"","object":"chat.completion.chunk","created":0,"model":"sora-2","choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":{"prompt_tokens":14,"completion_tokens":276,"total_tokens":290}}

data: [DONE]
```

## 错误编码说明

见[错误编码说明](https://platform.openai.com/docs/guides/error-codes)

## 图生视频接口

- 支持的模型：sora-2、veo3.1-fast、veo3.1-pro、veo3.1

**1. 图片转 URL（生成url支持公网访问）**

**请求示例**

```shell
curl --location 'https://maas-openapi.wanjiedata.com/api/file/v1/uploadFile' \
--header 'Authorization: 你的key' \
--form 'maasFile=@"postman-cloud:///1f0c5bd8-53ca-43c0-bbde-19562bb591bb"'
```

使用时需要在 body 层配置 maasFile ，Text：输入文本；File：上传本地图片

**响应示例**

```shell
{
    "success": true,
    "message": "",
    "code": 200,
    "result": {
        "url": "粘贴你的图片 URL",
        "fileName": "xxx.jpg"
    },
    "timestamp": 1763711398638
}
```

注意：上传对应的图片文件，目前仅仅 “jpg，png，jpeg”三种格式生成视频，生成的图片 URL 有效期 24h

**2. 图片 URL 生成视频**

**请求示例**

```shell
curl --location 'https://maas-openapi.wanjiedata.com/api/v1/chat/completions' \
--header 'Authorization: 您的key' \
--header 'accept: text/event-stream' \
--header 'Content-Type: application/json' \
--data '{
    "model": "sora-2",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "这里写你的要求"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "上传图片的url"
                    }
                }
            ]
        }
    ],
    "stream": true
}'
```

**响应示例**

```shell
{
    "id": "foaicmpl-03580ff5-5ca0-421e-9d15-a908e14aac47",
    "object": "chat.completion.chunk",
    "created": 1764750479,
    "model": "sora-2",
    "choices": [
        {
            "index": 0,
            "delta": {
                "content":
                ...
                "> 🏃 进度：98.7%\n\n"
                "> ✅ 视频生成成功，[点击这里](https://4o-image-plus.oss-cn-hongkong.aliyuncs.com/sora/aee7c29b-8346-4b95-8977-0e34da3c633d.mp4) 查看视频~~~\n\n"
            },
            "finish_reason": null
        }
    ]
}
```

**其他文件请求格式如下：**

```python
1. 图片转 URL

import requests

url = "https://maas-openapi.wanjiedata.com/api/file/v1/uploadFile"

# 替换为你的实际API key
api_key = "你的key"

headers = {
    "Authorization": api_key
}

# 方式1：上传本地文件
files = {
    'maasFile': ('xxx.jpg', open('path/to/your/file.jpg', 'rb'), 'image/jpeg')
}

# 方式2：如果你要上传的文件在内存中，可以这样：
# files = {
#     'maasFile': ('xxx.jpg', file_content, 'image/jpeg')
# }

response = requests.post(url, headers=headers, files=files)

# 关闭文件
if 'files' in locals():
    for file_tuple in files.values():
        if hasattr(file_tuple[1], 'close'):
            file_tuple[1].close()

print(response.text)

2. 图片 URL 生成视频

import requests
import json

url = "https://maas-openapi.wanjiedata.com/api/v1/chat/completions"

# 替换为你的实际API key
api_key = "您的key"

headers = {
    "Authorization": api_key,
    "accept": "text/event-stream",
    "Content-Type": "application/json"
}

# 替换为实际上传图片的URL
image_url = "上传图片的url"

data = {
    "model": "sora-2",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "这里写你的要求"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url
                    }
                }
            ]
        }
    ],
    "stream": True
}

# 流式处理响应
with requests.post(url, headers=headers, json=data, stream=True) as response:
    response.raise_for_status()  # 检查HTTP错误

    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            # 处理SSE格式的数据
            if decoded_line.startswith('data: '):
                if decoded_line == 'data: [DONE]':
                    print("流式传输完成")
                    break
                else:
                    try:
                        # 移除 'data: ' 前缀并解析JSON
                        json_data = json.loads(decoded_line[6:])
                        print(json.dumps(json_data, indent=2, ensure_ascii=False))
                    except json.JSONDecodeError:
                        print(f"无法解析的JSON: {decoded_line}")
            else:
                print(f"原始数据: {decoded_line}")
```

```javascript
1. 图片转 URL

const fs = require('fs');
const axios = require('axios');
const FormData = require('form-data');

async function uploadFile() {
    try {
        const form = new FormData();
        form.append('maasFile', fs.createReadStream('你的文件所在路径，格式为C:/Users/1764750392698_download.png'));

        const response = await axios.post(
            'https://maas-openapi.wanjiedata.com/api/file/v1/uploadFile',
            form,
            {
                headers: {
                    'Authorization': '你的 API Key',
                    ...form.getHeaders()
                }
            }
        );

        // 假设响应数据中包含url字段
        if (response.data && response.data.url) {
            console.log(response.data.url);
        } else {
            console.log('上传成功，但未找到URL:', JSON.stringify(response.data));
        }

    } catch (error) {
        if (error.response) {
            console.error('上传失败:', error.response.data);
        } else {
            console.error('上传失败:', error.message);
        }
    }
}

uploadFile();

2. 图片 URL 生成视频

const axios = require('axios');

async function main() {
    try {
        console.log('开始生成视频...');

        const response = await axios.post(
            'https://maas-openapi.wanjiedata.com/api/v1/chat/completions',
            {
                "model": "sora-2",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "这里写你的要求"},
                            {"type": "image_url", "image_url": {"url": "粘贴你的图片 URL"}}
                        ]
                    }
                ],
                "stream": true
            },
            {
                headers: {
                    'Authorization': '你的 API Key',
                    'accept': 'text/event-stream',
                    'Content-Type': 'application/json'
                },
                responseType: 'stream'
            }
        );

        console.log('连接成功，正在接收流数据...');

        // 处理流数据
        response.data.on('data', (chunk) => {
            const data = chunk.toString();
            // 解析SSE数据
            if (data.startsWith('data: ')) {
                const jsonData = data.replace('data: ', '');
                if (jsonData.trim() !== '[DONE]') {
                    try {
                        const parsed = JSON.parse(jsonData);
                        if (parsed.choices && parsed.choices[0]) {
                            const content = parsed.choices[0].delta?.content;
                            if (content) {
                                process.stdout.write(content);
                            }
                        }
                    } catch (e) {
                        console.log('原始数据:', jsonData);
                    }
                }
            }
        });

        response.data.on('end', () => {
            console.log('\n视频生成完成！');
        });

        response.data.on('error', (error) => {
            console.error('流错误:', error);
        });

    } catch (error) {
        console.error('请求错误:', error.message);
        if (error.response) {
            console.error('响应状态:', error.response.status);
            console.error('响应数据:', error.response.data);
        }
    }
}

main();
```

## Open AI 文生图接口

- 支持的模型：FLUX.2-dev、Z-Image-Turbo

```shell
POST /v1/images/generations
```

```shell
export API_KEY="<你的 API KEY>"
export MODEL="<你的授权文生图模型名称>"
curl --location --request POST 'https://maas-openapi.wanjiedata.com/api/v1/images/generations' \
--header "Authorization: Bearer $API_KEY"  \
--header 'Content-Type: application/json' \
--data-raw '{
  "model": "'$MODEL'",
  "prompt": "graphic of a Harley Davidson bike",
  "n": 1,
  "size": "1024x1024",
  "responseFormat": "url",
  "quality": "standard",
  "style": "vivid"
}'
```

```python
import requests
API_KEY = "<你的 API KEY>"
MODEL = "<你的授权文生图模型名称>"
url = "https://maas-openapi.wanjiedata.com/api/v1/images/generations"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
payload = {
    "model": MODEL,
    "prompt": "graphic of a Harley Davidson bike",
    "n": 1,
    "size": "1024x1024",
    "responseFormat": "url",
    "quality": "standard",
    "style": "vivid"
}
response = requests.post(url, headers=headers, json=payload)
if response.status_code == 200:
    result = response.json()
    print(result)
else:
    print("请求失败:", response.status_code)
    print(response.text)
```

```javascript
import axios from 'axios';

const apiKey = '<你的 API KEY>';
const model = '<你的授权文生图模型名称>';
const url = 'https://maas-openapi.wanjiedata.com/api/v1/images/generations';

async function generateImage() {
    const headers = {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
    };
    const data = {
        model,
        prompt: 'graphic of a Harley Davidson bike',
        n: 1,
        size: '1024x1024',
        responseFormat: 'url'
    };

    try {
        const res = await axios.post(url, data, { headers });
        console.log(res.data.data[0].url);
    } catch (err) {
        console.error('请求失败:', err.message);
    }
}

generateImage();
```

```csharp
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;

class P {
    static async Task Main() {
        var c = new HttpClient();
        c.DefaultRequestHeaders.Add("Authorization", "Bearer <API_KEY>");
        var d = new StringContent(@"{
            ""model"":""<MODEL>"",
            ""prompt"":""graphic of a Harley Davidson bike"",
            ""n"":1,
            ""size"":""1024x1024"",
            ""responseFormat"":""url"",
            ""quality"":""standard"",
            ""style"":""vivid""
        }", Encoding.UTF8, "application/json");
        var r = await c.PostAsync("https://maas-openapi.wanjiedata.com/api/v1/images/generations", d);
        System.Console.WriteLine(await r.Content.ReadAsStringAsync());
    }
}
```

**响应示例**

```shell
{
    "created": 1762221608,
    "data": [
        {
            "url": "https://rgw.wanjiedata.com/maas-public-bucket/2025/11/04/c3fe6bdd3a601f90c4d1e33e961e064f.jpg"
        }
    ],
    "usage": {
        "input_tokens_details": {}
    }
}
```

```python
{
    'created': 1762220795,
    'data': [{'url': 'https://rgw.wanjiedata.com/maas-public-bucket/2025/11/04/a920b1331c7c5676624e38cbc10d8b43.jpg'}],
    'usage': {'input_tokens_details': {}
    }
    }
```

```javascript
https://rgw.wanjiedata.com/maas-public-bucket/2025/11/04/0d4e5bc27fe7b76a1544a36d75f4c1da.jpg
```

```csharp
{"created":1762414008,"data":[{"url":"https://rgw.wanjiedata.com/maas-public-bucket/2025/11/06/6c6eaaa374eb4be4a629b3adff530412.jpg"}],"usage":{"input_tokens_details":{}}}
```

**文生图接口参数说明见** [OpenAI API Create image](https://platform.openai.com/docs/api-reference/images/create)

[sora-2-pro-openai 请求调用方式](https://docs.wjark.com/maas/scenarios/USEGPTmodel/sorapro.html)

# OpenAI 接口标准适用模型配置相关文档参考

[在 Cherry Studio 中配置 OpenAI 接口标准适用模型](https://docs.wjark.com/maas/scenarios/USEGPTmodel/GPTCherryStudio.html)

[Deep Research Web UI 配置 OpenAI 接口标准适用模型教程](https://docs.wjark.com/maas/scenarios/USEGPTmodel/GPTDeepResearchWebUI.html)

[OpenAI API 接口 Java 版本](https://docs.wjark.com/maas/scenarios/USEGPTmodel/OpenAI_Java.html)
