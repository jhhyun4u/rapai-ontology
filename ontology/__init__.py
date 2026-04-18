"""RAPai L2.5 Ontology package.

Python implementation of the SSOT declared in ADR-001 (R5).
Schemas under ``ontology/schemas`` are the canonical source; Pydantic models
under ``ontology/models`` are derived (manually maintained + verified by roundtrip
tests). See ``ontology/README.md`` for the governance rules.
"""

from __future__ import annotations

__version__ = "0.1.0"
ONTOLOGY_LAYER = "L2.5"
