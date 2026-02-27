# 内部 DSL 演示：使用 Python 构建的工作流
class WorkflowBuilder:
    def __init__(self):
        self.steps = []
        self.condition = None

    def add_step(self, name, func):
        print(f"[内部DSL] 添加步骤: {name}")
        self.steps.append((name, func))
        return self

    def add_condition(self, name, condition_func):
        print(f"[内部DSL] 添加条件: {name}")
        self.condition = condition_func
        return self

    def build(self):
        print("[内部DSL] 构建工作流成功")
        return self

    def run(self, context):
        print("\n[内部DSL] 开始运行工作流...")
        for name, func in self.steps:
            if (
                name == "send_notification"
                and self.condition
                and not self.condition(context)
            ):
                print(f"[内部DSL] 跳过步骤: {name} (条件未满足)")
                continue
            func(context)
        print("[内部DSL] 工作流运行结束\n")


# 模拟业务函数
def validate_user_input(ctx):
    print("  - 执行: 验证用户输入")
    ctx.validation_result = True


def process_business_data(ctx):
    print("  - 执行: 处理业务数据")


def send_success_notification(ctx):
    print("  - 执行: 发送成功通知")


# --- 原 Notebook 代码开始 ---

# 使用Python构建的工作流DSL
workflow = (
    WorkflowBuilder()
    .add_step("validate_input", validate_user_input)
    .add_step("process_data", process_business_data)
    .add_condition("data_valid", lambda ctx: ctx.validation_result)
    .add_step("send_notification", send_success_notification)
    .build()
)

# 优势：开发成本低，可以复用宿主语言的工具链
#
# 劣势：受宿主语言语法限制，业务人员难以直接理解

# 客服对话流程DSL
# conversation_flow:
#   name: "customer_service_flow"
#
#   triggers:
#     - intent: "greeting"
#       response: "您好！我是智能客服，有什么可以帮您的？"
#
#     - intent: "refund_request"
#       conditions:
#         - check: "order_exists"
#         - check: "order_refundable"
#       actions:
#         - type: "api_call"
#           service: "payment_service"
#           method: "process_refund"
#         - type: "send_message"
#           template: "refund_success"

# 优势：语法完全自定义，业务人员可以直接理解和修改
#
# 劣势：需要开发专门的解析器，开发成本相对较高

# --- 原 Notebook 代码结束 ---

if __name__ == "__main__":

    class Context:
        def __init__(self):
            self.validation_result = False

    # 运行演示
    ctx = Context()
    if hasattr(workflow, "run"):
        workflow.run(ctx)
