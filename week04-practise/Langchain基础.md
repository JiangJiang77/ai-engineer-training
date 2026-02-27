Langchain基础
常见的处理链的三要素：语言模型/提示词模板/输出解释器

1. 语言模型
语言模型包含：LLM通用模型/ChatModel对话模型
消息包含消息的内容和角色
角色分为：HumanMessage/AIMessage/SystemMessage/FunctionMessage/ToolMessage/ChatMessage

方法：LCEL默认实现是同步调用，常见方法是invoke.接受BaseMessage对象作为参数，返回BaseMessage对象作为结果

2. 提示词模版
format的几种形式
# 带 system/human 等角色
ChatPromptTemplate.format_message 支持带角色的消息列表
# 纯文本
PromptTemplate
# 模板短 用# f-string 风格、jinja2语法 ...
f_string_prompt = PromptTemplate.from_template(
    "分析以下{data_type}数据：\n{data}\n\n请提供{analysis_type}分析。"
)

result = f_string_prompt.format(
    data_type="销售",
    data="Q1销售额: 100万, Q2销售额: 120万",
    analysis_type="趋势"
)
print(result)

# 模版长，显示约束输入变量 PromptTemplate+手写input_variables
complex_prompt = PromptTemplate(
    input_variables=["topic", "audience", "tone"],
    template="""
    请为{audience}写一篇关于{topic}的文章。
    写作风格应该是{tone}的。
    
    文章要求：
    - 内容准确且有用
    - 结构清晰
    - 适合目标受众
    """
)

formatted_prompt = complex_prompt.format(
    topic="人工智能",
    audience="初学者",
    tone="通俗易懂"
)
print(formatted_prompt)

# 带条件逻辑的模版

conditional_prompt = PromptTemplate(
    input_variables=["user_type", "question"],
    template="""
    {%- if user_type == "expert" -%}
    作为专家，请详细回答：{question}
    {%- else -%}
    请用简单易懂的方式回答：{question}
    {%- endif -%}
    """
)



3. 输出解释器

常见的输出解析器
# JSON 输出解析器 PydanticOutputParser
# 列表输出解析器 CommaSeparatedListOutputParser


4. LCEL（以下优点没有对应的示例，观察下后续是否有补全）

1. 简洁语法: 使用管道操作符 | 创建链，代码直观易读
2. 自动类型推断: 组件间数据类型自动转换，减少手动处理
3. 并行处理: 内置并行执行能力，提高处理效率
4. 流式处理: 原生支持流式输出，适合实时应用
5. 智能缓存: 自动缓存中间结果，避免重复计算
6. 内置调试: 更好的调试和监控能力
7. 插件化: 支持自定义组件和扩展
8. 标准接口: 统一的 Runnable 接口
9. 版本管理: 支持链的版本控制和管理
