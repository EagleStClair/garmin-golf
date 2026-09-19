"""Approach Ladder & Green Zone — how good is the approach game, by yardage.

Deterministic (no LLM). One row per approach in the window (a real stroke whose
distance-to-pin falls in the band and that was actually aimed at the green), binned by
yardage and scored against the Green Zone:

    Green Zone = the approach finished on the green, OR inside the zone radius of the
                 pin, OR in the hole.

Geometric and pin-centred. This is NOT Garmin's green-in-regulation stat — that one is
unchanged everywhere it already appears and is reported separately (ADR #19).

Two bands, deliberately: `bandYds` is what the table DISPLAYS (60-250y), while
`headlineBandYds` (60-170y) is what the priority metric, its trend and the payoff
anchors are computed on. Extending the display must never re-base a shipped metric, and
the leave-class prices the short bins are read against cannot be estimated on a
population whose median leave is 48-66 yards.

Row-level facts come from `derived.shot_play` (threshold-free by design); every cut —
window, bands, bin edges, zone radius, rings, leave classes, exclusions, coverage
floors — lives in config/analysis.json -> approachLadder and is read once, here, then
passed down as a `cfg` dict. Nothing re-reads config inside a helper.

    python -m src.ladder

Output: data/processed/approach_ladder.{json,md}. The md is what the coach prompt
ingests; the json is inlined into the site and feeds insight candidates.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from .config import approach_ladder as _ladder_cfg
from .constants import LEAVE_CLASS_LABELS, LEAVE_CLASSES, PUTTER_CLUB_TYPE_ID

OUT_JSON = Path("data/processed/approach_ladder.json")
OUT_MD = Path("data/processed/approach_ladder.md")

SCHEMA = 2
FLAT_BAND_PTS = 2         # |delta| at or below this reads as flat, not a real move


# --------------------------------------------------------------------------- pure fns
# Everything below is DB-free and unit-tested: the bin/zone/leave vocabulary the whole
# feature speaks, with the config values passed in rather than read.

def in_band(to_pin_yds: float | None, band: list) -> bool:
    """Is this stroke an approach? Inclusive at both ends of the band."""
    return to_pin_yds is not None and band[0] <= to_pin_yds <= band[1]


def display_bin(to_pin_yds: float | None, edges: list) -> str | None:
    """Coarse bin key ("100-125"). Half-open [lo, hi) per bin; the final bin is closed
    so an exact 170.0 is never dropped."""
    if to_pin_yds is None:
        return None
    for i, (lo, hi) in enumerate(zip(edges, edges[1:])):
        last = i == len(edges) - 2
        if lo <= to_pin_yds < hi or (last and to_pin_yds == hi):
            return f"{lo}-{hi}"
    return None


def detail_bin(to_pin_yds: float | None, width: int, band: list) -> str | None:
    """Fine bin key ("110-120") at the detail width, same closed-at-the-top rule."""
    if not in_band(to_pin_yds, band):
        return None
    lo = band[0] + int((to_pin_yds - band[0]) // width) * width
    lo = min(lo, band[1] - width)          # the closing edge belongs to the last bin
    return f"{lo}-{lo + width}"


def exclusion(end_lie: str | None, start_lie: str | None, par: int | None,
              shot_type: str | None, cfg: dict) -> str | None:
    """Why an in-band stroke is not an approach, or None when it counts.

    Three reasons, in the order they are counted. A tee-box FINISH is a next-tee GPS
    artifact `shot_flags` does not catch. A layup and a tee shot on a par above 3 were
    never attempting the green, so scoring them against the Green Zone reads the right
    play as a failure (ADR #19 v1.1) — a par-3 tee shot IS an approach and stays in.
    Start lie and end lie are separate rules here and must not be conflated."""
    if end_lie in set(cfg["excludeEndLie"]):
        return "teeBoxArtifact"
    if shot_type in set(cfg["excludeShotTypes"]):
        return "layup"
    if start_lie == "TeeBox" and par is not None and par > cfg["excludeTeeShotsAbovePar"]:
        return "teeShot"
    return None


def in_zone(end_lie: str | None, leave_yds: float | None, holed: bool,
            zone_radius_yds: float) -> bool | None:
    """The locked definition, verbatim: on the green, or inside the radius, or holed.
    None means unmeasurable (no leave, not green, not holed) — those count in coverage
    but never in the rate."""
    if end_lie == "Green" or holed:
        return True
    if leave_yds is None:
        return None
    return leave_yds <= zone_radius_yds


def in_ring(leave_yds: float | None, radius_yds: float) -> bool | None:
    """Rings are pin-centred and need a measured leave — a 'Green' end lie alone does
    not satisfy one (green centre is not the pin)."""
    return None if leave_yds is None else leave_yds <= radius_yds


def putter_next(next_club_type_id: int | None) -> bool | None:
    """Did he putt next? Keyed on CLUB, because Garmin marks shot_type='PUTT' only from
    the green — fringe putts read as chips. DIAGNOSTIC ONLY: never inside in_zone.
    None = the hole ended, or the next stroke's club is unattributed (club_type_id 0)."""
    if not next_club_type_id:
        return None
    return next_club_type_id == PUTTER_CLUB_TYPE_ID


def leave_class(end_lie: str | None, leave_yds: float | None, putter_next_flag: bool | None,
                edges: list, holed: bool = False) -> str | None:
    """Where the approach left him, in the vocabulary the payoff anchors price. A holed
    approach has nothing left to finish, so it classes as None and is counted apart."""
    if holed:
        return None
    if putter_next_flag and end_lie == "Green":
        return "greenPutted"
    if putter_next_flag:
        return "fringePutted"              # putter off the green: fringe/apron
    if end_lie == "Green":
        return "greenPutted"               # green, next club unattributed or a non-putt
    if leave_yds is None:
        return None
    if leave_yds <= edges[0]:
        return "chipped"
    return "pitch" if leave_yds <= edges[1] else "long"


def stat(hits: int, n: int) -> dict:
    """The coverage primitive. EVERY rate in this export goes through it, so a consumer
    physically cannot render a percentage without its n in hand."""
    return {"pct": round(100 * hits / n) if n else None, "n": n}


def window_label(days: int) -> str:
    if days == 30:
        return "last month"
    if days >= 60 and days % 30 == 0:
        return f"last {days // 30} mo"
    return f"last {days} days"


def _detail_band(cfg: dict) -> list:
    """The 10-yard grid runs from the band floor to detailMaxYds, not to the top of the
    display band: past 200y the grid is thinner than it is informative, so those display
    bins carry no detail at all."""
    return [cfg["bandYds"][0], cfg["detailMaxYds"]]


def scope_label(band: list, days: int) -> str:
    return f"{band[0]}–{band[1]}y · {window_label(days)}"


def scope_suffix(band: list, days: int, n: int) -> str:
    return f"{scope_label(band, days)} · n={n}"


# ---------------------------------------------------------------------------- dataset

# shot_play is threshold-free and deliberately does not project Garmin's own
# shot_type; the layup exclusion needs it, so it is joined back from canon here rather
# than widening the view (the view serves more than this feature).
_ROW_SQL = """
SELECT sp.shot_id, sp.round_id, sp.round_date, sp.hole_number, sp.par, sp.play_order,
       sp.club_id, sp.club_type_id, sp.club_name, sp.start_lie, sp.end_lie,
       sp.to_pin_yds, sp.leave_yds, sp.miss_range, sp.miss_side,
       sp.next_club_type_id, sp.hole_strokes, sp.hole_putts, sp.strokes_to_finish,
       sp.holed, s.shot_type
FROM derived.shot_play sp JOIN canon.shot s USING (shot_id)
WHERE sp.round_date >= ? AND sp.round_date <= ? AND sp.to_pin_yds IS NOT NULL
ORDER BY sp.round_date, sp.hole_number, sp.play_order"""

TO_PIN_COL = 11          # _ROW_SQL ordinal of to_pin_yds, for the pre-_row band filter


def _club_name(name: str | None) -> str | None:
    """A real club name, or None when Garmin logged no sensor for the swing. Those
    shots still count in every bin total — only the per-club rows lose them."""
    if not name or name.lower().startswith("unknown"):
        return None
    return name


def _row(r: tuple, cfg: dict) -> dict:
    """One approach, with every config cut already applied to it."""
    (shot_id, round_id, round_date, hole, par, play_order, club_id, club_type_id,
     club_name, start_lie, end_lie, to_pin, leave, miss_range, miss_side,
     next_club_type_id, hole_strokes, hole_putts, stf, holed, shot_type) = r
    holed = bool(holed)
    pn = putter_next(next_club_type_id)
    return {
        "shotId": shot_id, "roundId": round_id, "date": str(round_date), "hole": hole,
        "par": par, "playOrder": play_order, "club": _club_name(club_name),
        "clubTypeId": club_type_id, "startLie": start_lie, "endLie": end_lie,
        "shotType": shot_type,
        "toPin": to_pin, "leave": leave, "missRange": miss_range, "missSide": miss_side,
        "nextClubTypeId": next_club_type_id, "strokesToFinish": stf, "holed": holed,
        "displayBin": display_bin(to_pin, cfg["displayBinEdges"]),
        "detailBin": detail_bin(to_pin, cfg["detailBinWidthYds"], _detail_band(cfg)),
        "zone": in_zone(end_lie, leave, holed, cfg["zoneRadiusYds"]),
        "rings": {f"ring{int(r_)}": in_ring(leave, r_) for r_ in cfg["ringYds"]},
        "putterNext": pn,
        "leaveClass": leave_class(end_lie, leave, pn, cfg["leaveClassEdgesYds"], holed),
    }


def load_rows(con, cfg: dict, as_of: date, days: int | None = None) -> dict:
    """The windowed, band-filtered, artifact-excluded approach population.

    The band filter and the exclusions live here rather than in the view: the view
    stays threshold-free, and keeping the lies, the par and the shot type on the row
    makes each drop auditable — excluded strokes are counted by reason, not quietly
    missing. One rule across the whole band: the split predicate the 170-250 extension
    seemed to want costs exactly one shot inside 60-170, which is no discontinuity."""
    days = cfg["windowDays"] if days is None else days
    start = as_of - timedelta(days=days)
    rows = con.execute(_ROW_SQL, [start, as_of]).fetchall()
    band = cfg["bandYds"]
    eligible = [_row(r, cfg) for r in rows if in_band(r[TO_PIN_COL], band)]
    excluded = {"teeBoxArtifact": 0, "layup": 0, "teeShot": 0}
    kept = []
    for r in eligible:
        why = exclusion(r["endLie"], r["startLie"], r["par"], r["shotType"], cfg)
        if why:
            excluded[why] += 1
        else:
            kept.append(r)
    return {"rows": kept, "eligible": len(eligible), "excluded": excluded,
            "from": start.isoformat(), "to": as_of.isoformat(), "days": days}


def _median(vals: list) -> float | None:
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return None
    mid = len(vals) // 2
    return vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2


def _rate(rows: list, pred) -> dict:
    """A rate over the rows where the predicate is measurable (None = unmeasurable and
    excluded from the denominator, never counted as a miss)."""
    vals = [pred(r) for r in rows]
    known = [v for v in vals if v is not None]
    return stat(sum(1 for v in known if v), len(known))


def _miss(rows: list) -> dict:
    """Short/long and left/right/straight shares for a slice, each over the rows that
    carry the reading."""
    rng = [r["missRange"] for r in rows if r["missRange"]]
    side = [r["missSide"] for r in rows if r["missSide"]]
    d = {"n": len(rows)}
    for key, vals, want in (("shortPct", rng, "short"), ("longPct", rng, "long"),
                            ("leftPct", side, "left"), ("rightPct", side, "right"),
                            ("straightPct", side, "straight")):
        d[key] = round(100 * sum(1 for v in vals if v == want) / len(vals)) if vals else None
    return d


def payoff_anchors(rows: list, cfg: dict) -> dict:
    """Average strokes to hole out after an approach, by where it left the ball.

    Strokes to finish is the authoritative hole score minus the stroke's ordinal, never
    a count of remaining shot rows — the shot layer under-records tap-ins and penalties,
    which would price every leave class too cheaply."""
    over_recorded = sum(1 for r in rows if r["strokesToFinish"] is not None
                        and r["strokesToFinish"] < 0)
    by_class: dict[str, list] = {k: [] for k in LEAVE_CLASSES}
    for r in rows:
        stf = r["strokesToFinish"]
        if r["leaveClass"] in by_class and stf is not None and stf >= 0:
            by_class[r["leaveClass"]].append(stf)
    classes = []
    for key in LEAVE_CLASSES:
        vals = by_class[key]
        classes.append({
            "key": key, "label": LEAVE_CLASS_LABELS[key],
            "strokes": round(sum(vals) / len(vals), 2) if vals else None,
            "n": len(vals), "provisional": len(vals) < cfg["minAnchorN"]})
    legend = "Miss the zone and it costs you: " + " · ".join(
        f"{c['label'].lower()} {c['strokes']:.2f} strokes to hole out"
        if c["key"] == LEAVE_CLASSES[0] else f"{c['label'].lower()} {c['strokes']:.2f}"
        for c in classes if c["strokes"] is not None)
    return {
        "basis": "average strokes to hole out after an approach in the band, by where it "
                 "left the ball; strokes counted from the authoritative scorecard, never "
                 "from shot rows",
        "classes": classes, "excludedOverRecorded": over_recorded, "legend": legend}


def _anchor_map(anchors: dict) -> dict:
    return {c["key"]: c["strokes"] for c in anchors["classes"] if c["strokes"] is not None}


def _payoff(rows: list, amap: dict, min_n: int) -> dict | None:
    """What an approach from this slice costs, on average, by pricing each leave."""
    vals = [amap[r["leaveClass"]] for r in rows if r["leaveClass"] in amap]
    if len(vals) < min_n:
        return None
    return {"strokes": round(sum(vals) / len(vals), 2), "n": len(vals)}


def _club_rows(rows: list, cfg: dict) -> tuple[list, dict]:
    """Per-club rows at or above the floor, plus the shots that did not make one —
    unattributed swings and thin clubs still count in the bin, they just cannot be
    rated on their own."""
    groups: dict[str, list] = {}
    for r in rows:
        if r["club"]:
            groups.setdefault(r["club"], []).append(r)
    out, below = [], len([r for r in rows if not r["club"]])
    for club, rs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        if len(rs) < cfg["minClubRowN"]:
            below += len(rs)
            continue
        out.append({"club": club, "clubTypeId": rs[0]["clubTypeId"],
                    "zone": _rate(rs, lambda r: r["zone"]),
                    "medianLeaveYds": round(_median([r["leave"] for r in rs]), 1)
                    if _median([r["leave"] for r in rs]) is not None else None,
                    "miss": _miss(rs)})
    return out, {"shots": below, "minN": cfg["minClubRowN"]}


def _bin_doc(key: str, lo: float, hi: float, rows: list, cfg: dict, amap: dict,
             detail: list | None = None) -> dict:
    ring_keys = [f"ring{int(r_)}" for r_ in cfg["ringYds"]]
    clubs, below = _club_rows(rows, cfg)
    lies: dict[str, list] = {}
    for r in rows:
        lies.setdefault(r["startLie"] or "Unknown", []).append(r)
    doc = {
        "key": key, "label": f"{lo:g}–{hi:g}y", "loYds": lo, "hiYds": hi,
        "zone": _rate(rows, lambda r: r["zone"]),
        "medianLeaveYds": round(_median([r["leave"] for r in rows]), 1) if rows else None,
        "payoffStrokes": _payoff(rows, amap, cfg["minBinN"]),
        "provisional": len(rows) < cfg["minBinN"],
        "miss": _miss(rows),
        "fromLie": [{"lie": lie, "zone": _rate(rs, lambda r: r["zone"])}
                    for lie, rs in sorted(lies.items(), key=lambda kv: -len(kv[1]))],
        "clubs": clubs, "clubsBelowMin": below,
    }
    for rk in ring_keys:
        doc[rk] = _rate(rows, lambda r, rk=rk: r["rings"][rk])
    if detail is not None:
        doc["detail"] = detail
    return doc


def _detail_bins(rows: list, cfg: dict, amap: dict) -> list:
    """The 10-yard grid across the detail band. It is a BAND grid, not a per-display-bin
    one: a display edge like 125 falls mid-grid, so each detail bin is filed under the
    display bin its lower edge sits in and keeps its own (grid-aligned) rows. Display
    bins above detailMaxYds simply find no grid bins and carry an empty detail list."""
    width, (lo0, hi0) = cfg["detailBinWidthYds"], _detail_band(cfg)
    out, edge = [], lo0
    while edge < hi0:
        key = f"{edge:g}-{edge + width:g}"
        rs = [r for r in rows if r["detailBin"] == key]
        out.append(_bin_doc(key, edge, edge + width, rs, cfg, amap))
        edge += width
    return out


def _verdict(delta: float | None) -> str:
    if delta is None:
        return "unknown"
    if abs(delta) <= FLAT_BAND_PTS:
        return "flat"
    return "improving" if delta > 0 else "slipping"


def trust_chip(coverage: dict) -> str:
    """The data-honesty label the card wears: what these numbers are actually made of.
    Published as a string so the card renders it and never re-assembles it in JS."""
    # Pin-centred rings need real pin coordinates. A connector that has none would
    # return "green-hit only · no pin data" here instead (vNext2 capability flags).
    source = "real pins"
    return (f"{source} · {coverage['pinCoverage']['pct']}% of holes · "
            f"n={coverage['approaches']} · {coverage['rounds']} rounds")


def _run_doc(run: list) -> dict:
    """A contiguous stretch of display bins, described by its outer edges."""
    pcts = [b["zone"]["pct"] for b in run]
    return {"label": f"{run[0]['loYds']:g}–{run[-1]['hiYds']:g}y",
            "loYds": run[0]["loYds"], "hiYds": run[-1]["hiYds"],
            "minPct": min(pcts), "maxPct": max(pcts),
            "n": sum(b["zone"]["n"] for b in run), "bins": [b["key"] for b in run]}


def _longest_run(bins: list, kinds: list, want: str) -> list:
    """The longest contiguous run of one kind, in display order. An unrated or
    provisional bin BREAKS contiguity — a range with a hole in the evidence is not a
    range. Ties go to the lower-yardage run, which is the one he plays more often."""
    best, cur = [], []
    for b, kind in zip(bins, kinds):
        cur = cur + [b] if kind == want else []
        if len(cur) > len(best):
            best = cur
    return best


def _range_text(run_doc: dict) -> str:
    """A run's percentage range, collapsed to one number when it is a single bin."""
    lo, hi = run_doc["minPct"], run_doc["maxPct"]
    return f"{lo}%" if lo == hi else f"{lo}–{hi}%"


def verdict_line(headline: dict, bins: list, ladder_zone: dict, days: int) -> dict:
    """The reading, before any table: rate, trend, and the stretches that hold and fail.

    A computed template, never an LLM and never re-templated in JS — `text` is the
    single source of truth that the card and the markdown export both print verbatim."""
    gz, n, delta = headline["zone"]["pct"], headline["zone"]["n"], headline["deltaPts"]
    if gz is None:
        return {"text": f"Not enough measured approaches in the {window_label(days)} to "
                        f"rate the approach game (n={n}).",
                "gzPct": None, "n": n, "deltaPts": None, "direction": "unknown",
                "solid": None, "weak": None}
    moved = _verdict(delta)
    direction = {"improving": "up", "slipping": "down"}.get(moved, moved)
    if direction == "unknown":
        trend = "no comparable previous window"
    elif direction == "flat":
        trend = f"flat vs the {headline['prev']['label']}"
    else:
        trend = f"{direction} {abs(delta)} pts vs the {headline['prev']['label']}"

    # Solid vs weak splits on the LADDER rate, not the headline one: the table now runs
    # past the headline band, so the comparison has to stay inside a single scope.
    pivot = ladder_zone["pct"]
    kinds = [None if b["provisional"] or b["zone"]["pct"] is None
             else ("solid" if b["zone"]["pct"] >= pivot else "weak") for b in bins]
    runs = [(word, _run_doc(run))
            for word, run in (("Strongest", _longest_run(bins, kinds, "solid")),
                              ("Weakest", _longest_run(bins, kinds, "weak"))) if run]
    rated = [k for k in kinds if k]
    base = {"gzPct": gz, "n": n, "deltaPts": delta, "direction": direction}
    if len(rated) < 2 or not runs:
        return {"text": f"{gz}% Green Zone — {trend}. Too few rated bins to call a "
                        "strong or weak range yet.", **base, "solid": None, "weak": None}
    clauses = "; ".join(f"{word if i == 0 else word.lower()} {d['label']} "
                        f"at {_range_text(d)}" for i, (word, d) in enumerate(runs))
    by_word = {word: d for word, d in runs}
    return {"text": f"{gz}% Green Zone — {trend}. {clauses}.", **base,
            "solid": by_word.get("Strongest"), "weak": by_word.get("Weakest")}


def _coverage(con, cfg: dict, win: dict, rows: list) -> dict:
    n_rounds, holes, with_pin = con.execute("""
        SELECT count(DISTINCT round_id), count(*), count(*) FILTER (WHERE has_pin)
        FROM derived.hole_pin_coverage WHERE round_date >= ? AND round_date <= ?""",
        [win["from"], win["to"]]).fetchone()
    n, dropped = len(rows), win["excluded"]
    cov = {
        "rounds": n_rounds, "holes": holes, "holesWithPin": with_pin,
        "holesWithoutPin": holes - with_pin, "pinCoverage": stat(with_pin, holes),
        "eligible": win["eligible"],
        "excludedTeeBoxArtifact": dropped["teeBoxArtifact"],
        "excludedLayup": dropped["layup"], "excludedTeeShot": dropped["teeShot"],
        "approaches": n,
        "leaveMeasured": stat(sum(1 for r in rows if r["leave"] is not None), n),
        "clubAttributed": stat(sum(1 for r in rows if r["club"]), n),
        "nextShotKnown": stat(sum(1 for r in rows if r["putterNext"] is not None), n),
        "note": "Holes without pin coordinates carry no shot data at all, so they "
                "contribute no approaches — they are counted here so the shrunken "
                "denominator stays visible. Approaches recorded as finishing on a tee "
                "box are next-tee GPS artifacts (shot_flags does not catch them) and are "
                "excluded; layups and tee shots on par 4s and 5s are excluded because "
                "they were never attempting the green. Every count is shown so each drop "
                "stays visible.",
    }
    cov["scopeChip"] = trust_chip(cov)
    return cov


def candidate_findings(doc: dict, cfg: dict) -> list:
    """Bin-level findings offered to the insight ranker. Candidates, never a standing
    list — insights.py scores them against everything else and only the winners show."""
    out, band_zone = [], (doc["headline"]["zone"]["pct"] or 0)
    bins, head_band = doc["bins"], doc["headline"]["band"]
    # Reach-swing and best-window read against the HEADLINE band's rate, so they only
    # scan detail bins inside it. Past its top edge every club is a reach swing and the
    # pattern stops meaning anything — those candidates would displace real findings.
    detail = [d for b in bins for d in b["detail"] if d["hiYds"] <= head_band["maxYds"]]

    # 1. Reach swing — a club pushed past its stock max leaks short AND right together.
    for d in detail:
        for c in d["clubs"]:
            m = c["miss"]
            if (m["n"] >= cfg["minClubRowN"] and (m["shortPct"] or 0) >= 65
                    and (m["rightPct"] or 0) >= 55):
                out.append({
                    "cat": "Approach ladder", "key": "reach-swing", "binKey": d["key"],
                    "club": c["club"], "n": m["n"],
                    "magnitude": round((m["shortPct"] + m["rightPct"] - 120) / 60, 3),
                    "weight": 1.15,
                    "text": f"{c['club']} from {d['label']} is a reach swing: of "
                            f"{m['n']} shots, {m['shortPct']}% finish short and "
                            f"{m['rightPct']}% finish right, and only "
                            f"{c['zone']['pct']}% reach the Green Zone. One more club "
                            f"is the whole fix."})

    # 2. The cliff — where the ladder stops holding, at display resolution.
    # The cliff still scans every DISPLAYED bin — it breaks after the first real drop,
    # which is still 150-170, and the long bins are legitimate evidence for it.
    rated = [b for b in bins if not b["provisional"] and b["zone"]["pct"] is not None]
    for lower, upper in zip(rated, rated[1:]):
        drop = lower["zone"]["pct"] - upper["zone"]["pct"]
        if drop >= 12:
            out.append({
                "cat": "Approach ladder", "key": "cliff", "binKey": upper["key"],
                "club": None, "n": upper["zone"]["n"], "magnitude": round(drop / 25, 3),
                "weight": 1.2,
                "text": f"Your approach game falls off a cliff at {upper['loYds']:g} "
                        f"yards: {lower['label']} reaches the Green Zone "
                        f"{lower['zone']['pct']}% of the time (n={lower['zone']['n']}) "
                        f"but {upper['label']} only {upper['zone']['pct']}% "
                        f"(n={upper['zone']['n']}), leaving a median "
                        f"{upper['medianLeaveYds']:.0f} yards. Lay up to the range that "
                        f"still works."})
            break

    # 3. Best window — the yardage worth manufacturing, when it clearly beats the band.
    rated_d = [d for d in detail if not d["provisional"] and d["zone"]["pct"] is not None]
    if rated_d:
        best = max(rated_d, key=lambda d: d["zone"]["pct"])
        edge = best["zone"]["pct"] - band_zone
        if edge >= 12:
            out.append({
                "cat": "Approach ladder", "key": "best-window", "binKey": best["key"],
                "club": None, "n": best["zone"]["n"], "magnitude": round(edge / 25, 3),
                "weight": 1.0,
                "text": f"{best['label']} is your best window: {best['zone']['pct']}% of "
                        f"{best['zone']['n']} approaches reach the Green Zone, against "
                        f"{band_zone}% across the whole {head_band['label']} band. "
                        f"Worth leaving yourself that number off the tee."})
    return out


def build_doc(con, cfg: dict, as_of: date) -> dict:
    win = load_rows(con, cfg, as_of)
    rows = win["rows"]
    prev = load_rows(con, cfg, as_of - timedelta(days=cfg["windowDays"]))
    band, days = cfg["bandYds"], cfg["windowDays"]
    # The priority metric, its trend and the payoff anchors are pinned to the headline
    # band. The table may run past it; a shipped metric must not silently re-base, and
    # a leave-class price has to be estimated where the leaves look like the ones it
    # is used to price (a 200y+ leave is 48-66 yards and would poison "long").
    head_band = cfg["headlineBandYds"]
    head_rows = [r for r in rows if in_band(r["toPin"], head_band)]
    prev_rows = [r for r in prev["rows"] if in_band(r["toPin"], head_band)]
    anchors = payoff_anchors(head_rows, cfg)
    amap = _anchor_map(anchors)
    edges = cfg["displayBinEdges"]

    detail = _detail_bins(rows, cfg, amap)
    bins = []
    for lo, hi in zip(edges, edges[1:]):
        key = f"{lo:g}-{hi:g}"
        rs = [r for r in rows if r["displayBin"] == key]
        bins.append(_bin_doc(key, lo, hi, rs, cfg, amap,
                             detail=[d for d in detail if lo <= d["loYds"] < hi]))

    zone = _rate(head_rows, lambda r: r["zone"])
    prev_zone = _rate(prev_rows, lambda r: r["zone"])
    # Rounded-then-subtracted, as shipped in v1: both operands are already whole points.
    delta = (zone["pct"] - prev_zone["pct"]
             if zone["pct"] is not None and prev_zone["pct"] is not None else None)
    ring0 = f"ring{int(cfg['ringYds'][0])}"
    headline = {
        "key": "greenZonePct", "label": "Green Zone %",
        "scope": scope_label(head_band, days),
        "band": {"minYds": head_band[0], "maxYds": head_band[1],
                 "label": f"{head_band[0]}–{head_band[1]}y"},
        "zone": zone, ring0: _rate(head_rows, lambda r: r["rings"][ring0]),
        "putterNext": {**_rate(head_rows, lambda r: r["putterNext"]), "diagnostic": True},
        "prev": {**prev_zone, "label": f"previous {window_label(days).replace('last ', '')}"},
        "deltaPts": delta, "verdict": _verdict(delta),
        "payoffStrokes": _payoff(head_rows, amap, cfg["minBinN"]),
    }
    ladder_zone = _rate(rows, lambda r: r["zone"])

    doc = {
        "schema": SCHEMA,
        "generatedFor": as_of.isoformat(),
        "window": {"days": days, "from": win["from"], "to": win["to"],
                   "label": window_label(days)},
        "band": {"minYds": band[0], "maxYds": band[1], "label": f"{band[0]}–{band[1]}y"},
        "scope": scope_suffix(band, days, len(rows)),
        "headline": headline,
        # The rate across everything the TABLE shows — the scope the verdict line
        # splits strong from weak on, so the comparison never crosses two populations.
        "ladderZone": ladder_zone,
        "verdict": verdict_line(headline, bins, ladder_zone, days),
        "bins": bins,
        "payoffAnchors": anchors,
        "coverage": _coverage(con, cfg, win, rows),
        "config": cfg,
        "note": "Green Zone means the approach finished on the green, or inside "
                f"{cfg['zoneRadiusYds']:g} yards of the pin, or in the hole — a "
                "geometric, pin-centred measure. It is not Garmin's green-in-regulation "
                "stat, which is unchanged and reported separately. Green Zone % is a "
                "RATE, so it uses every round in the window, 9- and 18-hole alike; only "
                "scoring-level metrics are restricted to 18-hole regulation rounds.",
    }
    doc["findings"] = candidate_findings(doc, cfg)
    return doc


# --------------------------------------------------------------------------- renders

def render_markdown(doc: dict) -> str:
    """The coach-facing render: the season strip with an n on every row, the payoff
    line, the coverage line. Kept short — it shares a prompt with everything else."""
    h, cov = doc["headline"], doc["coverage"]
    d = h["deltaPts"]
    trend = ("no comparable previous window" if d is None else
             f"{d:+d} pts vs the {h['prev']['label']} ({h['prev']['pct']}%, "
             f"n={h['prev']['n']}) — {h['verdict']}")
    # The headline is scoped to ITS band, never to the (wider) table scope — printing a
    # 60-170 number under a 60-250 label is the one mistake this export must not make.
    head_scope = scope_suffix([h["band"]["minYds"], h["band"]["maxYds"]],
                              doc["window"]["days"], h["zone"]["n"])
    lines = [
        doc["verdict"]["text"],
        f"Green Zone % — {head_scope}: {h['zone']['pct']}% ({trend}). The table below "
        f"runs {doc['band']['label']}.",
        "Green Zone = finished on the green, inside "
        f"{doc['config']['zoneRadiusYds']:g} yards of the pin, or holed. NOT Garmin's "
        "green-in-regulation stat.",
        "",
        "| Bin | Green Zone % | n | median leave |",
        "|---|---|---|---|",
    ]
    for b in doc["bins"]:
        pct = "too few to rate" if b["provisional"] or b["zone"]["pct"] is None \
            else f"{b['zone']['pct']}%"
        leave = f"{b['medianLeaveYds']:.1f}y" if b["medianLeaveYds"] is not None else "—"
        lines.append(f"| {b['label']} | {pct} | {b['zone']['n']} | {leave} |")
    lines += ["", doc["payoffAnchors"]["legend"] + " (priced on "
              f"{doc['headline']['band']['label']}).",
              f"Coverage: {cov['scopeChip']}; "
              f"{cov['excludedTeeBoxArtifact']} dropped as next-tee GPS artifacts, "
              f"{cov['excludedLayup']} layups and {cov['excludedTeeShot']} par-4/5 tee "
              f"shots dropped as strokes never attempting the green; "
              f"club named on {cov['clubAttributed']['pct']}%; pin coordinates on "
              f"{cov['pinCoverage']['pct']}% of {cov['holes']} holes."]
    return "\n".join(lines) + "\n"


def round_samples(con, round_id: int, cfg: dict | None = None) -> dict:
    """THIS round's approaches in each display bin — the per-round companion to the
    season strip, so a coach read anchors to real shots or says the bin went untested.
    No window filter: the round is the scope."""
    cfg = cfg or _ladder_cfg()
    rows = con.execute(
        _ROW_SQL.replace("WHERE sp.round_date >= ? AND sp.round_date <= ?",
                         "WHERE sp.round_id = ?"), [round_id]).fetchall()
    band, edges = cfg["bandYds"], cfg["displayBinEdges"]
    eligible = [_row(r, cfg) for r in rows if in_band(r[TO_PIN_COL], band)]
    kept = [r for r in eligible
            if exclusion(r["endLie"], r["startLie"], r["par"], r["shotType"], cfg) is None]
    bins = {f"{lo:g}-{hi:g}": [] for lo, hi in zip(edges, edges[1:])}
    for r in kept:
        if r["displayBin"] in bins:
            bins[r["displayBin"]].append({
                "hole": r["hole"], "fromYds": round(r["toPin"]), "lie": r["startLie"],
                "leaveYds": round(r["leave"], 1) if r["leave"] is not None else None,
                "end": r["endLie"], "zone": r["zone"], "missRange": r["missRange"],
                "missSide": r["missSide"]})
    return {"bins": bins, "zone": _rate(kept, lambda r: r["zone"])}


def render_round_samples(samples: dict) -> str:
    lines = ["THIS ROUND'S APPROACHES BY BIN (the strip above is his SEASON profile — "
             "anchor your read to these shots, or say the bin went untested this round):"]
    for key, shots in samples["bins"].items():
        label = key.replace("-", "–") + "y"
        if not shots:
            lines.append(f"  {label}: none this round — bin untested")
            continue
        parts = []
        for s in shots:
            miss = ", ".join(m for m in (s["missRange"], s["missSide"]) if m
                             and m != "straight")
            verdict = "ZONE" if s["zone"] else f"missed{' — ' + miss if miss else ''}"
            parts.append(f"H{s['hole']} {s['fromYds']:.0f}y ({(s['lie'] or '?').lower()}) "
                         f"-> left {s['leaveYds']:.0f}y, {(s['end'] or '?').lower()} "
                         f"— {verdict}")
        lines.append(f"  {label}: " + "; ".join(parts))
    z = samples["zone"]
    lines.append(f"  Round Green Zone: {z['pct']}% of {z['n']} approaches in the band"
                 if z["n"] else "  Round Green Zone: no approaches in the band")
    return "\n".join(lines)


def build(write: bool = True, as_of: date | None = None, cfg: dict | None = None,
          con=None) -> dict:
    """Build the ladder document. `as_of` and `cfg` are injectable because the window is
    date-relative: tests pin a date so the fixture round stays visible."""
    from .db import connect
    full = dict(_ladder_cfg())
    full.update(cfg or {})
    doc = build_doc(con or connect(), full, as_of or date.today())
    if write:
        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(json.dumps(doc, indent=2))
        OUT_MD.write_text(render_markdown(doc))
        print(f"  approach ladder -> {OUT_MD}")
    return doc


def main() -> None:
    doc = build()
    print(render_markdown(doc))


if __name__ == "__main__":
    main()
