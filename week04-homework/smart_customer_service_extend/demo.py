"""智能客服系统主程序

演示LangGraph工作流功能
"""
from smart_customer_service_extend.repository import (
    authenticate_user
)
from smart_customer_service_extend.workflow import run_workflow, create_workflow_graph, print_workflow_graph
from smart_customer_service_extend.utils import setup_logger

logger = setup_logger()


def demo_workflow():
    """演示工作流功能"""
    print("\n" + "=" * 60)
    print("🤖 智能客服系统 - LangGraph工作流演示")
    print("版本: 0.2.0")
    print("=" * 60)
    
    # 登录用户
    print("\n✅ 登录用户: test_user")
    user = authenticate_user("test_user", "password123")
    
    if not user:
        print("❌ 登录失败")
        return
    
    user_id = user["user_id"]
    session_id = "demo_session_001"
    
    # 打印流程图
    app = create_workflow_graph()
    print_workflow_graph(app)
    
    # 测试场景
    test_cases = [
        {
            "name": "物流查询 - 关键字场景",
            "input": "查看昨天购买的年货礼品发货了吗"
        },
        {
            "name": "物流查询 - 日期场景",
            "input": "查看昨天下单的订单"
        },
        {
            "name": "退款申请",
            "input": "我要退货"
        },
        {
            "name": "发票开具",
            "input": "我要开具发票"
        },
        {
            "name": "一般对话",
            "input": "你好"
        },
        {
            "name": "未知意图",
            "input": "我要投诉"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print("\n" + "=" * 60)
        print(f"📋 场景{i}: {test_case['name']}")
        print("=" * 60)
        print(f"\n用户: {test_case['input']}")
        
        # 运行工作流
        response = run_workflow(
            user_id=user_id,
            session_id=session_id,
            user_input=test_case['input']
        )
        
        print(f"\n系统: {response}")
    
    print("\n" + "=" * 60)
    print("✅ 工作流演示完成!")
    print("=" * 60)
    print("\n💡 提示: 完整的Gradio界面正在开发中...")
    print()


def interactive_mode():
    """交互式模式"""
    print("\n" + "=" * 60)
    print("🤖 智能客服系统 - 交互式模式")
    print("=" * 60)
    
    # 登录
    print("\n请登录:")
    username = input("用户名: ").strip()
    password = input("密码: ").strip()
    
    user = authenticate_user(username, password)
    
    if not user:
        print("❌ 登录失败,用户名或密码错误")
        return
    
    print(f"\n✅ 登录成功! 欢迎 {user['username']}")
    
    user_id = user["user_id"]
    session_id = "interactive_session"
    
    # 打印流程图
    app = create_workflow_graph()
    print_workflow_graph(app)
    
    print("\n💬 开始对话 (输入 'quit' 或 'exit' 退出)")
    print("-" * 60)
    
    while True:
        try:
            user_input = input("\n你: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("\n👋 再见!")
                break
            
            # 运行工作流
            response = run_workflow(
                user_id=user_id,
                session_id=session_id,
                user_input=user_input
            )
            
            print(f"\n客服: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 再见!")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            logger.error(f"交互模式错误: {e}", exc_info=True)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="智能客服系统")
    parser.add_argument(
        "--mode",
        choices=["workflow", "react"],
        default="react",
        help="运行模式: workflow(原有工作流) 或 react(ReAct Agent)"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="交互模式"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="显示详细日志"
    )
    
    args = parser.parse_args()
    
    # 根据模式选择运行方式
    if args.mode == "react":
        # ReAct Agent模式
        if args.interactive:
            interactive_mode_react(args.verbose)
        else:
            demo_react(args.verbose)
    else:
        # Workflow模式
        if args.interactive:
            interactive_mode()
        else:
            demo_workflow()


def interactive_mode_react(verbose: bool = True):
    """ReAct Agent交互式模式"""
    from smart_customer_service_extend.agents import CustomerServiceReActAgent
    
    print("\n" + "=" * 60)
    print("🤖 智能客服系统 - ReAct Agent模式")
    print("=" * 60)
    
    # 登录
    print("\n请登录:")
    username = input("用户名: ").strip()
    password = input("密码: ").strip()
    
    user = authenticate_user(username, password)
    
    if not user:
        print("❌ 登录失败,用户名或密码错误")
        return
    
    print(f"\n✅ 登录成功! 欢迎 {user['username']}")
    
    user_id = user["user_id"]
    
    # 创建Agent
    agent = CustomerServiceReActAgent(user_id, verbose=verbose)
    
    print("\n💬 开始对话 (输入 'quit' 或 'exit' 退出)")
    print("-" * 60)
    
    while True:
        try:
            user_input = input("\n你: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("\n👋 再见!")
                break
            
            # 运行Agent
            print("\n客服: ", end="", flush=True)
            result = agent.run(user_input)
            print(result["output"])
            
            if verbose and result["iterations"] > 0:
                print(f"\n[推理步骤数: {result['iterations']}]")
            
        except KeyboardInterrupt:
            print("\n\n👋 再见!")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            logger.error(f"ReAct Agent错误: {e}", exc_info=True)


def demo_react(verbose: bool = True):
    """ReAct Agent演示模式"""
    from smart_customer_service_extend.agents import CustomerServiceReActAgent
    
    print("\n" + "=" * 60)
    print("🤖 智能客服系统 - ReAct Agent演示")
    print("=" * 60)
    
    # 登录用户
    print("\n✅ 登录用户: test_user")
    user = authenticate_user("test_user", "password123")
    
    if not user:
        print("❌ 登录失败")
        return
    
    user_id = user["user_id"]
    
    # 创建Agent
    agent = CustomerServiceReActAgent(user_id, verbose=verbose)
    
    # 测试场景
    test_cases = [
        "昨天买的手表发货了吗",
        # "我想退掉那个贵的订单",
        # "你们的退货政策是什么?"
    ]
    
    for i, question in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"📋 测试用例 {i}: {question}")
        print('='*60)
        
        result = agent.run(question)
        print(f"\n回答: {result['output']}")
        print(f"推理步骤数: {result['iterations']}")
    
    print("\n" + "=" * 60)
    print("✅ ReAct Agent演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    # main()

    ## react模式
    interactive_mode_react(True)
    # demo_react(True)
    # Workflow模式
    # interactive_mode()
    # demo_workflow()

