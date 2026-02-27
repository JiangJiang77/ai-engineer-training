# 万界方舟 API 接口文档

万界方舟（Wanjie Ark）是一站式聚合 MaaS 平台，聚合全球顶尖大模型 API。本接口文档详细说明了如何接入并调用平台的各种模型能力。

## 1. 接入流程说明

1.  **访问平台**：登录 [万界方舟-模型平台](https://www.wjark.com)。
2.  **获取模型**：在“模型广场”中，点击想要使用的模型，点击“模型复制”获取模型标识。
3.  **获取密钥**：进入 [API Key 管理页](https://www.wjark.com/center/api-key) 复制你的 API KEY。
4.  **模型授权**：模型广场展示的是已授权模型。如需其他模型，请联系运营人员。

## 2. 接口基础信息

### 基础地址 (Base URL)

*   **OpenAI/Gemini 兼容接口**：`https://maas-openapi.wanjiedata.com/api`
*   **Anthropic 兼容接口**：`https://maas-openapi.wanjiedata.com/api/anthropic`

### 认证方式 (Authentication)

所有请求必须在 HTTP Header 中包含 `Authorization` 字段：
`Authorization: Bearer <你的 API KEY>`

---

## 3. 核心接口说明

### A. 获取模型列表 (Models)
获取当前账号已授权的所有模型列表。

**请求方式**：`GET`
**Endpoint**：`/v1/models`

**示例代码 (cURL)**：
```bash
curl https://maas-openapi.wanjiedata.com/api/v1/models \
  -H "Authorization: Bearer $API_KEY"
```

---

### B. 文本对话 (Chat Completions)
支持多种文本大模型（如 DeepSeek, GPT, Qwen 等），采用 OpenAI 兼容格式。

**请求方式**：`POST`
**Endpoint**：`/v1/chat/completions`

**主要参数**：
*   `model` (string, 必须): 模型标识，例如 `deepseek-v3`。
*   `messages` (array, 必须): 对话消息列表。
*   `stream` (boolean): 是否流式输出，默认为 `false`。

**示例代码 (cURL)**：
```bash
curl --location --request POST 'https://maas-openapi.wanjiedata.com/api/v1/chat/completions' \
--header "Authorization: Bearer $API_KEY" \
--header 'Content-Type: application/json' \
--data-raw '{
    "model": "deepseek-v3",
    "messages": [{"role": "user", "content": "你好，请自我介绍一下。"}],
    "stream": false
}'
```

---

### C. 多模态视频生成

#### 1. 文生视频 (Text-to-Video)
**支持模型**：`sora-2`, `veo3.1-fast`, `veo3.1-pro`, `veo3.1`

**示例代码**：
```bash
curl --location 'https://maas-openapi.wanjiedata.com/api/v1/chat/completions' \
--header "Authorization: Bearer $API_KEY" \
--data '{
    "model": "sora-2",
    "messages": [{"role": "user", "content": "一段电影感的高山航拍视频。"}],
    "stream": true
}'
```

#### 2. 图生视频 (Image-to-Video)
1.  **文件上传**：调用 `POST /api/file/v1/uploadFile` 获取文件 URL。
2.  **生成视频**：在 `messages` 中包含 `image_url`。

---

### D. 语音合成 (Text-to-Speech)
**支持模型**：`CosyVoice`
**Endpoint**：`/v1/audio/speech`

**主要参数**：
*   `input` (string): 待合成的文本。
*   `model` (string): 语音模型标识，如 `cosyvoice-v1`。
*   `voice` (string): 音色选择。
*   `responseFormat` (string): 输出格式，如 `mp3`。

**示例代码**：
```bash
curl --request POST 'https://maas-openapi.wanjiedata.com/api/v1/audio/speech' \
--header "Authorization: Bearer $API_KEY" \
--data-raw '{
  "input": "你好，我是语音助手。",
  "model": "cosyvoice-v1",
  "voice": "普通话",
  "responseFormat": "mp3"
}' --output output.mp3
```

---

## 4. 常见问题
*   **请求限制**：具体频率限制请参考官网个人中心。
*   **错误码**：
    *   `401`：API KEY 无效或缺失。
    *   `404`：模型不存在或未授权。
    *   `429`：请求过于频繁。
