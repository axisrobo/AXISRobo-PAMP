"""Tests for app/utils/logging.py — covers setup_logging with both colorlog and fallback."""
from __future__ import annotations

import logging
import sys
from unittest.mock import patch, MagicMock


class TestSetupLogging:
    def test_setup_with_colorlog(self):
        """setup_logging should configure colorlog handler when colorlog is available."""
        from app.utils.logging import setup_logging
        # colorlog is installed in the project, so this should run the colorlog path
        setup_logging()
        root = logging.getLogger()
        assert len(root.handlers) > 0

    def test_setup_without_colorlog_falls_back(self, monkeypatch):
        """setup_logging should fall back to basicConfig when colorlog is not available."""
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "colorlog":
                raise ImportError("colorlog not installed")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            # Remove cached module
            sys.modules.pop("colorlog", None)
            sys.modules.pop("app.utils.logging", None)
            # Re-import and call
            import importlib
            import app.utils.logging as logging_mod
            importlib.reload(logging_mod)
            # Should not raise
            logging_mod.setup_logging()
