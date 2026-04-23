"""Link models for object relationships.

Canonical link types define relationships between RAPai objects. 8 types total.
Source: ontology/schemas/links.json (Draft 2020-12, v0.1.0)
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Link(BaseModel):
    """Base Link model for all relationship types."""

    model_config = ConfigDict(extra="forbid")

    link_id: str | None = Field(
        None,
        pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$",
        description="ULID for this link (auto-generated if not provided)",
    )
    link_type: str = Field(..., description="Type of relationship (see LinkType enum)")
    from_id: str = Field(..., pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    to_id: str = Field(..., pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$")
    metadata: dict | None = Field(None, description="Additional link metadata")
    created_at: str | None = None
    updated_at: str | None = None

    @model_validator(mode="after")
    def validate_link_not_self_referencing(self) -> Link:
        """Links must not reference the same object as both source and target."""
        if self.from_id == self.to_id:
            raise ValueError("link cannot reference the same object as both from_id and to_id")
        return self


# Specialized Link subclasses for type-specific validation

class DependsOnLink(Link):
    """Task → Task dependency relationship."""

    link_type: str = Field(default="depends_on", pattern="^depends_on$")
    dependency_type: str | None = Field(
        None, description="Type of dependency: blocks, waits_for, related"
    )


class ProducesLink(Link):
    """Task → Artifact production relationship."""

    link_type: str = Field(default="produces", pattern="^produces$")


class BlocksLink(Link):
    """Blocker → Task blocking relationship."""

    link_type: str = Field(default="blocks", pattern="^blocks$")


class AssignedToLink(Link):
    """Task → Person assignment relationship."""

    link_type: str = Field(default="assigned_to", pattern="^assigned_to$")
    role: str | None = Field(None, description="Role assigned")


class GovernedByLink(Link):
    """Project → Gate governance relationship."""

    link_type: str = Field(default="governed_by", pattern="^governed_by$")


class MeasuredByLink(Link):
    """Project/Task → KPI measurement relationship."""

    link_type: str = Field(default="measured_by", pattern="^measured_by$")


class RaisedFromLink(Link):
    """Risk → Blocker escalation relationship."""

    link_type: str = Field(default="raised_from", pattern="^raised_from$")


class RelatedIPLink(Link):
    """Artifact ↔ IP relationship."""

    link_type: str = Field(default="related_ip", pattern="^related_ip$")


# Link registry for type mapping
LINK_MODELS = {
    "depends_on": DependsOnLink,
    "produces": ProducesLink,
    "blocks": BlocksLink,
    "assigned_to": AssignedToLink,
    "governed_by": GovernedByLink,
    "measured_by": MeasuredByLink,
    "raised_from": RaisedFromLink,
    "related_ip": RelatedIPLink,
}


def get_link_model(link_type: str):
    """Get the appropriate Link model class for a given link type."""
    return LINK_MODELS.get(link_type, Link)
