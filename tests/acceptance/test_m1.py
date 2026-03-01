"""
M1 验收测试 - SQLite 持久化

测试 Project 和 ProjectJDEntry 的 CRUD 操作
"""
import pytest
import sqlite3
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.db.models import Project, ProjectJDEntry
from src.db.crud import ProjectCRUD, ProjectJDEntryCRUD
from src.db.database import init_db, get_connection, DB_PATH


class TestProjectCRUD:
    """Project CRUD 测试"""

    def setup_method(self):
        """每个测试前清理数据库"""
        # 删除测试数据库
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        # 初始化数据库
        init_db()

    def test_create_project(self):
        """测试创建项目"""
        crud = ProjectCRUD()
        project = crud.create(name="test-project", cycle="")

        assert project.id is not None
        assert len(project.id) == 8  # 8 字符短 ID
        assert project.name == "test-project"
        assert project.created_at is not None

    def test_create_with_cycle(self):
        """测试创建带 cycle 的项目"""
        crud = ProjectCRUD()
        project = crud.create(name="test", cycle="2024春招")

        assert project.cycle == "2024春招"

    def test_get_project(self):
        """测试查询项目"""
        crud = ProjectCRUD()
        created = crud.create(name="test-project")
        fetched = crud.get(created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == "test-project"

    def test_get_nonexistent_project(self):
        """测试查询不存在的项目"""
        crud = ProjectCRUD()
        result = crud.get("nonexistent")
        assert result is None

    def test_list_projects(self):
        """测试列出所有项目"""
        crud = ProjectCRUD()
        crud.create(name="project-1")
        crud.create(name="project-2")
        crud.create(name="project-3")

        projects = crud.list_all()
        assert len(projects) == 3
        names = [p.name for p in projects]
        assert "project-1" in names
        assert "project-2" in names
        assert "project-3" in names

    def test_delete_project(self):
        """测试删除项目"""
        crud = ProjectCRUD()
        project = crud.create(name="to-delete")

        # 删除前存在
        assert crud.get(project.id) is not None

        # 删除
        result = crud.delete(project.id)
        assert result is True

        # 删除后不存在
        assert crud.get(project.id) is None

    def test_delete_nonexistent_project(self):
        """测试删除不存在的项目"""
        crud = ProjectCRUD()
        result = crud.delete("nonexistent")
        assert result is False


class TestProjectJDEntryCRUD:
    """ProjectJDEntry CRUD 测试"""

    def setup_method(self):
        """每个测试前清理数据库"""
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()

    def test_create_jd_entry(self):
        """测试创建 JD 条目"""
        project_crud = ProjectCRUD()
        project = project_crud.create(name="test-project")

        jd_crud = ProjectJDEntryCRUD()
        jd_entry = jd_crud.create(
            project_id=project.id,
            content="JD content here",
            source_file="test.txt"
        )

        assert jd_entry.id is not None
        assert jd_entry.project_id == project.id
        assert jd_entry.raw_content == "JD content here"
        assert jd_entry.source_file == "test.txt"

    def test_get_jd_entry(self):
        """测试查询 JD 条目"""
        project_crud = ProjectCRUD()
        project = project_crud.create(name="test-project")

        jd_crud = ProjectJDEntryCRUD()
        created = jd_crud.create(
            project_id=project.id,
            content="JD content",
            source_file="test.txt"
        )
        fetched = jd_crud.get(created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.raw_content == "JD content"

    def test_list_by_project(self):
        """测试查询项目的所有 JD 条目"""
        project_crud = ProjectCRUD()
        project = project_crud.create(name="test-project")

        jd_crud = ProjectJDEntryCRUD()
        jd_crud.create(project_id=project.id, content="JD 1", source_file="jd1.txt")
        jd_crud.create(project_id=project.id, content="JD 2", source_file="jd2.txt")
        jd_crud.create(project_id=project.id, content="JD 3", source_file="jd3.txt")

        jd_entries = jd_crud.list_by_project(project.id)
        assert len(jd_entries) == 3


class TestPersistence:
    """持久化测试"""

    def setup_method(self):
        """每个测试前清理数据库"""
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

    def test_persistence_across_reconnect(self):
        """测试重连后数据仍然存在"""
        # 第一阶段：创建数据
        init_db()
        crud = ProjectCRUD()
        project = crud.create(name="persistence-test")
        project_id = project.id

        # 第二阶段：模拟重连（重新创建连接）
        new_crud = ProjectCRUD()

        # 验证数据仍然存在
        fetched = new_crud.get(project_id)
        assert fetched is not None
        assert fetched.name == "persistence-test"


class TestDatabaseInit:
    """数据库初始化测试"""

    def teardown_method(self):
        """测试后清理"""
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

    def test_init_creates_tables(self):
        """测试数据库初始化创建表"""
        init_db()

        conn = get_connection()
        cursor = conn.cursor()

        # 检查 projects 表
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='projects'
        """)
        assert cursor.fetchone() is not None

        # 检查 project_jd_entries 表
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='project_jd_entries'
        """)
        assert cursor.fetchone() is not None

        conn.close()

    def test_init_idempotent(self):
        """测试重复初始化不报错"""
        init_db()
        init_db()  # 第二次初始化不应该报错

        # 数据库应该正常工作
        crud = ProjectCRUD()
        project = crud.create(name="test")
        assert project.id is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
