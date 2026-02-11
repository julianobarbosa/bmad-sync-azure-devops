"""Tests for parse-artifacts.py."""

import os
import importlib

import pytest

parse_artifacts = importlib.import_module("parse-artifacts")


# --- detect_heading_levels ---

class TestDetectHeadingLevels:
    def test_double_hash(self):
        content = "## Epic 1: Foundation\nSome text"
        assert parse_artifacts.detect_heading_levels(content) == (2, 3)

    def test_triple_hash(self):
        content = "### Epic 1: Foundation\nSome text"
        assert parse_artifacts.detect_heading_levels(content) == (3, 4)

    def test_quad_hash(self):
        content = "#### Epic 2: Security\nSome text"
        assert parse_artifacts.detect_heading_levels(content) == (4, 5)

    def test_no_epic_heading_defaults(self):
        content = "# Overview\nNo epic headings here"
        assert parse_artifacts.detect_heading_levels(content) == (2, 3)

    def test_empty_content(self):
        assert parse_artifacts.detect_heading_levels("") == (2, 3)


# --- parse_epics_file ---

class TestParseEpicsFile:
    def test_basic_epic(self, tmp_file):
        path = tmp_file("## Epic 1: Foundation\nDescription text\n**Phase:** Alpha\n")
        epics, stories = parse_artifacts.parse_epics_file(path)
        assert len(epics) == 1
        assert epics[0]["id"] == "1"
        assert epics[0]["title"] == "Foundation"
        assert epics[0]["phase"] == "Alpha"

    def test_multiple_epics(self, tmp_file):
        content = (
            "## Epic 1: First\nDesc 1\n\n"
            "## Epic 2: Second\nDesc 2\n"
        )
        path = tmp_file(content)
        epics, stories = parse_artifacts.parse_epics_file(path)
        assert len(epics) == 2
        assert epics[0]["id"] == "1"
        assert epics[1]["id"] == "2"

    def test_epic_with_stories(self, tmp_file):
        content = (
            "## Epic 1: Foundation\nEpic desc\n\n"
            "### Story 1.1: Setup\nStory desc\n\n"
            "### Story 1.2: Config\nConfig desc\n"
        )
        path = tmp_file(content)
        epics, stories = parse_artifacts.parse_epics_file(path)
        assert len(epics) == 1
        assert len(stories) == 2
        assert stories[0]["id"] == "1.1"
        assert stories[0]["epicId"] == "1"
        assert stories[1]["id"] == "1.2"

    def test_story_acceptance_criteria(self, tmp_file):
        content = (
            "## Epic 1: Test\nDesc\n\n"
            "### Story 1.1: Setup\nStory text\n"
            "**Acceptance Criteria:**\n"
            "- [ ] AC item 1\n"
            "- [x] AC item 2\n"
        )
        path = tmp_file(content)
        _, stories = parse_artifacts.parse_epics_file(path)
        assert "AC item 1" in stories[0]["acceptanceCriteria"]
        assert "AC item 2" in stories[0]["acceptanceCriteria"]

    def test_requirements_extraction(self, tmp_file):
        content = (
            "## Epic 1: Test\n"
            "References FR-1.1 and NFR-2.3 and ARCH-DB\n"
        )
        path = tmp_file(content)
        epics, _ = parse_artifacts.parse_epics_file(path)
        assert "FR-1.1" in epics[0]["requirements"]
        assert "NFR-2.3" in epics[0]["requirements"]
        assert "ARCH-DB" in epics[0]["requirements"]

    def test_dependencies_extraction(self, tmp_file):
        content = (
            "## Epic 1: Test\n"
            "**Dependencies:** Epic 2; Epic 3\n"
        )
        path = tmp_file(content)
        epics, _ = parse_artifacts.parse_epics_file(path)
        assert "Epic 2" in epics[0]["dependencies"]
        assert "Epic 3" in epics[0]["dependencies"]

    def test_target_phase_variant(self, tmp_file):
        content = "## Epic 1: Test\n**Target Phase:** Beta\n"
        path = tmp_file(content)
        epics, _ = parse_artifacts.parse_epics_file(path)
        assert epics[0]["phase"] == "Beta"

    def test_duplicate_epics_deduplicated(self, tmp_file):
        content = (
            "## Epic 1: First occurrence\nDesc 1\n\n"
            "## Epic 2: Second\nDesc 2\n\n"
            "## Epic 1: Duplicate\nDuplicate desc\n"
        )
        path = tmp_file(content)
        epics, _ = parse_artifacts.parse_epics_file(path)
        assert len(epics) == 2
        assert epics[0]["title"] == "First occurrence"

    def test_nonexistent_file(self):
        epics, stories = parse_artifacts.parse_epics_file("/nonexistent/path.md")
        assert epics == []
        assert stories == []

    def test_triple_hash_level(self, tmp_file):
        content = (
            "### Epic 1: Deep\nDesc\n\n"
            "#### Story 1.1: Deeper\nStory text\n"
        )
        path = tmp_file(content)
        epics, stories = parse_artifacts.parse_epics_file(path)
        assert len(epics) == 1
        assert len(stories) == 1


# --- parse_story_file ---

class TestParseStoryFile:
    def test_tasks_extraction(self, tmp_file):
        content = (
            "# Story 1.1\n**Status:** in-progress\n\n"
            "## Tasks / Subtasks\n"
            "- [ ] First task\n"
            "- [x] Second task\n"
            "  - [ ] Subtask A\n"
            "  - [x] Subtask B\n"
        )
        path = tmp_file(content)
        tasks, status, review_tasks = parse_artifacts.parse_story_file("1.1", path)
        assert len(tasks) == 2
        assert tasks[0]["id"] == "1.1-T1"
        assert tasks[0]["complete"] is False
        assert tasks[1]["id"] == "1.1-T2"
        assert tasks[1]["complete"] is True
        assert len(tasks[1]["subtasks"]) == 2
        assert tasks[1]["subtasks"][0]["id"] == "1.1-T2.1"
        assert tasks[1]["subtasks"][1]["complete"] is True

    def test_status_extraction(self, tmp_file):
        path = tmp_file("**Status:** done\n## Tasks / Subtasks\n- [ ] Task\n")
        _, status, _ = parse_artifacts.parse_story_file("1.1", path)
        assert status == "done"

    def test_status_without_bold(self, tmp_file):
        path = tmp_file("Status: in-progress\n")
        _, status, _ = parse_artifacts.parse_story_file("1.1", path)
        assert status == "in-progress"

    def test_review_followups(self, tmp_file):
        content = (
            "# Story\n\n"
            "### Review Follow-ups (AI)\n"
            "- [ ] Fix error handling\n"
            "- [x] Add logging\n\n"
            "### Review Follow-ups Round 2 (AI)\n"
            "- [ ] Refactor method\n"
        )
        path = tmp_file(content)
        _, _, review_tasks = parse_artifacts.parse_story_file("1.1", path)
        assert len(review_tasks) == 3
        assert review_tasks[0]["id"] == "1.1-R1.1"
        assert review_tasks[0]["reviewRound"] == 1
        assert review_tasks[0]["isReviewFollowup"] is True
        assert review_tasks[1]["id"] == "1.1-R1.2"
        assert review_tasks[1]["complete"] is True
        assert review_tasks[2]["id"] == "1.1-R2.1"
        assert review_tasks[2]["reviewRound"] == 2

    def test_nonexistent_file(self):
        tasks, status, review_tasks = parse_artifacts.parse_story_file("1.1", "/nonexistent.md")
        assert tasks == []
        assert status is None
        assert review_tasks == []

    def test_no_tasks_section(self, tmp_file):
        path = tmp_file("# Story 1.1\nJust description, no tasks.\n")
        tasks, _, _ = parse_artifacts.parse_story_file("1.1", path)
        assert tasks == []


# --- story_id_from_filename ---

class TestStoryIdFromFilename:
    def test_standard_filename(self):
        assert parse_artifacts.story_id_from_filename("1-1-initialize-scaffold.md") == "1.1"

    def test_double_digit(self):
        assert parse_artifacts.story_id_from_filename("12-3-some-feature.md") == "12.3"

    def test_no_match(self):
        assert parse_artifacts.story_id_from_filename("readme.md") is None

    def test_no_trailing_slug(self):
        assert parse_artifacts.story_id_from_filename("1-1-") is None or \
               parse_artifacts.story_id_from_filename("1-1-") == "1.1"


# --- scan_story_files ---

class TestScanStoryFiles:
    def test_flat_file_discovery(self, tmp_path):
        story_file = tmp_path / "1-1-test-story.md"
        story_file.write_text(
            "**Status:** done\n## Tasks / Subtasks\n- [x] Task one\n",
            encoding="utf-8"
        )
        tasks, statuses, _ = parse_artifacts.scan_story_files(str(tmp_path), [])
        assert "1.1" in tasks
        assert statuses["1.1"] == "done"

    def test_nested_directory_discovery(self, tmp_path):
        story_dir = tmp_path / "2.1"
        story_dir.mkdir()
        story_file = story_dir / "story.md"
        story_file.write_text(
            "**Status:** in-progress\n## Tasks / Subtasks\n- [ ] Task\n",
            encoding="utf-8"
        )
        tasks, statuses, _ = parse_artifacts.scan_story_files(str(tmp_path), ["2.1"])
        assert "2.1" in tasks
        assert statuses["2.1"] == "in-progress"

    def test_nonexistent_dir(self):
        tasks, statuses, reviews = parse_artifacts.scan_story_files("/nonexistent", [])
        assert tasks == {}
        assert statuses == {}
        assert reviews == {}


# --- parse_epic_statuses ---

class TestParseEpicStatuses:
    def test_basic_statuses(self, tmp_file):
        content = (
            "development_status:\n"
            "  epic-1: in-progress\n"
            "  epic-2: backlog\n"
            "  epic-3: done\n"
        )
        path = tmp_file(content, "sprint-status.yaml")
        result = parse_artifacts.parse_epic_statuses(path)
        assert result == {"1": "in-progress", "2": "backlog", "3": "done"}

    def test_stops_at_next_section(self, tmp_file):
        content = (
            "development_status:\n"
            "  epic-1: in-progress\n"
            "other_section:\n"
            "  epic-2: should-not-appear\n"
        )
        path = tmp_file(content, "sprint-status.yaml")
        result = parse_artifacts.parse_epic_statuses(path)
        assert result == {"1": "in-progress"}
        assert "2" not in result

    def test_empty_file(self, tmp_file):
        path = tmp_file("", "sprint-status.yaml")
        assert parse_artifacts.parse_epic_statuses(path) == {}

    def test_no_development_status(self, tmp_file):
        path = tmp_file("other_key: value\n", "sprint-status.yaml")
        assert parse_artifacts.parse_epic_statuses(path) == {}

    def test_nonexistent_file(self):
        assert parse_artifacts.parse_epic_statuses("/nonexistent.yaml") == {}

    def test_none_path(self):
        assert parse_artifacts.parse_epic_statuses(None) == {}

    def test_uppercase_status_normalized(self, tmp_file):
        content = "development_status:\n  epic-1: IN-PROGRESS\n"
        path = tmp_file(content, "sprint-status.yaml")
        result = parse_artifacts.parse_epic_statuses(path)
        assert result["1"] == "in-progress"

    def test_many_epics(self, tmp_file):
        lines = ["development_status:"]
        for i in range(1, 16):
            lines.append(f"  epic-{i}: backlog")
        path = tmp_file("\n".join(lines), "sprint-status.yaml")
        result = parse_artifacts.parse_epic_statuses(path)
        assert len(result) == 15
