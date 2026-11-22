"""
tests/test_cli.py
Tests for command-line entry point main.py.
"""

import sys
import pytest
from main import main


def test_cli_help(monkeypatch, capsys):
    """Test that --help prints usage and exits cleanly."""
    monkeypatch.setattr(sys, "argv", ["main.py", "--help"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "HostelGuard" in captured.out


def test_cli_missing_mode(monkeypatch):
    """Test that omitting --mode exits with code 2."""
    monkeypatch.setattr(sys, "argv", ["main.py"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2


def test_cli_serve_without_secure(monkeypatch, capsys):
    """Test that --serve with --mode insecure returns error code 2."""
    monkeypatch.setattr(sys, "argv", ["main.py", "--mode", "insecure", "--serve"])
    exit_code = main()
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "ERROR: --serve requires --mode secure" in captured.err


def test_cli_insecure_mode(monkeypatch):
    """Test main() with --mode insecure."""
    monkeypatch.setattr(sys, "argv", ["main.py", "--mode", "insecure"])
    assert main() == 0


def test_cli_secure_mode(monkeypatch):
    """Test main() with --mode secure."""
    monkeypatch.setattr(sys, "argv", ["main.py", "--mode", "secure"])
    assert main() == 0
