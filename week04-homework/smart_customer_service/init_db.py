"""数据库基础设施与初始化"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from smart_customer_service_extend.config import settings
from smart_customer_service_extend.repository.models import Base


# 创建数据库引擎
engine = create_engine(settings.get_database_url(), echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session():
    """获取数据库会话(上下文管理器)"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database():
    """初始化数据库表"""
    # 确保数据目录存在
    db_path = Path(settings.DATABASE_PATH)
    if not db_path.is_absolute():
        db_path = settings.BASE_DIR / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print(f"✅ 数据库表创建成功: {db_path}")


def load_mock_data():
    """加载模拟数据"""
    from smart_customer_service_extend.repository.models import Order
    from smart_customer_service_extend.repository.session_repo import create_user, get_user_by_username
    from smart_customer_service_extend.repository.order_repo import create_order

    print("📦 开始插入模拟数据...")

    # 清理旧的测试数据
    print("🗑️  清理旧的测试数据...")
    try:
        with get_db_session() as session:
            # 删除test_user的所有订单
            test_user = get_user_by_username("test_user")
            if test_user:
                session.query(Order).filter(Order.user_id == test_user["user_id"]).delete()
                print("✅ 已清理旧订单数据")
    except Exception as e:
        print(f"⚠️  清理数据时出错: {e}")

    # 创建测试用户
    try:
        user1 = create_user("test_user", "password123")
        print(f"✅ 创建测试用户: {user1['username']}")
    except ValueError as e:
        print(f"⚠️  用户已存在: {e}")
        user1 = get_user_by_username("test_user")

    # 创建模拟订单
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    last_week = today - timedelta(days=7)

    orders_data = [
        {
            "order_name": "年货礼品大礼包",
            "order_date": yesterday,
            "status": "shipped",
            "logistics_status": "商品已发货,预计明天送达",
            "can_refund": 1,
            "can_invoice": 1,
            "invoice_status": "未开票",
        },
        {
            "order_name": "智能手表",
            "order_date": yesterday,
            "status": "pending",
            "logistics_status": "订单处理中",
            "can_refund": 1,
            "can_invoice": 1,
            "invoice_status": "未开票",
        },
        {
            "order_name": "笔记本电脑",
            "order_date": last_week,
            "status": "delivered",
            "logistics_status": "已签收",
            "can_refund": 0,
            "can_invoice": 1,
            "invoice_status": "未开票",
        },
        {
            "order_name": "无线耳机",
            "order_date": today,
            "status": "pending",
            "logistics_status": "订单已提交",
            "can_refund": 1,
            "can_invoice": 1,
            "invoice_status": "未开票",
        },
        {
            "order_id": "3236962442905351286",
            "order_name": "儿童手套秋冬新款可爱女童卡 玫红草莓熊1对装;3-12岁",
            "order_date": last_week,
            "status": "delivered",
            "logistics_status": "已签收 送至闲博花城i3-1-1503 粗粮 86-182****4093",
            "can_refund": 1,
            "can_invoice": 1,
            "invoice_status": "未开票",
        },
        {
            "order_id": "3237638702505351286",
            "order_name": "【优惠价】宝宝拧拧螺丝儿童 可推立螺丝配搭套装220件",
            "order_date": yesterday,
            "status": "shipped",
            "logistics_status": "运输中【揭阳市】预计02月12日到达【杭州】送至闲博花城i3-1-1503 粗粮 86-182****4093",
            "can_refund": 1,
            "can_invoice": 1,
            "invoice_status": "未开票",
        },
    ]

    for order_data in orders_data:
        order = create_order(user1["user_id"], **order_data)
        print(
            f"✅ 创建订单: {order_data['order_name']} "
            f"(ID: {order_data.get('order_id', 'N/A')[:8] if order_data.get('order_id') else 'auto'}...)"
        )

    print("✅ 模拟数据插入完成")


def main() -> None:
    parser = argparse.ArgumentParser(description="初始化数据库并插入测试数据")
    parser.add_argument("--init", action="store_true", help="初始化数据库表")
    parser.add_argument("--load-mock-data", action="store_true", help="加载模拟数据")
    args = parser.parse_args()

    if args.init:
        init_database()

    if args.load_mock_data:
        load_mock_data()


if __name__ == "__main__":
    main()
