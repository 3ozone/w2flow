"""Tests for GetActiveFilterQueryHandler (Fase 16.1)."""

from unittest.mock import MagicMock

from app.application.use_cases.queries.get_active_filter_query import (
    GetActiveFilterQuery,
    GetActiveFilterQueryHandler,
)
from app.domain.value_objects.filter_config import FilterConfig


def _make_filter_config(**kwargs) -> FilterConfig:
    defaults = {"tipus_expedient": 1, "fase_vigent": 0,
                "sector_keywords": ("obres",)}
    defaults.update(kwargs)
    return FilterConfig(**defaults)


def _make_port(stored: FilterConfig | None = None):
    port = MagicMock()
    port.get.return_value = stored
    return port


class TestGetActiveFilterQueryHandler:
    """Tests for GetActiveFilterQueryHandler."""

    # ------------------------------------------------------------------
    # Returns stored FilterConfig when one exists
    # ------------------------------------------------------------------

    def test_returns_filter_config_when_exists(self):
        """handle() must return the FilterConfig stored in the port."""
        fc = _make_filter_config()
        handler = GetActiveFilterQueryHandler(port=_make_port(stored=fc))
        result = handler.handle(GetActiveFilterQuery())
        assert result == fc

    def test_returns_none_when_no_filter_stored(self):
        """handle() must return None when no filter has been saved yet."""
        handler = GetActiveFilterQueryHandler(port=_make_port(stored=None))
        result = handler.handle(GetActiveFilterQuery())
        assert result is None

    # ------------------------------------------------------------------
    # Delegates to port.get()
    # ------------------------------------------------------------------

    def test_calls_port_get_once(self):
        """handle() must call port.get() exactly once."""
        port = _make_port(stored=None)
        handler = GetActiveFilterQueryHandler(port=port)
        handler.handle(GetActiveFilterQuery())
        port.get.assert_called_once()

    # ------------------------------------------------------------------
    # Returned value is the exact object from the port (no copy/transform)
    # ------------------------------------------------------------------

    def test_returns_exact_object_from_port(self):
        """handle() must return the same object reference as port.get()."""
        fc = _make_filter_config(max_results=42)
        port = _make_port(stored=fc)
        handler = GetActiveFilterQueryHandler(port=port)
        result = handler.handle(GetActiveFilterQuery())
        assert result is fc
