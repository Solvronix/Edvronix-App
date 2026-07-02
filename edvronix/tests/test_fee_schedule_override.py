"""
Unit tests for CustomFeeSchedule._get_coverage_issues().

Run with:
    bench --site <site> run-tests --app edvronix --module edvronix.tests.test_fee_schedule_override
"""
import unittest
from unittest.mock import MagicMock, patch

import frappe


class TestGetCoverageIssues(unittest.TestCase):
    def _make_doc(self, fee_structure, academic_year, student_groups=None):
        """Build a minimal mock Fee Schedule document."""
        doc = MagicMock()
        doc.fee_structure = fee_structure
        doc.academic_year = academic_year
        doc.student_groups = [
            MagicMock(student_group=sg) for sg in (student_groups or [])
        ]
        # Bind the real method to our mock doc
        from edvronix.fee_schedule_override import CustomFeeSchedule
        doc._get_coverage_issues = CustomFeeSchedule._get_coverage_issues.__get__(doc)
        doc._format_issues = CustomFeeSchedule._format_issues.__get__(doc)
        return doc

    @patch("frappe.db.get_value")
    def test_no_program_returns_empty(self, mock_get_value):
        """If the Fee Structure has no program, return no issues."""
        mock_get_value.return_value = None
        doc = self._make_doc("FS-001", "2026-2027")
        issues = doc._get_coverage_issues()
        self.assertEqual(issues, [])

    @patch("frappe.get_all")
    @patch("frappe.db.get_value")
    def test_missing_groups_detected(self, mock_get_value, mock_get_all):
        """Groups in DB but absent from the schedule should be flagged."""
        mock_get_value.return_value = "Grade 1"  # program
        mock_get_all.return_value = ["Grade 1 - A", "Grade 1 - B"]  # all groups in DB
        # Schedule contains no groups
        doc = self._make_doc("FS-001", "2026-2027", student_groups=[])
        issues = doc._get_coverage_issues()
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["type"], "missing_groups")
        self.assertIn("Grade 1 - A", issues[0]["items"])
        self.assertIn("Grade 1 - B", issues[0]["items"])

    @patch("frappe.get_all")
    @patch("frappe.db.sql")
    @patch("frappe.db.get_value")
    def test_no_issues_when_all_matched(self, mock_get_value, mock_db_sql, mock_get_all):
        """No issues when all groups present and all enrolled students are in groups."""
        # program
        mock_get_value.side_effect = lambda dt, name, field, **kw: (
            "Grade 1" if field == "program" else
            {"program": "Grade 1", "academic_year": "2026-2027",
             "academic_term": None, "batch": None, "student_category": None}
        )
        mock_get_all.side_effect = lambda dt, **kw: (
            ["Grade 1 - A"] if dt == "Student Group" else ["EDU-STU-001"]
        )
        mock_db_sql.return_value = [{"student": "EDU-STU-001", "student_name": "Ahmed Khan"}]
        doc = self._make_doc("FS-001", "2026-2027", student_groups=["Grade 1 - A"])
        issues = doc._get_coverage_issues()
        self.assertEqual(issues, [])

    def test_format_issues_html(self):
        """_format_issues should produce non-empty HTML for a list of issues."""
        doc = self._make_doc("FS-001", "2026-2027")
        issues = [{"message": "Test message", "items": ["Item 1", "Item 2"]}]
        html = doc._format_issues(issues)
        self.assertIn("Test message", html)
        self.assertIn("Item 1", html)
        self.assertIn("Item 2", html)


class TestPreventEnablingGraduatedStudent(unittest.TestCase):
    @patch("frappe.db.sql")
    @patch("frappe.db.get_value")
    @patch("frappe.throw")
    def test_blocks_re_enabling_graduated(self, mock_throw, mock_get_value, mock_sql):
        """Validate handler must call frappe.throw for a graduated student."""
        mock_get_value.return_value = ("EDU-STU-001", 0, "Graduated")
        mock_sql.return_value = [{"name": "GRAD-001"}]

        doc = MagicMock()
        doc.name = "EDU-STU-001"
        doc.enabled = 1  # user is trying to re-enable

        from edvronix.events import prevent_enabling_graduated_student
        prevent_enabling_graduated_student(doc, None)
        self.assertTrue(mock_throw.called)

    @patch("frappe.db.get_value")
    @patch("frappe.throw")
    def test_allows_enabling_non_graduated(self, mock_throw, mock_get_value):
        """Active students (not graduated) should not trigger a throw."""
        mock_get_value.return_value = ("EDU-STU-002", 1, None)

        doc = MagicMock()
        doc.name = "EDU-STU-002"
        doc.enabled = 1

        from edvronix.events import prevent_enabling_graduated_student
        prevent_enabling_graduated_student(doc, None)
        mock_throw.assert_not_called()


if __name__ == "__main__":
    unittest.main()
