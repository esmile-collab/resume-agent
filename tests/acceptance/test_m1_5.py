"""M1.5 acceptance tests for minimal project CLI."""

from __future__ import annotations

import json
import os
import re

from click.testing import CliRunner

from src.cli.main import cli
from src.db.database import DB_PATH, init_db


class TestProjectCLI:
    """Acceptance tests for project subcommands."""

    def setup_method(self) -> None:
        """Reset database before each test."""
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db().close()
        self.runner = CliRunner()

    def test_project_init(self) -> None:
        """Should create a project and print generated short ID."""
        result = self.runner.invoke(cli, ["project", "init", "--name", "testproject"])

        assert result.exit_code == 0
        assert "项目已创建" in result.output
        assert re.search(r"[a-z0-9]{8}", result.output) is not None

    def test_project_init_with_cycle(self) -> None:
        """Should support cycle field when creating project."""
        result = self.runner.invoke(
            cli, ["project", "init", "--name", "testproject", "--cycle", "2024春招"]
        )

        assert result.exit_code == 0
        assert "项目已创建" in result.output

    def test_project_list_table(self) -> None:
        """Should list projects in table format."""
        self.runner.invoke(cli, ["project", "init", "--name", "alpha"])
        self.runner.invoke(cli, ["project", "init", "--name", "beta"])

        result = self.runner.invoke(cli, ["project", "list"])

        assert result.exit_code == 0
        assert "ID" in result.output
        assert "alpha" in result.output
        assert "beta" in result.output

    def test_project_list_json(self) -> None:
        """Should output valid JSON array for list command."""
        self.runner.invoke(cli, ["project", "init", "--name", "alpha"])

        result = self.runner.invoke(cli, ["project", "list", "--format", "json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0]["name"] == "alpha"

    def test_project_get_and_delete(self) -> None:
        """Should get and then delete a project by ID."""
        created = self.runner.invoke(cli, ["project", "init", "--name", "alpha"])
        project_id_match = re.search(r"([a-z0-9]{8})", created.output)
        assert project_id_match is not None
        project_id = project_id_match.group(1)

        get_result = self.runner.invoke(cli, ["project", "get", "--id", project_id])
        assert get_result.exit_code == 0
        assert project_id in get_result.output
        assert "alpha" in get_result.output

        delete_result = self.runner.invoke(cli, ["project", "delete", "--id", project_id])
        assert delete_result.exit_code == 0
        assert f"项目已删除: {project_id}" in delete_result.output

    def test_duplicate_name_allowed(self) -> None:
        """Should allow same name and generate different IDs."""
        first = self.runner.invoke(cli, ["project", "init", "--name", "same"])
        second = self.runner.invoke(cli, ["project", "init", "--name", "same"])

        first_id = re.search(r"([a-z0-9]{8})", first.output)
        second_id = re.search(r"([a-z0-9]{8})", second.output)
        assert first_id is not None
        assert second_id is not None
        assert first_id.group(1) != second_id.group(1)

    def test_get_nonexistent_project(self) -> None:
        """Should return not-found message and non-zero code."""
        result = self.runner.invoke(cli, ["project", "get", "--id", "nonexistent"])

        assert result.exit_code == 1
        assert "项目不存在: nonexistent" in result.output
