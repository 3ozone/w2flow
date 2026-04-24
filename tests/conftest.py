"""
Fixtures globales de pytest para w2flow.

Organizacion de tests (espejo de app/):
  tests/
  ├── domain/          → entidades, value objects, enums
  ├── application/     → commands, queries
  └── infrastructure/  → API, repositorios
"""

import pytest


# ── Fixtures de dominio ───────────────────────────────────────────

@pytest.fixture
def valid_tender_data() -> dict:
    """Datos mínimos válidos para construir un Tender."""
    return {
        "expedient_code": "EXP-2026-001",
        "title": "Servei de neteja d'edificis municipals",
        "budget": 50_000.0,
        "deadline": "2026-06-01",
        "contracting_authority": "Ajuntament de Barcelona",
    }


@pytest.fixture
def valid_filter_config_data() -> dict:
    """Datos mínimos válidos para construir un FilterConfig."""
    return {
        "keywords": ["neteja", "manteniment"],
        "max_budget": 100_000.0,
        "min_budget": 10_000.0,
    }
