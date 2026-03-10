# 测试用例文档

## 测试环境准备

### 1. 确保数据库已初始化

```bash
.venv/bin/python -m smart_customer_service_extend.database.init_db --load-mock-data
```

### 2. 运行测试

```bash
# 运行所有测试
.venv/bin/python -m pytest tests/ -v

# 或使用unittest
.venv/bin/python -m unittest tests.test_customer_service -v

# 运行特定测试类
.venv/bin/python -m unittest tests.test_customer_service.TestDatabaseOperations -v

# 运行特定测试方法
.venv/bin/python -m unittest tests.test_customer_service.TestDatabaseOperations.test_query_orders_by_date -v
```

## 测试用例清单

### 1. 数据库操作测试 (TestDatabaseOperations)

- ✅ `test_user_authentication`: 用户认证(正确/错误密码)
- ✅ `test_query_all_orders`: 查询所有订单
- ✅ `test_query_orders_by_date`: 按日期查询订单
- ✅ `test_query_orders_by_keyword`: 按关键字查询订单
- ✅ `test_query_refundable_orders`: 查询可退款订单
- ✅ `test_query_invoiceable_orders`: 查询可开票订单

### 2. 订单工具测试 (TestOrderTools)

- ✅ `test_query_order_by_keyword_tool`: 关键字查询工具
- ✅ `test_query_orders_by_date_tool`: 日期查询工具
- ✅ `test_query_refundable_orders_tool`: 可退款订单查询工具
- ✅ `test_query_invoiceable_orders_tool`: 可开票订单查询工具

### 3. 时间解析测试 (TestTimeParser)

- ✅ `test_parse_yesterday`: 解析"昨天"
- ✅ `test_parse_today`: 解析"今天"
- ✅ `test_parse_day_before_yesterday`: 解析"前天"
- ✅ `test_parse_n_days_ago`: 解析"N天前"

### 4. 集成测试 (TestIntegration)

- ✅ `test_complete_order_query_workflow`: 完整订单查询流程
- ✅ `test_complete_refund_workflow`: 完整退款流程

## 测试数据要求

测试依赖以下数据:
- 测试用户: `test_user` (密码: `password123`)
- 至少4个订单(不同日期、不同状态)
- 至少1个包含"年货"关键字的订单
- 至少1个可退款订单
- 至少1个可开票订单

## 回归测试检查清单

新增功能后,必须确保以下测试通过:

### 核心功能
- [ ] 用户认证功能正常
- [ ] 订单查询(全部/日期/关键字)正常
- [ ] 可退款订单查询正常
- [ ] 可开票订单查询正常

### 工具函数
- [ ] 所有订单工具返回正确格式
- [ ] 时间解析功能正常
- [ ] 日期匹配逻辑正确(datetime vs date)

### 集成流程
- [ ] 完整订单查询流程可执行
- [ ] 完整退款流程可执行

## 已知问题和注意事项

1. **日期匹配问题**: 已修复,使用`func.date()`提取日期部分
2. **Session管理**: 所有CRUD函数返回字典,避免DetachedInstanceError
3. **测试数据隔离**: 部分测试会修改数据库(如退款),建议使用独立测试数据库

## 性能基准

参考值(在测试环境下):
- 单个订单查询: < 50ms
- 批量订单查询(100条): < 200ms
- 用户认证: < 100ms
- 时间解析: < 1ms

## 扩展测试建议

后续可添加:
- [ ] LangGraph工作流测试
- [ ] Gradio界面测试
- [ ] 多模态功能测试(ASR/OCR)
- [ ] 热更新机制测试
- [ ] 并发访问测试
- [ ] 压力测试
