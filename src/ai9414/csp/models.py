"""Domain models for the CSP map-colouring demo."""

from __future__ import annotations

import math
from typing import Any

from pydantic import Field, model_validator

from ai9414.core.models import AI9414Model, SCHEMA_VERSION

BASE_COLOUR_VALUES: dict[str, str] = {
    "red": "#c75b4a",
    "green": "#4f8b63",
    "blue": "#4d79ab",
    "yellow": "#c7a233",
    "orange": "#d07a2b",
    "purple": "#7f6cb5",
    "teal": "#2b8c88",
    "brown": "#8b674f",
}


def _fallback_colour_value(name: str) -> str:
    seed = sum(ord(character) for character in name) % 360
    hue = seed
    saturation = 46
    lightness = 54
    return f"hsl({hue} {saturation}% {lightness}%)"


def resolve_colour_values(colours: list[str]) -> dict[str, str]:
    """Return stable display values for colour names."""

    resolved: dict[str, str] = {}
    for colour in colours:
        key = colour.lower()
        resolved[colour] = BASE_COLOUR_VALUES.get(key, _fallback_colour_value(key))
    return resolved


def extend_colour_list(base_colours: list[str], count: int) -> list[str]:
    """Extend the current colour list up to ``count`` using the standard teaching palette."""

    palette = ["red", "green", "blue", "yellow"]
    ordered: list[str] = []
    for colour in list(base_colours) + palette:
        if colour not in ordered:
            ordered.append(colour)
    return ordered[:count]


class RegionGeometry(AI9414Model):
    """Stylised polygon data for one region in the rendered map."""

    points: list[tuple[float, float]]
    label: tuple[float, float]
    domain_anchor: tuple[float, float] | None = None


def _regular_polygon(cx: float, cy: float, radius: float, *, sides: int = 6, rotation: float = 0.0) -> list[tuple[float, float]]:
    return [
        (
            round(cx + math.cos(rotation + (2 * math.pi * index) / sides) * radius, 3),
            round(cy + math.sin(rotation + (2 * math.pi * index) / sides) * radius, 3),
        )
        for index in range(sides)
    ]


def build_generic_geometry(regions: list[str]) -> dict[str, RegionGeometry]:
    """Build a simple polygon layout for custom map problems without supplied geometry."""

    count = max(len(regions), 1)
    centre_x = 500.0
    centre_y = 350.0
    orbit = 210.0 if count > 4 else 165.0
    radius = 72.0 if count > 6 else 82.0
    geometry: dict[str, RegionGeometry] = {}

    for index, region in enumerate(regions):
        angle = -math.pi / 2 + (2 * math.pi * index) / count
        cx = centre_x + math.cos(angle) * orbit
        cy = centre_y + math.sin(angle) * orbit
        points = _regular_polygon(cx, cy, radius, sides=6, rotation=math.pi / 6)
        geometry[region] = RegionGeometry(
            points=points,
            label=(round(cx, 3), round(cy - 6, 3)),
            domain_anchor=(round(cx, 3), round(cy + 28, 3)),
        )

    return geometry


class CspProblem(AI9414Model):
    """A small map-colouring CSP definition."""

    title: str = "Map-colouring CSP"
    subtitle: str = "Assign colours so neighbouring regions never share the same colour."
    regions: list[str]
    colours: list[str]
    neighbours: dict[str, list[str]]
    domains: dict[str, list[str]] = Field(default_factory=dict)
    geometry: dict[str, RegionGeometry] = Field(default_factory=dict)
    colour_values: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _accept_variables_alias(cls, data: Any) -> Any:
        if isinstance(data, dict) and "variables" in data:
            copied = dict(data)
            if "regions" not in copied:
                copied["regions"] = list(copied["variables"])
            copied.pop("variables", None)
            return copied
        return data

    @model_validator(mode="after")
    def _normalise(self) -> "CspProblem":
        seen: set[str] = set()
        ordered_regions: list[str] = []
        for region in self.regions:
            name = str(region)
            if name not in seen:
                seen.add(name)
                ordered_regions.append(name)
        if not ordered_regions:
            raise ValueError("A CSP problem must include at least one region.")
        self.regions = ordered_regions

        if len(self.colours) < 2:
            raise ValueError("A map-colouring CSP needs at least two colours.")
        self.colours = [str(colour) for colour in self.colours]

        domain_map: dict[str, list[str]] = {}
        for region in self.regions:
            raw_domain = self.domains.get(region, self.colours)
            domain = [str(colour) for colour in raw_domain]
            if not domain:
                raise ValueError(f"Region '{region}' has an empty initial domain.")
            domain_map[region] = domain
        self.domains = domain_map

        region_order = {region: index for index, region in enumerate(self.regions)}
        neighbour_sets = {region: set() for region in self.regions}
        for region, raw_neighbours in self.neighbours.items():
            if region not in neighbour_sets:
                raise ValueError(f"Unknown region '{region}' appears in the neighbour map.")
            for neighbour in raw_neighbours:
                name = str(neighbour)
                if name not in neighbour_sets:
                    raise ValueError(f"Unknown neighbouring region '{name}' appears in the CSP.")
                if name == region:
                    continue
                neighbour_sets[region].add(name)
                neighbour_sets[name].add(region)
        self.neighbours = {
            region: sorted(neighbour_sets[region], key=lambda name: region_order[name])
            for region in self.regions
        }

        if not self.colour_values:
            self.colour_values = resolve_colour_values(self.colours)
        else:
            merged = resolve_colour_values(self.colours)
            for colour, value in self.colour_values.items():
                merged[str(colour)] = str(value)
            self.colour_values = merged

        if not self.geometry:
            self.geometry = build_generic_geometry(self.regions)
        else:
            missing = [region for region in self.regions if region not in self.geometry]
            if missing:
                generated = build_generic_geometry(missing)
                for region in missing:
                    self.geometry[region] = generated[region]

        return self

    def to_payload(self) -> dict[str, Any]:
        """Return the serialisable payload used by the browser and student solver."""

        payload = self.model_dump()
        payload["variables"] = list(self.regions)
        return payload


class CspExample(AI9414Model):
    """Curated named example metadata."""

    title: str
    subtitle: str
    problem: CspProblem


class CspConfigData(AI9414Model):
    problem: CspProblem


class CspConfigModel(AI9414Model):
    schema_version: str = SCHEMA_VERSION
    app_type: str = "csp"
    options: dict[str, Any] = Field(default_factory=dict)
    data: CspConfigData
