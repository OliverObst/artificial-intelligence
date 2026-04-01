"""Curated CSP map-colouring examples."""

from __future__ import annotations

from ai9414.csp.models import CspExample, CspProblem, RegionGeometry


def _australia_geometry() -> dict[str, RegionGeometry]:
    return {
        "wa": RegionGeometry(
            points=[
                (108, 118),
                (246, 102),
                (292, 134),
                (300, 214),
                (286, 278),
                (292, 366),
                (248, 440),
                (152, 446),
                (108, 366),
                (102, 242),
                (90, 174),
            ],
            label=(192, 262),
            domain_anchor=(192, 300),
        ),
        "nt": RegionGeometry(
            points=[
                (292, 116),
                (444, 106),
                (524, 124),
                (548, 190),
                (540, 252),
                (470, 296),
                (360, 296),
                (302, 258),
                (292, 196),
            ],
            label=(414, 206),
            domain_anchor=(414, 244),
        ),
        "sa": RegionGeometry(
            points=[
                (256, 298),
                (360, 292),
                (478, 298),
                (544, 336),
                (560, 430),
                (534, 510),
                (454, 560),
                (336, 552),
                (276, 500),
                (250, 418),
                (238, 340),
            ],
            label=(398, 416),
            domain_anchor=(398, 454),
        ),
        "q": RegionGeometry(
            points=[
                (528, 116),
                (668, 122),
                (754, 138),
                (816, 188),
                (842, 270),
                (822, 346),
                (742, 378),
                (636, 348),
                (582, 300),
                (540, 240),
            ],
            label=(684, 226),
            domain_anchor=(684, 264),
        ),
        "nsw": RegionGeometry(
            points=[
                (548, 334),
                (642, 338),
                (748, 370),
                (818, 418),
                (832, 498),
                (798, 556),
                (706, 576),
                (620, 548),
                (564, 488),
                (546, 412),
            ],
            label=(686, 438),
            domain_anchor=(686, 476),
        ),
        "v": RegionGeometry(
            points=[
                (500, 530),
                (590, 528),
                (656, 552),
                (706, 600),
                (688, 638),
                (610, 650),
                (528, 634),
                (468, 590),
            ],
            label=(586, 592),
            domain_anchor=(586, 628),
        ),
        "t": RegionGeometry(
            points=[
                (724, 640),
                (752, 626),
                (788, 634),
                (804, 660),
                (790, 694),
                (752, 702),
                (724, 684),
                (714, 660),
            ],
            label=(760, 664),
            domain_anchor=(760, 698),
        ),
    }


def _mini_easy_geometry() -> dict[str, RegionGeometry]:
    return {
        "a": RegionGeometry(points=[(118, 124), (308, 124), (308, 270), (142, 294), (90, 210)], label=(198, 198), domain_anchor=(198, 236)),
        "b": RegionGeometry(points=[(308, 124), (506, 124), (530, 270), (332, 288), (308, 270)], label=(418, 198), domain_anchor=(418, 236)),
        "c": RegionGeometry(points=[(506, 124), (716, 124), (760, 220), (700, 316), (530, 270)], label=(628, 204), domain_anchor=(628, 242)),
        "d": RegionGeometry(points=[(126, 292), (322, 286), (346, 484), (154, 520), (94, 406)], label=(218, 392), domain_anchor=(218, 430)),
        "e": RegionGeometry(points=[(322, 286), (532, 270), (562, 488), (354, 502)], label=(436, 394), domain_anchor=(436, 432)),
        "f": RegionGeometry(points=[(532, 270), (700, 316), (756, 510), (562, 530)], label=(640, 412), domain_anchor=(640, 450)),
    }


def _mini_tight_geometry() -> dict[str, RegionGeometry]:
    return {
        "a": RegionGeometry(points=[(168, 130), (332, 118), (364, 240), (230, 308), (130, 230)], label=(246, 194), domain_anchor=(246, 232)),
        "b": RegionGeometry(points=[(332, 118), (530, 120), (550, 266), (364, 240)], label=(438, 190), domain_anchor=(438, 228)),
        "c": RegionGeometry(points=[(530, 120), (722, 138), (742, 282), (550, 266)], label=(632, 204), domain_anchor=(632, 242)),
        "d": RegionGeometry(points=[(230, 308), (364, 240), (550, 266), (486, 430), (286, 454)], label=(388, 346), domain_anchor=(388, 384)),
        "e": RegionGeometry(points=[(164, 450), (286, 454), (334, 602), (142, 612)], label=(238, 528), domain_anchor=(238, 566)),
        "f": RegionGeometry(points=[(486, 430), (660, 424), (734, 592), (544, 612)], label=(604, 516), domain_anchor=(604, 554)),
    }


def build_examples() -> dict[str, CspExample]:
    """Return the curated teaching examples for CSP map colouring."""

    australia_neighbours = {
        "wa": ["nt", "sa"],
        "nt": ["wa", "sa", "q"],
        "sa": ["wa", "nt", "q", "nsw", "v"],
        "q": ["nt", "sa", "nsw"],
        "nsw": ["q", "sa", "v"],
        "v": ["sa", "nsw"],
        "t": [],
    }

    mini_easy_neighbours = {
        "a": ["b", "d"],
        "b": ["a", "c", "d", "e"],
        "c": ["b", "e", "f"],
        "d": ["a", "b", "e"],
        "e": ["b", "c", "d", "f"],
        "f": ["c", "e"],
    }

    mini_tight_neighbours = {
        "a": ["b", "d", "e"],
        "b": ["a", "c", "d"],
        "c": ["b", "d", "f"],
        "d": ["a", "b", "c", "e", "f"],
        "e": ["a", "d"],
        "f": ["c", "d"],
    }

    examples = {
        "australia": CspExample(
            title="CSP Demo - Australia Map Colouring",
            subtitle="The standard Australia map-colouring CSP. Tasmania stays unconstrained, so compare it with the more informative mainland regions.",
            problem=CspProblem(
                title="Australia map colouring",
                subtitle="Colour Australia so neighbouring regions are always different.",
                regions=["wa", "nt", "sa", "q", "nsw", "v", "t"],
                colours=["red", "green", "blue"],
                neighbours=australia_neighbours,
                geometry=_australia_geometry(),
            ),
        ),
        "australia_unsat_2_colours": CspExample(
            title="CSP Demo - Australia with Two Colours",
            subtitle="The same Australia map, but only two colours are available. Forward checking will eventually prove that no legal colouring exists.",
            problem=CspProblem(
                title="Australia with two colours",
                subtitle="Try to colour the map with only red and green. This CSP is unsatisfiable.",
                regions=["wa", "nt", "sa", "q", "nsw", "v", "t"],
                colours=["red", "green"],
                neighbours=australia_neighbours,
                geometry=_australia_geometry(),
            ),
        ),
        "mini_map_easy": CspExample(
            title="CSP Demo - Mini Map (Easy)",
            subtitle="A small six-region map with a clear structure. Useful for a first run before switching to Australia.",
            problem=CspProblem(
                title="Mini map",
                subtitle="A small made-up map for first exposure to variables, domains, and constraints.",
                regions=["a", "b", "c", "d", "e", "f"],
                colours=["red", "green", "blue"],
                neighbours=mini_easy_neighbours,
                geometry=_mini_easy_geometry(),
            ),
        ),
        "mini_map_tight": CspExample(
            title="CSP Demo - Mini Map (Tight)",
            subtitle="A tighter six-region map with a highly connected centre. Forward checking removes colours quickly, especially around the middle region.",
            problem=CspProblem(
                title="Tight mini map",
                subtitle="A tighter made-up map where local propagation is much more visible.",
                regions=["a", "b", "c", "d", "e", "f"],
                colours=["red", "green", "blue", "yellow"],
                neighbours=mini_tight_neighbours,
                geometry=_mini_tight_geometry(),
            ),
        ),
    }

    return examples
