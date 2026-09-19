"""Approach Ladder tests — the binning/zone vocabulary, the fixture round, and the
shape rules that keep every published rate next to its sample size.

The fixture round (2 holes, id 999000111) is dated well outside a live 90-day window,
so every build() here pins `as_of` or widens `windowDays` — the ladder is date-relative
by design and the fixture must stay visible regardless of when the suite runs.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest

from src.constants import LEAVE_CLASSES
from src.ladder import (detail_bin, display_bin, exclusion, in_band, in_ring, in_zone,
                        leave_class, putter_next, render_markdown, scope_suffix,
                        stat, trust_chip, verdict_line, window_label)

EDGES = [60, 80, 100, 125, 150, 170]
BAND = [60, 170]
CLASS_EDGES = [15, 25]
EXCL = {"excludeEndLie": ["TeeBox"], "excludeShotTypes": ["LAYUP"],
        "excludeTeeShotsAbovePar": 3}


def test_in_band_is_inclusive_both_ends():
    assert in_band(60, BAND) and in_band(170, BAND)
    assert not in_band(59.9, BAND) and not in_band(170.1, BAND)
    assert in_band(None, BAND) is False


def test_display_bin_half_open_with_closed_top():
    assert display_bin(60, EDGES) == "60-80"
    assert display_bin(79.9, EDGES) == "60-80"
    assert display_bin(80, EDGES) == "80-100"
    assert display_bin(124.9, EDGES) == "100-125"
    assert display_bin(125, EDGES) == "125-150"
    assert display_bin(169.9, EDGES) == "150-170"
    assert display_bin(170.0, EDGES) == "150-170"      # the closing edge is never dropped
    assert display_bin(59.9, EDGES) is None
    assert display_bin(170.1, EDGES) is None
    assert display_bin(None, EDGES) is None


def test_detail_bin_walks_the_band_in_fixed_widths():
    assert detail_bin(60, 10, BAND) == "60-70"
    assert detail_bin(119.9, 10, BAND) == "110-120"
    assert detail_bin(120, 10, BAND) == "120-130"
    assert detail_bin(170, 10, BAND) == "160-170"
    assert detail_bin(59.9, 10, BAND) is None


def test_exclusion_drops_strokes_that_never_attempted_the_green():
    # A tee-box FINISH is the next-tee GPS artifact; start lie and end lie are separate
    # rules and must not be conflated.
    assert exclusion("TeeBox", "Fairway", 4, "APPROACH", EXCL) == "teeBoxArtifact"
    assert exclusion("Green", "Fairway", 5, "LAYUP", EXCL) == "layup"
    assert exclusion("Rough", "TeeBox", 4, "TEE", EXCL) == "teeShot"
    assert exclusion("Rough", "TeeBox", 5, "TEE", EXCL) == "teeShot"
    # A par-3 tee shot IS an approach and stays in (ADR #19 v1.1).
    assert exclusion("Green", "TeeBox", 3, "TEE", EXCL) is None
    assert exclusion("Fairway", "Rough", 4, "APPROACH", EXCL) is None
    # Missing par cannot be assumed to be a par 4 — an unknown hole keeps its stroke.
    assert exclusion("Rough", "TeeBox", None, "TEE", EXCL) is None


def test_exclusion_order_is_artifact_then_layup_then_tee_shot():
    """One stroke can satisfy two rules; the published counts must not double-count it."""
    assert exclusion("TeeBox", "TeeBox", 5, "LAYUP", EXCL) == "teeBoxArtifact"
    assert exclusion("Rough", "TeeBox", 5, "LAYUP", EXCL) == "layup"


def test_in_zone_is_the_locked_definition():
    assert in_zone("Green", 40.0, False, 15) is True       # on the green beats distance
    assert in_zone("Rough", 14.9, False, 15) is True
    assert in_zone("Rough", 15.0, False, 15) is True       # the radius is inclusive
    assert in_zone("Rough", 15.1, False, 15) is False
    assert in_zone("Rough", None, True, 15) is True        # holed
    # Unmeasurable: counted in coverage, excluded from the rate — never False.
    assert in_zone("Rough", None, False, 15) is None


def test_in_ring_needs_a_measured_leave():
    assert in_ring(9.9, 10) is True
    assert in_ring(10.0, 10) is True
    assert in_ring(10.1, 10) is False
    assert in_ring(None, 10) is None


def test_putter_next_keys_on_club_not_shot_type():
    assert putter_next(23) is True
    assert putter_next(19) is False
    assert putter_next(0) is None          # unattributed club
    assert putter_next(None) is None       # hole ended


def test_leave_class_precedence():
    # 1. holed — nothing left to finish
    assert leave_class("Green", 0.0, True, CLASS_EDGES, holed=True) is None
    # 2/3. putter next, on the green vs off it
    assert leave_class("Green", 12.0, True, CLASS_EDGES) == "greenPutted"
    assert leave_class("Fringe", 12.0, True, CLASS_EDGES) == "fringePutted"
    # 4. green with an unattributed next club still counts as green — without this
    #    fallback those shots would mislabel as "chipped".
    assert leave_class("Green", 12.0, None, CLASS_EDGES) == "greenPutted"
    assert leave_class("Green", 12.0, False, CLASS_EDGES) == "greenPutted"
    # 5. distance classes off the green
    assert leave_class("Rough", 15.0, False, CLASS_EDGES) == "chipped"
    assert leave_class("Rough", 25.0, False, CLASS_EDGES) == "pitch"
    assert leave_class("Rough", 25.1, False, CLASS_EDGES) == "long"
    # 6. unmeasurable
    assert leave_class("Rough", None, False, CLASS_EDGES) is None


def test_stat_always_carries_its_denominator():
    assert stat(0, 0) == {"pct": None, "n": 0}
    assert stat(3, 4)["pct"] == 75
    assert stat(3, 4)["n"] == 4


def test_window_and_scope_labels():
    assert window_label(90) == "last 3 mo"
    assert window_label(30) == "last month"
    assert window_label(45) == "last 45 days"
    s = scope_suffix(BAND, 90, 363)
    assert s == "60–170y · last 3 mo · n=363"


def test_trust_chip_reads_as_one_published_string():
    chip = trust_chip({"pinCoverage": {"pct": 100, "n": 405}, "approaches": 447,
                       "rounds": 30})
    assert chip == "real pins · 100% of holes · n=447 · 30 rounds"


# --------------------------------------------------------------------- verdict line
# Pure-function territory: synthetic headlines and bins, no database. The published
# sentence is the single source of truth for the card and the markdown export alike.

def _b(lo, hi, pct, n, provisional=False):
    return {"key": f"{lo}-{hi}", "label": f"{lo}–{hi}y", "loYds": lo, "hiYds": hi,
            "zone": {"pct": pct, "n": n}, "provisional": provisional}


def _h(pct=33, n=362, delta=7, prev_pct=26, prev_n=254):
    return {"zone": {"pct": pct, "n": n}, "deltaPts": delta,
            "prev": {"pct": prev_pct, "n": prev_n, "label": "previous 3 mo"}}


SHIPPED_BINS = [_b(60, 80, 43, 42), _b(80, 100, 37, 51), _b(100, 125, 39, 80),
                _b(125, 150, 37, 107), _b(150, 170, 16, 82), _b(170, 200, 10, 51),
                _b(200, 250, 6, 34)]


def test_verdict_line_is_the_published_sentence():
    v = verdict_line(_h(), SHIPPED_BINS, {"pct": 29, "n": 447}, 90)
    assert v["text"] == ("33% Green Zone — up 7 pts vs the previous 3 mo. Strongest "
                         "60–150y at 37–43%; weakest 150–250y at 6–16%.")
    assert (v["gzPct"], v["n"], v["deltaPts"], v["direction"]) == (33, 362, 7, "up")
    assert v["solid"]["label"] == "60–150y" and v["solid"]["n"] == 280
    assert v["solid"]["bins"] == ["60-80", "80-100", "100-125", "125-150"]
    assert v["weak"]["label"] == "150–250y" and v["weak"]["n"] == 167


def test_verdict_runs_split_on_the_ladder_rate_not_the_headline():
    """The table runs past the headline band, so strong/weak must be judged inside one
    scope. At a pivot of 38 the 37% bins fall to the weak side."""
    v = verdict_line(_h(), SHIPPED_BINS, {"pct": 38, "n": 447}, 90)
    assert v["solid"]["bins"] == ["60-80"]
    assert v["weak"]["bins"] == ["125-150", "150-170", "170-200", "200-250"]


def test_verdict_range_collapses_to_one_number_for_a_single_bin():
    v = verdict_line(_h(), SHIPPED_BINS, {"pct": 38, "n": 447}, 90)
    assert "Strongest 60–80y at 43%;" in v["text"]


def test_an_unrated_bin_breaks_contiguity():
    """A range with a hole in the evidence is not a range: the provisional bin splits
    the strong stretch, and the longest surviving run wins."""
    bins = [_b(60, 80, 43, 42), _b(80, 100, 37, 4, provisional=True),
            _b(100, 125, 39, 80), _b(125, 150, 37, 107), _b(150, 170, 16, 82)]
    v = verdict_line(_h(), bins, {"pct": 29, "n": 315}, 90)
    assert v["solid"]["bins"] == ["100-125", "125-150"]
    assert v["solid"]["label"] == "100–150y"


def test_run_ties_go_to_the_lower_yardage():
    bins = [_b(60, 80, 43, 42), _b(80, 100, 41, 51), _b(100, 125, 10, 80),
            _b(125, 150, 42, 107), _b(150, 170, 40, 82)]
    v = verdict_line(_h(), bins, {"pct": 29, "n": 362}, 90)
    assert v["solid"]["label"] == "60–100y"


def test_verdict_with_no_measured_approaches():
    v = verdict_line(_h(pct=None, n=0, delta=None, prev_pct=None, prev_n=0), [],
                     {"pct": None, "n": 0}, 90)
    assert v["text"] == ("Not enough measured approaches in the last 3 mo to rate the "
                         "approach game (n=0).")
    assert v["solid"] is None and v["weak"] is None and v["direction"] == "unknown"


def test_verdict_with_no_previous_window():
    v = verdict_line(_h(delta=None), SHIPPED_BINS, {"pct": 29, "n": 447}, 90)
    assert v["text"].startswith("33% Green Zone — no comparable previous window. ")
    assert v["direction"] == "unknown" and v["deltaPts"] is None


def test_verdict_calls_a_small_move_flat():
    v = verdict_line(_h(delta=2), SHIPPED_BINS, {"pct": 29, "n": 447}, 90)
    assert "— flat vs the previous 3 mo." in v["text"]
    assert v["direction"] == "flat"


def test_verdict_with_too_few_rated_bins():
    bins = [_b(60, 80, 43, 42), _b(80, 100, 37, 4, provisional=True),
            _b(100, 125, None, 0, provisional=True)]
    v = verdict_line(_h(), bins, {"pct": 29, "n": 42}, 90)
    assert v["text"].endswith("Too few rated bins to call a strong or weak range yet.")
    assert v["solid"] is None and v["weak"] is None


def test_verdict_with_only_one_kind_of_run_has_no_dangling_punctuation():
    bins = [_b(60, 80, 43, 42), _b(80, 100, 41, 51), _b(100, 125, 39, 80)]
    v = verdict_line(_h(), bins, {"pct": 29, "n": 173}, 90)
    assert v["text"].endswith("Strongest 60–125y at 39–43%.")
    assert ";" not in v["text"] and v["weak"] is None


# ------------------------------------------------------------------ the fixture round
# Hole 1: 312y tee shot -> 126y approach to the green (6.8y leave), 2 putts, 5 strokes.
# Hole 2: 117y tee shot to the green (8.7y leave), 2 putts, 4 strokes. Both approaches
# are in the band; the tee shot on hole 1 is not.

FIXTURE_AS_OF = date(2026, 6, 16)          # the fixture round is dated 2026-06-15


def _fixture_doc(con, **over):
    from src.ladder import build
    return build(write=False, as_of=FIXTURE_AS_OF, cfg=over or None, con=con)


def test_fixture_ladder_population(ingested_db):
    doc = _fixture_doc(ingested_db)
    assert doc["coverage"]["approaches"] == 2          # the 312y tee shot is out of band
    assert doc["headline"]["zone"] == {"pct": 100, "n": 2}
    rated = {b["key"]: b["zone"]["n"] for b in doc["bins"] if b["zone"]["n"]}
    assert rated == {"100-125": 1, "125-150": 1}
    detail = {d["key"] for b in doc["bins"] for d in b["detail"] if d["zone"]["n"]}
    assert detail == {"110-120", "120-130"}
    assert all(b["provisional"] for b in doc["bins"])  # every bin is under minBinN
    assert doc["coverage"]["pinCoverage"] == {"pct": 100, "n": 2}


def test_fixture_anchors_and_club_rows(ingested_db):
    doc = _fixture_doc(ingested_db)
    anchors = {c["key"]: c for c in doc["payoffAnchors"]["classes"]}
    # Both approaches finished on the green; strokes to finish = 5-2 and 4-1... the
    # authoritative scorecard leaves 3 strokes after each.
    assert anchors["greenPutted"]["strokes"] == 3.0
    assert anchors["greenPutted"]["n"] == 2
    assert anchors["greenPutted"]["provisional"] is True      # under minAnchorN
    assert anchors["long"]["strokes"] is None and anchors["long"]["n"] == 0
    assert doc["payoffAnchors"]["excludedOverRecorded"] == 0
    # Both fixture clubs are unmapped (club_type 12) and below the per-club floor.
    assert all(b["clubs"] == [] for b in doc["bins"])
    assert sum(b["clubsBelowMin"]["shots"] for b in doc["bins"]) == 2


def test_fixture_out_of_band_shot_is_absent(ingested_db):
    doc = _fixture_doc(ingested_db)
    assert all(r is not None for r in [doc["headline"]["zone"]["n"]])
    binned = sum(b["zone"]["n"] for b in doc["bins"])
    assert binned == 2                     # the 312y stroke lands in no bin at all


def test_fixture_verdict_degrades_when_the_window_is_empty(ingested_db):
    """The n=0 case is the one the fixture can reach: no approaches, no sentence to
    build, and no ranges invented out of nothing."""
    from src.ladder import build
    doc = build(write=False, as_of=date(2026, 9, 19), con=ingested_db)
    assert doc["verdict"]["text"].startswith("Not enough measured approaches")
    assert doc["verdict"]["solid"] is None and doc["verdict"]["weak"] is None
    assert doc["ladderZone"] == {"pct": None, "n": 0}
    assert render_markdown(doc).splitlines()[0] == doc["verdict"]["text"]


def test_fixture_markdown_never_prints_the_headline_under_the_table_scope(ingested_db):
    """The table scope (bandYds) and the headline scope (headlineBandYds) are different
    populations; the export must never label one with the other."""
    doc = _fixture_doc(ingested_db)
    lines = render_markdown(doc).splitlines()
    assert lines[0] == doc["verdict"]["text"]
    assert lines[1].startswith(f"Green Zone % — {doc['headline']['band']['label']} · ")
    assert f"n={doc['headline']['zone']['n']}:" in lines[1]
    assert doc["scope"].startswith(doc["band"]["label"])


def test_fixture_layup_leaves_the_ladder_and_is_counted(ingested_db):
    """A layup was the right play; scoring it against the Green Zone reads it as a
    failure. It leaves the population and shows up in its own coverage count."""
    ingested_db.execute("UPDATE canon.shot SET shot_type = 'LAYUP' "
                        "WHERE shot_id = 90000000005")
    doc = _fixture_doc(ingested_db)
    assert doc["coverage"]["excludedLayup"] == 1
    assert doc["coverage"]["excludedTeeShot"] == 0
    assert doc["coverage"]["approaches"] == 1


def test_teebox_artifact_is_excluded_and_counted(ingested_db):
    # Re-point the hole-2 approach at a tee box: the next-tee GPS artifact shot_flags
    # does not catch. It must leave the ladder and show up in the coverage badge.
    ingested_db.execute("UPDATE canon.shot SET end_lie = 'TeeBox' "
                        "WHERE shot_id = 90000000005")
    doc = _fixture_doc(ingested_db)
    assert doc["coverage"]["eligible"] == 2
    assert doc["coverage"]["excludedTeeBoxArtifact"] == 1
    assert doc["coverage"]["approaches"] == 1
    assert sum(b["zone"]["n"] for b in doc["bins"]) == 1


def test_window_scopes_every_stat(ingested_db):
    from src.ladder import build
    doc = build(write=False, as_of=date(2026, 9, 19), con=ingested_db)
    assert doc["coverage"]["approaches"] == 0      # fixture round is ~96 days back
    assert doc["headline"]["zone"] == {"pct": None, "n": 0}
    wide = build(write=False, as_of=date(2026, 9, 19), cfg={"windowDays": 3650},
                 con=ingested_db)
    assert wide["coverage"]["approaches"] == 2


def test_round_samples_marks_untested_bins(ingested_db):
    from src.ladder import render_round_samples, round_samples
    s = round_samples(ingested_db, 999000111)
    filled = {k: v for k, v in s["bins"].items() if v}
    assert set(filled) == {"100-125", "125-150"}
    assert s["zone"] == {"pct": 100, "n": 2}
    txt = render_round_samples(s)
    assert txt.count("bin untested") == len(s["bins"]) - 2
    assert "ZONE" in txt


# ------------------------------------------------------------------- structural rules

def _walk(node, path="doc"):
    if isinstance(node, dict):
        yield path, node
        for k, v in node.items():
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk(v, f"{path}[{i}]")


def test_no_bare_rates_anywhere_in_the_document(ingested_db):
    """The coverage mechanism is a SHAPE, not a convention: any dict that publishes a
    percentage publishes the n it came from, so no consumer can render one without it."""
    doc = _fixture_doc(ingested_db)
    for path, node in _walk(doc):
        pcts = [k for k in node if k == "pct" or k.endswith("Pct")]
        if pcts:
            assert "n" in node, f"{path} publishes {pcts} with no n"


def test_the_headline_band_closes_on_a_display_edge():
    """The headline is exactly the sum of the display bins below its top edge. If that
    edge ever drifts off the grid, the tile and the table stop agreeing."""
    from src.config import approach_ladder
    cfg = approach_ladder()
    assert cfg["headlineBandYds"][1] in cfg["displayBinEdges"]
    assert cfg["headlineBandYds"][0] == cfg["bandYds"][0]
    assert cfg["detailMaxYds"] in cfg["displayBinEdges"]


def test_the_metric_is_never_called_gir(ingested_db):
    """Garmin's GIR stat is separate and unchanged; this feature never borrows the name
    (ADR #19) — not in the module, not in the document."""
    import re

    import src.ladder as ladder_mod
    src = Path(ladder_mod.__file__).read_text()
    assert not re.search(r"\bGIR\b", src)
    doc = json.dumps(_fixture_doc(ingested_db))
    assert not re.search(r"\bGIR\b", doc)
    # ...and not in the new card either. Scoped to the NEW markup/JS: Garmin's GIR row
    # elsewhere on the dashboard is untouched and must stay.
    site = Path("src/site.py").read_text()
    card = site[site.index('<div class="card" id="ladcard">'):
                site.index('<div class="card"><h2>What changed')]
    js = site[site.index("/* ---- Approach Ladder"):site.index("function drawCone(I){")]
    band = site[site.index("function renderGreenZoneBand"):site.index("function drawBars(")]
    assert not re.search(r"\bGIR\b", card + js + band)


def _ladder_js() -> str:
    """The card's pure render helpers, sliced out of src/site.py so node can run the
    real ones rather than a copy that could drift."""
    site = Path("src/site.py").read_text()
    return site[site.index("const LAD_RAMP="):site.index("let ladOpen=null;")]


def test_the_card_never_renders_new_js_outside_the_gir_guard():
    """The guard above slices site.py on exact anchors. Anything placed outside them is
    silently unchecked — so the card's render functions must sit inside the slice."""
    site = Path("src/site.py").read_text()
    js = site[site.index("/* ---- Approach Ladder"):site.index("function drawCone(I){")]
    for fn in ("function ladState(", "function ladPill(", "function renderLadTable(",
               "function renderLadVerdict(", "function renderLadChip(",
               "function renderLadAnat("):
        assert fn in js, f"{fn} escaped the guarded region"


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_a_bin_reads_as_one_of_exactly_three_states():
    """A real 0% at n=13 (the 190-200 detail bin) is a CONFIDENT zero at the red end of
    the ramp. It must not look like "too few to rate", and neither must look like a bin
    nobody has played. Three states, three distinct renders — pinned here because the
    only thing standing between them is a boolean."""
    probe = _ladder_js() + """
const zero={key:"190-200",label:"190\u2013200y",loYds:190,hiYds:200,
            zone:{pct:0,n:13},provisional:false,medianLeaveYds:60.0};
const thin={key:"200-250",label:"200\u2013250y",loYds:200,hiYds:250,
            zone:{pct:33,n:3},provisional:true,medianLeaveYds:60.0};
const none={key:"250-300",label:"250\u2013300y",loYds:250,hiYds:300,
            zone:{pct:null,n:0},provisional:true,medianLeaveYds:null};
console.log(JSON.stringify({
  states:[ladState(zero),ladState(thin),ladState(none)],
  pills:[ladPill(zero),ladPill(thin),ladPill(none)],
  cells:[ladCell(zero),ladCell(thin),ladCell(none)],
  redEnd:ladColor(0), greenEnd:ladColor(43)}));
"""
    out = json.loads(subprocess.run(["node", "-e", probe], capture_output=True,
                                    text=True, check=True).stdout)
    assert out["states"] == ["rate", "thin", "none"]
    zero_pill, thin_pill, none_pill = out["pills"]
    # The real zero is tinted and prints a number; the other two do neither.
    assert f'background:{out["redEnd"]}' in zero_pill and ">0%<" in zero_pill
    assert "zpill thin" in thin_pill and "too few to rate" in thin_pill
    assert "zpill none" in none_pill and "no shots" in none_pill
    assert len({zero_pill, thin_pill, none_pill}) == 3
    zero_cell, thin_cell, none_cell = out["cells"]
    assert "ladcell thin" not in zero_cell and "ladcell none" not in zero_cell
    assert "background:" in zero_cell and "background:" not in none_cell
    assert out["redEnd"] != out["greenEnd"]


def test_coach_prompt_carries_the_ladder_slot():
    """The coach gets the ladder as a deterministic block, and is told never to call it
    GIR. No LLM call is involved in checking this."""
    from src import coach
    assert "{benchmark}{ladder}" in coach.PROMPT
    assert "APPROACH LADDER" in coach.SYSTEM
    assert "NEVER call this GIR" in coach.SYSTEM
    assert coach._ladder_block.__doc__            # the block exists and is documented


# ----------------------------------------------------------------------- real data

@pytest.mark.skipif(not Path("data/turn.duckdb").exists(),
                    reason="no database — run `python -m src.db rebuild` first")
def test_build_against_real_data():
    from src.ladder import build
    doc = build(write=False)
    cfg = doc["config"]
    assert len(doc["bins"]) == len(cfg["displayBinEdges"]) - 1 == 7
    # The 10y grid stops at detailMaxYds; the display bins above it carry none.
    assert sum(len(b["detail"]) for b in doc["bins"]) == 14
    assert doc["bins"][-1]["detail"] == []
    assert doc["ladderZone"]["n"] == doc["coverage"]["approaches"]
    assert doc["ladderZone"]["n"] > doc["headline"]["zone"]["n"]
    assert doc["coverage"]["scopeChip"].startswith("real pins · ")
    assert 300 <= doc["headline"]["zone"]["n"] <= 450
    assert 0 <= doc["headline"]["zone"]["pct"] <= 100
    assert (doc["coverage"]["approaches"] + doc["coverage"]["excludedTeeBoxArtifact"]
            + doc["coverage"]["excludedLayup"] + doc["coverage"]["excludedTeeShot"]
            == doc["coverage"]["eligible"])
    assert doc["coverage"]["pinCoverage"]["pct"] == 100
    anchors = {c["key"]: c["strokes"] for c in doc["payoffAnchors"]["classes"]}
    assert set(anchors) == set(LEAVE_CLASSES)
    assert all(v is not None for v in anchors.values())
    # Leaving it closer costs fewer strokes to finish — the whole point of the zone.
    assert anchors["greenPutted"] < anchors["pitch"] < anchors["long"]


@pytest.mark.skipif(not Path("data/turn.duckdb").exists(),
                    reason="no database — run `python -m src.db rebuild` first")
def test_preserved_findings_reproduce_in_shape():
    """The spec's three findings are ACCEPTANCE EVIDENCE for the generators: assert the
    shape and the direction, never the exact percentages (the window moves)."""
    from src.ladder import build
    doc = build(write=False)
    found = {f["key"] for f in doc["findings"]}
    assert {"reach-swing", "cliff", "best-window"} <= found
    reach = [f for f in doc["findings"] if f["key"] == "reach-swing"]
    assert all(f["club"] and f["n"] >= doc["config"]["minClubRowN"] for f in reach)
    cliff = next(f for f in doc["findings"] if f["key"] == "cliff")
    assert cliff["binKey"] == "150-170"          # the cliff starts at 150, not 160
    best = next(f for f in doc["findings"] if f["key"] == "best-window")
    assert best["binKey"] == "100-110"           # 100y is still his best window
    assert all(0 < f["magnitude"] for f in doc["findings"])


def test_delta_pts_rounds_once_from_exact_rates():
    # The crew's own catch on v1.1: 33.6% vs 25.4% is a true move of +8.2 -> +8,
    # but round-then-subtract reads 34 - 25 = +9. Delta must round ONCE.
    from src.ladder import _delta_pts
    cur = [{"zone": True}] * 42 + [{"zone": False}] * 83      # 33.6%
    prev = [{"zone": True}] * 32 + [{"zone": False}] * 94     # 25.4%
    assert _delta_pts(cur, prev, lambda r: r["zone"]) == 8
    assert _delta_pts(cur, [], lambda r: r["zone"]) is None
    assert _delta_pts([{"zone": None}], prev, lambda r: r["zone"]) is None
