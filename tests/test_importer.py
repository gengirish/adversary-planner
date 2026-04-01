"""Tests for garak report importer."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from adversary_planner.importer import import_garak_report
from adversary_planner.exceptions import ReportParseError


class TestGarakImporter:
    """Test parsing of garak JSONL reports."""

    def test_import_eval_based_report(self, sample_garak_report):
        result = import_garak_report(sample_garak_report)

        assert result.source == "garak"
        assert result.total_attempts > 0
        assert result.total_mapped > 0
        assert len(result.technique_results) > 0

    def test_maps_dan_probes_to_jailbreak_technique(self, sample_garak_report):
        result = import_garak_report(sample_garak_report)
        assert "T0001" in result.technique_results

    def test_maps_encoding_probes(self, sample_garak_report):
        result = import_garak_report(sample_garak_report)
        encoding_ids = {"T0011", "T0012", "T0013", "T0014", "T0015"}
        mapped = set(result.technique_results.keys())
        assert mapped & encoding_ids, "At least one encoding technique should be mapped"

    def test_success_failure_counts_are_consistent(self, sample_garak_report):
        result = import_garak_report(sample_garak_report)
        for tid, counts in result.technique_results.items():
            assert counts["successes"] >= 0
            assert counts["failures"] >= 0

    def test_nonexistent_file_raises_error(self, tmp_path):
        with pytest.raises(ReportParseError, match="does not exist"):
            import_garak_report(tmp_path / "missing.jsonl")

    def test_empty_file_raises_error(self, tmp_path):
        empty = tmp_path / "empty.jsonl"
        empty.write_text("")
        with pytest.raises(ReportParseError, match="empty"):
            import_garak_report(empty)

    def test_report_with_only_attempts(self, tmp_path):
        """Fallback: when no eval entries exist, use raw attempts."""
        report = tmp_path / "attempts_only.jsonl"
        lines = [
            json.dumps({
                "entry_type": "attempt",
                "status": 2,
                "probe_classname": "probes.dan.Dan_6_0",
                "detector_results": {"detectors.dan.DAN": [0.9]},
            }),
            json.dumps({
                "entry_type": "attempt",
                "status": 2,
                "probe_classname": "probes.dan.Dan_6_0",
                "detector_results": {"detectors.dan.DAN": [0.1]},
            }),
        ]
        report.write_text("\n".join(lines) + "\n")

        result = import_garak_report(report)
        assert "T0001" in result.technique_results
        assert result.technique_results["T0001"]["successes"] == 1
        assert result.technique_results["T0001"]["failures"] == 1

    def test_unmapped_probes_are_recorded(self, tmp_path):
        report = tmp_path / "unknown.jsonl"
        lines = [
            json.dumps({
                "entry_type": "eval",
                "probe": "probes.custom_unknown_probe.Foo",
                "detector": "detectors.foo",
                "passed": 5, "fails": 5, "total_evaluated": 10,
            }),
        ]
        report.write_text("\n".join(lines) + "\n")

        result = import_garak_report(report)
        assert "probes.custom_unknown_probe.Foo" in result.unmapped_probes
