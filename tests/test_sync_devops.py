"""Tests for sync-devops.py (unit tests for pure functions only — no az CLI calls)."""

import importlib

import pytest

sync_devops = importlib.import_module("sync-devops")


# --- get_story_type ---

class TestGetStoryType:
    def test_agile(self):
        assert sync_devops.get_story_type("Agile") == "User Story"

    def test_scrum(self):
        assert sync_devops.get_story_type("Scrum") == "Product Backlog Item"

    def test_cmmi(self):
        assert sync_devops.get_story_type("CMMI") == "Requirement"

    def test_basic(self):
        assert sync_devops.get_story_type("Basic") == "Issue"

    def test_unknown_defaults(self):
        assert sync_devops.get_story_type("CustomProcess") == "User Story"


# --- get_ac_field ---

class TestGetAcField:
    def test_agile(self):
        assert sync_devops.get_ac_field("Agile") == "Microsoft.VSTS.Common.AcceptanceCriteria"

    def test_basic_returns_none(self):
        assert sync_devops.get_ac_field("Basic") is None


# --- get_complete_state ---

class TestGetCompleteState:
    def test_agile(self):
        assert sync_devops.get_complete_state("Agile") == "Closed"

    def test_scrum(self):
        assert sync_devops.get_complete_state("Scrum") == "Done"

    def test_cmmi(self):
        assert sync_devops.get_complete_state("CMMI") == "Resolved"


# --- map_bmad_status_to_devops_state ---

class TestMapBmadStatus:
    def test_draft_agile(self):
        assert sync_devops.map_bmad_status_to_devops_state("draft", "Agile") == "New"

    def test_in_progress_scrum(self):
        assert sync_devops.map_bmad_status_to_devops_state("in-progress", "Scrum") == "Committed"

    def test_review_maps_like_in_progress(self):
        assert sync_devops.map_bmad_status_to_devops_state("review", "Agile") == "Active"
        assert sync_devops.map_bmad_status_to_devops_state("in-progress", "Agile") == "Active"

    def test_done_cmmi(self):
        assert sync_devops.map_bmad_status_to_devops_state("done", "CMMI") == "Resolved"

    def test_empty_status_returns_none(self):
        assert sync_devops.map_bmad_status_to_devops_state("", "Agile") is None

    def test_none_status_returns_none(self):
        assert sync_devops.map_bmad_status_to_devops_state(None, "Agile") is None

    def test_unknown_status_returns_none(self):
        assert sync_devops.map_bmad_status_to_devops_state("blocked", "Agile") is None

    def test_whitespace_and_case_insensitive(self):
        assert sync_devops.map_bmad_status_to_devops_state("  DONE  ", "Scrum") == "Done"


# --- wrap_html ---

class TestWrapHtml:
    def test_basic(self):
        assert sync_devops.wrap_html("Hello") == "<div>Hello</div>"

    def test_escapes_html(self):
        result = sync_devops.wrap_html("a < b & c > d")
        assert "&lt;" in result
        assert "&amp;" in result
        assert "&gt;" in result
        assert "<div>" in result

    def test_newlines_to_br(self):
        result = sync_devops.wrap_html("line 1\nline 2")
        assert "<br>" in result

    def test_empty(self):
        assert sync_devops.wrap_html("") == ""

    def test_none(self):
        assert sync_devops.wrap_html(None) == ""

    def test_max_len_no_truncation(self):
        result = sync_devops.wrap_html("short", max_len=100)
        assert result == "<div>short</div>"

    def test_max_len_truncates_long_text(self):
        text = "A" * 5000
        result = sync_devops.wrap_html(text, max_len=100)
        assert "truncated" in result
        # The raw text inside the div should be well under 5000 chars
        assert len(result) < 1000

    def test_max_len_zero_means_no_limit(self):
        text = "B" * 5000
        result = sync_devops.wrap_html(text, max_len=0)
        assert "truncated" not in result
        assert "B" * 100 in result


# --- truncate_title ---

class TestTruncateTitle:
    def test_short_title_unchanged(self):
        assert sync_devops.truncate_title("Hello World") == "Hello World"

    def test_exact_255_unchanged(self):
        title = "A" * 255
        assert sync_devops.truncate_title(title) == title

    def test_over_255_truncated(self):
        title = "A" * 300
        result = sync_devops.truncate_title(title)
        assert len(result) == 255
        assert result.endswith("...")

    def test_custom_max_len(self):
        title = "A" * 50
        result = sync_devops.truncate_title(title, max_len=20)
        assert len(result) == 20
        assert result.endswith("...")

    def test_empty_string(self):
        assert sync_devops.truncate_title("") == ""


# --- get_default_iteration ---

class TestGetDefaultIteration:
    def test_with_root_and_project(self):
        config = {"iterationRootPath": "Iterations", "projectName": "MyProject"}
        assert sync_devops.get_default_iteration(config) == "MyProject\\Iterations"

    def test_root_already_includes_project(self):
        config = {"iterationRootPath": "MyProject\\Iterations", "projectName": "MyProject"}
        assert sync_devops.get_default_iteration(config) == "MyProject\\Iterations"

    def test_no_root_returns_empty(self):
        config = {"projectName": "MyProject"}
        assert sync_devops.get_default_iteration(config) == ""

    def test_no_project(self):
        config = {"iterationRootPath": "Iterations"}
        assert sync_devops.get_default_iteration(config) == "Iterations"


# --- find_az_executable ---

class TestFindAzExecutable:
    def test_returns_string(self):
        result = sync_devops.find_az_executable()
        assert isinstance(result, str)
        assert len(result) > 0


# --- build_task_description ---

class TestBuildTaskDescription:
    def test_review_task_with_file_path(self):
        task = {"isReviewFollowup": True, "filePath": "src/api/handler.py:42"}
        result = sync_devops.build_task_description(task)
        assert "<code>" in result
        assert "src/api/handler.py:42" in result
        assert "<b>File:</b>" in result

    def test_review_task_no_file_path(self):
        task = {"isReviewFollowup": True, "filePath": None}
        result = sync_devops.build_task_description(task)
        assert result == ""

    def test_regular_task_with_subtasks_and_ac(self):
        task = {
            "acReferences": [1, 3],
            "subtaskHtml": "<div><ul><li>&#9744; Sub A</li></ul></div>"
        }
        result = sync_devops.build_task_description(task)
        assert "Acceptance Criteria:" in result
        assert "1, 3" in result
        assert "&#9744; Sub A" in result

    def test_regular_task_no_enrichment(self):
        task = {"acReferences": [], "subtaskHtml": ""}
        result = sync_devops.build_task_description(task)
        assert result == ""

    def test_html_escaping_in_file_path(self):
        task = {"isReviewFollowup": True, "filePath": "src/<gen>/foo.py"}
        result = sync_devops.build_task_description(task)
        assert "&lt;gen&gt;" in result


# --- build_task_create_args ---

class TestBuildTaskCreateArgs:
    def test_regular_task_basic(self):
        task = {"description": "Set up auth", "acReferences": [], "subtaskHtml": ""}
        args = sync_devops.build_task_create_args(task, "MyArea", "MyIter")
        assert "--type" in args
        assert "Task" in args
        assert "--title" in args
        idx = args.index("--title")
        assert args[idx + 1] == "Set up auth"
        assert "--area" in args
        assert "--iteration" in args

    def test_review_task_uses_clean_title(self):
        task = {
            "description": "[HIGH] [AI-Review] Fix null check [src/h.py:42]",
            "isReviewFollowup": True,
            "cleanTitle": "Fix null check",
            "priority": 1,
            "filePath": "src/h.py:42",
            "tags": ["AI-Review"],
        }
        args = sync_devops.build_task_create_args(task, "", "")
        idx = args.index("--title")
        assert args[idx + 1] == "Fix null check"

    def test_priority_field_set(self):
        task = {
            "description": "Fix",
            "isReviewFollowup": True,
            "cleanTitle": "Fix",
            "priority": 2,
            "filePath": None,
            "tags": [],
        }
        args = sync_devops.build_task_create_args(task, "", "")
        assert "Microsoft.VSTS.Common.Priority=2" in args

    def test_tags_field_set(self):
        task = {
            "description": "Fix",
            "isReviewFollowup": True,
            "cleanTitle": "Fix",
            "priority": None,
            "filePath": None,
            "tags": ["AI-Review"],
        }
        args = sync_devops.build_task_create_args(task, "", "")
        assert "System.Tags=AI-Review" in args

    def test_subtask_html_in_description(self):
        task = {
            "description": "Main task",
            "acReferences": [],
            "subtaskHtml": "<div><ul><li>&#9744; Sub</li></ul></div>"
        }
        args = sync_devops.build_task_create_args(task, "", "")
        assert "--description" in args
        idx = args.index("--description")
        assert "&#9744; Sub" in args[idx + 1]

    def test_ac_description_in_args(self):
        task = {
            "description": "Main task",
            "acReferences": [1, 3],
            "subtaskHtml": ""
        }
        args = sync_devops.build_task_create_args(task, "", "")
        assert "--description" in args
        idx = args.index("--description")
        assert "1, 3" in args[idx + 1]

    def test_no_description_when_no_enrichment(self):
        task = {"description": "Plain task", "acReferences": [], "subtaskHtml": ""}
        args = sync_devops.build_task_create_args(task, "", "")
        assert "--description" not in args


# --- build_task_update_args ---

class TestBuildTaskUpdateArgs:
    def test_regular_task_state_mapping(self):
        task = {"description": "Do thing", "complete": True, "acReferences": [], "subtaskHtml": ""}
        args = sync_devops.build_task_update_args(task, 999, "Closed")
        assert "--id" in args
        assert "999" in args
        assert "--state" in args
        idx = args.index("--state")
        assert args[idx + 1] == "Closed"

    def test_incomplete_task_state_new(self):
        task = {"description": "Do thing", "complete": False, "acReferences": [], "subtaskHtml": ""}
        args = sync_devops.build_task_update_args(task, 999, "Closed")
        idx = args.index("--state")
        assert args[idx + 1] == "New"

    def test_review_task_uses_clean_title(self):
        task = {
            "description": "[HIGH] Fix it [src/f.py]",
            "isReviewFollowup": True,
            "cleanTitle": "Fix it",
            "complete": False,
            "priority": 1,
            "filePath": "src/f.py",
            "tags": ["AI-Review"],
        }
        args = sync_devops.build_task_update_args(task, 100, "Done")
        idx = args.index("--title")
        assert args[idx + 1] == "Fix it"
        assert "Microsoft.VSTS.Common.Priority=1" in args
        assert "System.Tags=AI-Review" in args

    def test_updates_include_title(self):
        task = {"description": "My task", "complete": False, "acReferences": [], "subtaskHtml": ""}
        args = sync_devops.build_task_update_args(task, 100, "Done")
        assert "--title" in args
        idx = args.index("--title")
        assert args[idx + 1] == "My task"


# --- detect_template (from detect-template.py) ---

detect_template = importlib.import_module("detect-template")


class TestDetectTemplate:
    def test_agile(self):
        assert detect_template.detect_template(["Epic", "User Story", "Task", "Bug"]) == "Agile"

    def test_scrum(self):
        assert detect_template.detect_template(["Epic", "Product Backlog Item", "Task"]) == "Scrum"

    def test_cmmi(self):
        assert detect_template.detect_template(["Epic", "Requirement", "Task"]) == "CMMI"

    def test_basic(self):
        assert detect_template.detect_template(["Epic", "Issue", "Task"]) == "Basic"

    def test_unknown(self):
        assert detect_template.detect_template(["Custom Type"]) == "Unknown"

    def test_priority_agile_over_basic(self):
        # If both User Story and Issue exist, Agile wins
        assert detect_template.detect_template(["User Story", "Issue"]) == "Agile"
