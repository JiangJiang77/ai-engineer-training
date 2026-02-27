#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
p26 DSLManager 示例（由 p26-DSLManager.ipynb 提取）
"""

import logging
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from fastapi import FastAPI, HTTPException


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


@dataclass
class CoffeeState:
    workflow_name: str


class MockWorkflowApp:
    """模拟 LangGraph App（用于本地演示）"""

    def __init__(self, ast: Dict[str, Any]):
        self.ast = ast

    def stream(self, _):
        yield {"response": f"执行成功: {self.ast.get('name', 'unknown')}"}


def parse_with_antlr(dsl_code: str) -> Dict[str, Any]:
    """模拟 ANTLR 解析"""
    if not dsl_code.strip():
        raise ValueError("DSL 不能为空")
    return {"name": "coffee_workflow", "dsl_code": dsl_code}


def validate_with_antlr(dsl_code: str):
    """模拟 ANTLR 语法校验"""
    parse_with_antlr(dsl_code)


def create_coffee_workflow(ast: Dict[str, Any]) -> MockWorkflowApp:
    """模拟编译 DSL 为 LangGraph App"""
    return MockWorkflowApp(ast)


class InMemoryDB:
    """用于演示的最小 DB 接口，兼容 notebook 里的调用风格"""

    def __init__(self):
        self.rules: List[Dict[str, Any]] = [
            {
                "id": 1,
                "name": "default",
                "version": "1.0.0",
                "dsl_code": "WORKFLOW default VERSION 1.0",
                "author": "system",
                "description": "seed",
                "enabled": 1,
                "created_at": datetime.now().isoformat(),
                "updated_at": None,
                "is_latest": 1,
            }
        ]

    def query(self, sql: str, params: Optional[List[Any]] = None):
        if "SELECT name, dsl_code FROM dsl_rules WHERE enabled=1" in sql:
            return [type("Row", (), {"name": r["name"], "dsl_code": r["dsl_code"]}) for r in self.rules if r["enabled"] == 1]
        return []

    def get(self, sql: str, params: Optional[List[Any]] = None):
        params = params or []
        if "SELECT version FROM dsl_rules WHERE name=? AND is_latest=1" in sql:
            name = params[0]
            latest = next((r for r in self.rules if r["name"] == name and r["is_latest"] == 1), None)
            return (latest["version"],) if latest else None
        if "SELECT * FROM dsl_rules WHERE name=? AND version=?" in sql:
            name, version = params
            row = next((r for r in self.rules if r["name"] == name and r["version"] == version), None)
            return type("Row", (), row) if row else None
        return None

    def all(self, sql: str, params: Optional[List[Any]] = None):
        params = params or []
        if "SELECT version, author, description, created_at FROM dsl_rules WHERE name=? ORDER BY created_at DESC" in sql:
            name = params[0]
            rows = [r for r in self.rules if r["name"] == name]
            rows.sort(key=lambda x: x["created_at"], reverse=True)
            return [
                {
                    "version": r["version"],
                    "author": r["author"],
                    "description": r["description"],
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
        return []

    def execute(self, sql: str, params: Optional[List[Any]] = None):
        params = params or []
        if "UPDATE dsl_rules SET dsl_code=?, updated_at=CURRENT_TIMESTAMP WHERE name=?" in sql:
            dsl_code, name = params
            for r in self.rules:
                if r["name"] == name and r["is_latest"] == 1:
                    r["dsl_code"] = dsl_code
                    r["updated_at"] = datetime.now().isoformat()
        elif "INSERT INTO dsl_rules" in sql:
            name, version, dsl_code, author, description = params
            self.rules.append(
                {
                    "id": len(self.rules) + 1,
                    "name": name,
                    "version": version,
                    "dsl_code": dsl_code,
                    "author": author,
                    "description": description,
                    "enabled": 1,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": None,
                    "is_latest": 1,
                }
            )
        elif "UPDATE dsl_rules SET is_latest=0 WHERE name=? AND version=?" in sql:
            name, version = params
            for r in self.rules:
                if r["name"] == name and r["version"] == version:
                    r["is_latest"] = 0
        elif "UPDATE dsl_rules SET is_latest=0 WHERE name=? AND is_latest=1" in sql:
            name = params[0]
            for r in self.rules:
                if r["name"] == name and r["is_latest"] == 1:
                    r["is_latest"] = 0
        elif "UPDATE dsl_rules SET is_latest=1 WHERE name=? AND version=?" in sql:
            name, version = params
            for r in self.rules:
                if r["name"] == name and r["version"] == version:
                    r["is_latest"] = 1


db = InMemoryDB()


# --- cell ---
# Step 1：设计一个 DSL 管理器，用于管理和执行 DSL 规则。
class DSLManager:
    def __init__(self):
        self.workflows: Dict[str, Callable] = {}
        self.lock = threading.Lock()
        self.load_all_workflows()

    # notebook 中 __init__ 调用了该方法，这里补齐以便可运行
    def load_all_workflows(self):
        self.reload_from_db()

    def load_workflow(self, name: str, dsl_code: str):
        """解析 DSL 并编译为可执行工作流"""
        try:
            ast = parse_with_antlr(dsl_code)
            workflow = create_coffee_workflow(ast)  # 返回 LangGraph App
            with self.lock:
                self.workflows[name] = workflow
            logger.info(f"已加载工作流: {name}")
        except Exception as e:
            logger.error(f"加载失败 {name}: {e}")

    def get_workflow(self, name: str):
        with self.lock:
            return self.workflows.get(name)

    def reload_from_db(self):
        """从数据库加载所有最新 DSL"""
        for row in db.query("SELECT name, dsl_code FROM dsl_rules WHERE enabled=1"):
            self.load_workflow(row.name, row.dsl_code)


# Step 2：支持热更新 API
app = FastAPI()
dsl_manager = DSLManager()


@app.post("/reload")
async def reload_dsl():
    try:
        dsl_manager.reload_from_db()
        return {"status": "success", "message": "所有 DSL 规则已热更新"}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/update_rule")
async def update_rule(name: str, dsl_code: str):
    # 先验证语法
    try:
        validate_with_antlr(dsl_code)
    except Exception as e:
        raise HTTPException(400, f"DSL 语法错误: {e}")

    # 更新数据库
    db.execute(
        "UPDATE dsl_rules SET dsl_code=?, updated_at=CURRENT_TIMESTAMP WHERE name=?",
        [dsl_code, name],
    )

    # 热加载
    dsl_manager.load_workflow(name, dsl_code)
    return {"status": "success", "message": f"{name} 已更新并生效"}


# Step 3：LangGraph 中无缝切换
def execute_workflow(state: CoffeeState):
    # 每次都从最新管理器获取工作流（支持热更新）
    app = dsl_manager.get_workflow(state["workflow_name"])
    if not app:
        return {"response": "找不到该工作流"}

    output = {}
    for output in app.stream(...):
        pass
    return output


# --- cell ---
# Step 1：数据库表设计
SQL_CREATE_DSL_RULES_TABLE = """
CREATE TABLE dsl_rules (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,  -- 1.2.3
    dsl_code TEXT NOT NULL,
    author TEXT,
    description TEXT,
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    is_latest BOOLEAN DEFAULT 1
);
"""


# Step 2：版本操作接口
class DSLVersionControl:
    @staticmethod
    def save_new_version(name: str, dsl_code: str, author: str, desc: str = ""):
        # 获取当前最新版本
        latest = db.get("SELECT version FROM dsl_rules WHERE name=? AND is_latest=1", [name])
        old_ver = latest[0] if latest else "1.0.0"

        # 递增版本号（简单实现）
        major, minor, patch = map(int, old_ver.split("."))
        new_ver = f"{major}.{minor}.{patch + 1}"

        # 插入新版本
        db.execute(
            """
            INSERT INTO dsl_rules (name, version, dsl_code, author, description, is_latest)
            VALUES (?, ?, ?, ?, ?, 1)
        """,
            [name, new_ver, dsl_code, author, desc],
        )

        # 标记旧版本非最新
        db.execute("UPDATE dsl_rules SET is_latest=0 WHERE name=? AND version=?", [name, old_ver])

        return new_ver

    @staticmethod
    def rollback_to(name: str, version: str):
        """回滚到指定版本"""
        # 检查版本是否存在
        row = db.get("SELECT * FROM dsl_rules WHERE name=? AND version=?", [name, version])
        if not row:
            raise ValueError("版本不存在")

        # 禁用当前版本，启用目标版本
        db.execute("UPDATE dsl_rules SET is_latest=0 WHERE name=? AND is_latest=1", [name])
        db.execute("UPDATE dsl_rules SET is_latest=1 WHERE name=? AND version=?", [name, version])

        # 热加载
        dsl_manager.load_workflow(name, row.dsl_code)
        return f"已回滚 {name} 到 {version}"


# Step 3：集成到 Web 控制台
@app.get("/rules/{name}/versions")
async def list_versions(name: str):
    rows = db.all(
        "SELECT version, author, description, created_at FROM dsl_rules WHERE name=? ORDER BY created_at DESC",
        [name],
    )
    return {"versions": rows}


@app.post("/rules/{name}/rollback")
async def rollback(name: str, version: str):
    result = DSLVersionControl.rollback_to(name, version)
    return {"message": result}


def main():
    print("=== DSLManager 演示 ===")
    print(reload_dsl)
    new_ver = DSLVersionControl.save_new_version(
        name="default",
        dsl_code="WORKFLOW default VERSION 1.1",
        author="demo_user",
        desc="demo update",
    )
    print(f"新版本: {new_ver}")
    rollback_msg = DSLVersionControl.rollback_to("default", "1.0.0")
    print(rollback_msg)
    output = execute_workflow({"workflow_name": "default"})
    print(f"执行输出: {output}")


if __name__ == "__main__":
    main()
