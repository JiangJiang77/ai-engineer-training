"""RAG检索功能演示脚本

演示如何使用RAG检索政策信息
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_customer_service_extend.workflow import run_workflow


def demo_policy_queries():
    """演示政策查询功能"""
    
    print("=" * 80)
    print("RAG 政策检索功能演示")
    print("=" * 80)
    
    # 测试用户
    user_id = "test_user_001"
    session_id = "demo_session_001"
    
    # 测试查询列表
    test_queries = [
        "退货流程是什么?",
        "发货时效是多久?",
        "支持哪些支付方式?",
        "保修期限是多久?",
        "哪些情况不支持7天无理由退货?",
        "退货运费谁承担?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"测试场景 {i}: {query}")
        print(f"{'=' * 80}\n")
        
        try:
            response = run_workflow(
                user_id=user_id,
                session_id=f"{session_id}_{i}",
                user_input=query
            )
            
            print(f"\n【系统回复】\n{response}\n")
            
        except Exception as e:
            print(f"\n❌ 查询失败: {e}\n")
        
        print("-" * 80)


if __name__ == "__main__":
    demo_policy_queries()
