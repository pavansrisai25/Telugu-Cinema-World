"""Business logic. Turns database rows into API-ready dictionaries.

Rules: never invent data (missing stays None), always carry the source,
and keep the maths in small functions that tests can check.
"""
from collections import defaultdict
from datetime import date
from itertools import combinations
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.loaders.cleaning import norm_key
from app.models import Collection, Film, FilmCrew, Person

REPORTED = "Reported"
NOT_AVAILABLE = "Not available"
ROLE_ORDER = ["director", "hero", "heroine", "villain", "music", "cinematographer", "producer"]

# Reported facts about Varanasi that are not in the database. Verify before release.
VARANASI_FACTS = [
    {
        "fact": "Release date: 7 April 2027",
        "label": REPORTED,
        "source_name": "Hollywood Reporter India",
        "source_url": "https://www.hollywoodreporterindia.com/features/insight/ss-rajamouli-mahesh-babus-varanasi-locks-april-2027-release-date",
        "fetched_on": date(2026, 10, 23),
    },
    {
        "fact": "Shot in IMAX 1.43:1 (described as the first non-English film in that format)",
        "label": REPORTED,
        "source_name": "Dark Horizons",
        "source_url": "https://www.darkhorizons.com/?p=193815",
        "fetched_on": date(2026, 10, 23),
    },
]


# ---------- small helpers ----------

def pct(part: Optional[float], whole: Optional[float]) -> Optional[float]:
    """part/whole as a percentage, or None when either side is missing."""
    if part is None or not whole:
        return None
    return round(part / whole * 100, 1)


def pick_collection(film: Film, market: str) -> Optional[Collection]:
    """Headline figure when several sources exist: newest fetch wins;
    on a tie the smaller (more conservative) amount wins."""
    rows = [c for c in film.collections if c.market == market]
    if not rows:
        return None
    return sorted(rows, key=lambda c: (-c.fetched_on.toordinal(), c.amount_cr))[0]


def amount(film: Film, market: str) -> Optional[float]:
    c = pick_collection(film, market)
    return c.amount_cr if c else None


def roi_values(film: Film):
    """(roi, roi_min). roi uses budget_cr; roi_min uses the top of a budget range."""
    ww = amount(film, "worldwide")
    if ww is None or not film.budget_cr:
        return None, None
    roi = round(ww / film.budget_cr, 2)
    roi_min = round(ww / film.budget_cr_max, 2) if film.budget_cr_max else None
    return roi, roi_min


# ---------- building blocks for responses ----------

def film_summary(f: Film) -> dict:
    return {
        "id": f.id, "title": f.title, "language": f.language,
        "release_date": f.release_date, "status": f.status,
        "director": f.director, "poster_url": f.poster_url,
    }


def sourced_budget(f: Film) -> dict:
    if f.budget_cr is None:
        return {"label": NOT_AVAILABLE}
    return {
        "amount_cr": f.budget_cr, "amount_max_cr": f.budget_cr_max, "label": REPORTED,
        "source_name": f.budget_source_name, "source_url": f.budget_source_url,
        "fetched_on": f.budget_fetched_on, "note": f.budget_note,
    }


def sourced_worldwide(f: Film) -> dict:
    c = pick_collection(f, "worldwide")
    if c is None:
        return {"label": NOT_AVAILABLE}
    return {
        "amount_cr": c.amount_cr, "label": c.label, "source_name": c.source_name,
        "source_url": c.source_url, "fetched_on": c.fetched_on, "note": c.conversion_note,
    }


def collections_out(f: Film) -> list[dict]:
    rows = sorted(f.collections, key=lambda c: (c.market, -c.fetched_on.toordinal()))
    return [{
        "market": c.market, "amount_cr": c.amount_cr, "label": c.label,
        "source_name": c.source_name, "source_url": c.source_url,
        "fetched_on": c.fetched_on, "conversion_note": c.conversion_note,
    } for c in rows]


def ratings_out(f: Film) -> list[dict]:
    out = []
    for r in f.ratings:
        if r.source == "imdb" and not settings.show_imdb_ratings:
            continue
        out.append({"source": r.source, "score": r.score,
                    "vote_count": r.vote_count, "fetched_on": r.fetched_on})
    return sorted(out, key=lambda r: r["source"])


def crew_out(f: Film) -> list[dict]:
    rows = sorted(f.crew, key=lambda c: (ROLE_ORDER.index(c.role), c.person.name))
    return [{
        "person_id": c.person_id, "name": c.person.name, "photo_url": c.person.photo_url,
        "role": c.role, "character_name": c.character_name,
    } for c in rows]


# ---------- loading ----------

def load_film(db: Session, film_id: int) -> Optional[Film]:
    return db.scalar(
        select(Film).where(Film.id == film_id).options(
            selectinload(Film.crew).selectinload(FilmCrew.person),
            selectinload(Film.collections),
            selectinload(Film.ratings),
            selectinload(Film.links),
        )
    )


def load_all_films(db: Session) -> list[Film]:
    return list(db.scalars(
        select(Film).options(selectinload(Film.collections), selectinload(Film.ratings))
    ).all())


# ---------- search, film page, people ----------

def search_films(db: Session, q: str, limit: int = 10) -> list[dict]:
    """Autocomplete. Ignores case, spaces and punctuation ('kgf chapter 2' finds
    'KGF: Chapter 2'). Fine for a few hundred films; use SQL search if it grows."""
    nq = norm_key(q)
    if not nq:
        return []
    hits = [f for f in db.scalars(select(Film)).all() if nq in norm_key(f.title)]
    hits.sort(key=lambda f: (
        not norm_key(f.title).startswith(nq),                # title starts with query first
        -(f.release_date.toordinal() if f.release_date else 0),  # then newest first
    ))
    return [film_summary(f) for f in hits[:limit]]


def similar_films(db: Session, film: Film, limit: int = 6) -> list[dict]:
    """Films sharing key crew first; then same-language films nearest in time."""
    key_roles = ("director", "hero", "heroine", "music")
    people_ids = {c.person_id for c in film.crew if c.role in key_roles}
    results, used = [], {film.id}

    if people_ids:
        rows = db.execute(
            select(FilmCrew.film_id, func.count(func.distinct(FilmCrew.person_id)))
            .where(FilmCrew.person_id.in_(people_ids), FilmCrew.role.in_(key_roles),
                   FilmCrew.film_id != film.id)
            .group_by(FilmCrew.film_id)
        ).all()
        shared = {fid: n for fid, n in rows}
        if shared:
            films = db.scalars(select(Film).where(Film.id.in_(shared))).all()
            films.sort(key=lambda f: (-shared[f.id], f.release_date or date.max))
            for f in films[:limit]:
                d = film_summary(f)
                d["reason"] = f"Shares {shared[f.id]} key crew member(s)"
                results.append(d)
                used.add(f.id)

    if len(results) < limit:
        ref = film.release_date or date.today()
        same = db.scalars(
            select(Film).where(Film.language == film.language, Film.id.not_in(used))
        ).all()
        same.sort(key=lambda f: abs(((f.release_date or ref) - ref).days))
        for f in same[: limit - len(results)]:
            d = film_summary(f)
            d["reason"] = "Same language"
            results.append(d)
    return results


def film_detail(db: Session, f: Film) -> dict:
    roi, roi_min = roi_values(f)
    out = film_summary(f)
    out.update({
        "tmdb_id": f.tmdb_id, "imdb_id": f.imdb_id, "runtime": f.runtime,
        "overview": f.overview, "backdrop_url": f.backdrop_url, "trailer_url": f.trailer_url,
        "budget": sourced_budget(f), "worldwide": sourced_worldwide(f),
        "roi": roi, "roi_min": roi_min,
        "collections": collections_out(f), "ratings": ratings_out(f),
        "crew": crew_out(f), "similar": similar_films(db, f),
        "links": [{"site": l.site, "url": l.url} for l in f.links],
    })
    return out


def person_detail(db: Session, person_id: int) -> Optional[dict]:
    p = db.scalar(
        select(Person).where(Person.id == person_id).options(
            selectinload(Person.credits).selectinload(FilmCrew.film).selectinload(Film.collections)
        )
    )
    if p is None:
        return None
    credits = sorted(p.credits, key=lambda c: (c.film.release_date or date.max, c.role))
    filmography, rois = [], []
    for c in credits:
        roi, _ = roi_values(c.film)
        if roi is not None:
            rois.append(roi)
        filmography.append({
            "film": film_summary(c.film), "role": c.role, "character_name": c.character_name,
            "budget_cr": c.film.budget_cr, "worldwide_cr": amount(c.film, "worldwide"), "roi": roi,
        })
    return {
        "id": p.id, "name": p.name, "photo_url": p.photo_url, "known_for": p.known_for,
        "stats": {
            "films": len({c.film_id for c in credits}),
            "films_with_roi": len(rois),
            "average_roi": round(sum(rois) / len(rois), 2) if rois else None,
            "note": "average_roi covers only films that have both a budget and a worldwide figure",
        },
        "filmography": filmography,
    }


# ---------- analytics ----------

SAMPLE_NOTE = ("Based only on the films in this dataset (a curated sample), "
               "not the whole industry. All money figures are 'Reported'.")


def overview(films: list[Film]) -> dict:
    released = [f for f in films if f.status == "released"]
    with_ww = [(f, amount(f, "worldwide")) for f in released if amount(f, "worldwide") is not None]
    top = sorted(with_ww, key=lambda t: -t[1])[:10]

    years = defaultdict(lambda: {"films": 0, "films_with_worldwide": 0, "total_worldwide_cr": 0.0})
    for f in released:
        if f.release_date is None:
            continue
        y = years[f.release_date.year]
        y["films"] += 1
        ww = amount(f, "worldwide")
        if ww is not None:
            y["films_with_worldwide"] += 1
            y["total_worldwide_cr"] += ww

    return {
        "total_films": len(films),
        "released_films": len(released),
        "upcoming_films": len(films) - len(released),
        "films_with_worldwide": len(with_ww),
        "languages": sorted({f.language for f in films}),
        "top_grossers": [{**film_summary(f), "worldwide_cr": ww} for f, ww in top],
        "by_year": [{"year": y, **{k: (round(v, 2) if isinstance(v, float) else v) for k, v in d.items()}}
                    for y, d in sorted(years.items())],
        "note": SAMPLE_NOTE,
    }


def _shares(bucket: dict) -> tuple[list[dict], float]:
    total = sum(v["total_cr"] for v in bucket.values())
    rows = [{
        "language": lang, "total_cr": round(v["total_cr"], 2), "films": v["films"],
        "share_pct": round(v["total_cr"] / total * 100, 1),
    } for lang, v in sorted(bucket.items(), key=lambda kv: -kv[1]["total_cr"])]
    return rows, round(total, 2)


def language_share(films: list[Film]) -> dict:
    per_year = defaultdict(lambda: defaultdict(lambda: {"total_cr": 0.0, "films": 0}))
    overall = defaultdict(lambda: {"total_cr": 0.0, "films": 0})
    for f in films:
        ww = amount(f, "worldwide")
        if f.status != "released" or ww is None or f.release_date is None:
            continue
        for bucket in (per_year[f.release_date.year], overall):
            bucket[f.language]["total_cr"] += ww
            bucket[f.language]["films"] += 1

    years = []
    for y in sorted(per_year):
        rows, total = _shares(per_year[y])
        years.append({"year": y, "total_cr": total, "languages": rows})
    overall_rows, overall_total = _shares(overall) if overall else ([], 0.0)
    return {"basis": "worldwide gross (Reported)", "years": years,
            "overall": {"total_cr": overall_total, "languages": overall_rows}, "note": SAMPLE_NOTE}


def pan_india(films: list[Film], language: str = "Telugu") -> dict:
    chosen = sorted(
        (f for f in films if f.language == language and f.status == "released"),
        key=lambda f: f.release_date or date.max,
    )
    rows = []
    for f in chosen:
        india, hindi, overseas, ww = (amount(f, m) for m in
                                      ("india_net", "hindi_belt", "overseas", "worldwide"))
        rows.append({
            **film_summary(f), "year": f.release_date.year if f.release_date else None,
            "india_net_cr": india, "hindi_belt_cr": hindi, "overseas_cr": overseas, "worldwide_cr": ww,
            "hindi_belt_share_pct": pct(hindi, india),   # hindi_belt / india_net
            "overseas_share_pct": pct(overseas, ww),     # overseas / worldwide
        })
    return {
        "language": language,
        "coverage": {
            "films": len(rows),
            "with_hindi_belt": sum(r["hindi_belt_cr"] is not None for r in rows),
            "with_overseas": sum(r["overseas_cr"] is not None for r in rows),
        },
        "films": rows,
        "note": ("Hindi-belt and overseas splits are shown only where a source states them; "
                 "otherwise 'Not available'. Shares can mix sources, so treat them as indicative."),
    }


def budget_vs_collection(films: list[Film]) -> dict:
    points, missing = [], 0
    for f in films:
        if f.status != "released":
            continue
        ww = amount(f, "worldwide")
        if f.budget_cr is None or ww is None:
            missing += 1
            continue
        roi, roi_min = roi_values(f)
        points.append({
            **film_summary(f), "year": f.release_date.year if f.release_date else None,
            "budget_cr": f.budget_cr, "budget_max_cr": f.budget_cr_max,
            "worldwide_cr": ww, "roi": roi, "roi_min": roi_min,
        })
    points.sort(key=lambda p: p["budget_cr"])
    return {"points": points, "excluded_films": missing,
            "note": "Films missing a budget or a worldwide figure are excluded, not estimated. " + SAMPLE_NOTE}


def compare_card(f: Film) -> dict:
    roi, roi_min = roi_values(f)
    out = film_summary(f)
    out.update({
        "budget": sourced_budget(f), "worldwide": sourced_worldwide(f),
        "roi": roi, "roi_min": roi_min,
        "ratings": ratings_out(f), "collections": collections_out(f),
    })
    return out


# ---------- collaboration network ----------

def build_network(db: Session, roles: list[str], min_weight: int = 1) -> dict:
    """Nodes = people, links = number of films two people worked on together."""
    rows = db.scalars(
        select(FilmCrew).where(FilmCrew.role.in_(roles))
        .options(selectinload(FilmCrew.person), selectinload(FilmCrew.film))
    ).all()

    people_in_film = defaultdict(dict)   # film_id -> {person_id: Person}
    person_roles = defaultdict(set)
    person_films = defaultdict(set)
    titles = {}
    for r in rows:
        people_in_film[r.film_id][r.person_id] = r.person
        person_roles[r.person_id].add(r.role)
        person_films[r.person_id].add(r.film_id)
        titles[r.film_id] = r.film.title

    together = defaultdict(list)         # (person a, person b) -> [film ids]
    for fid, people in people_in_film.items():
        for a, b in combinations(sorted(people), 2):
            together[(a, b)].append(fid)

    links = [{"source": a, "target": b, "weight": len(fids),
              "films": sorted(titles[i] for i in fids)}
             for (a, b), fids in together.items() if len(fids) >= min_weight]
    links.sort(key=lambda l: -l["weight"])

    linked = {x for l in links for x in (l["source"], l["target"])}
    people = {pid: p for people in people_in_film.values() for pid, p in people.items()}
    nodes = [{"id": pid, "name": people[pid].name, "photo_url": people[pid].photo_url,
              "roles": sorted(person_roles[pid]), "films": len(person_films[pid])}
             for pid in sorted(linked)]
    return {"roles": roles, "nodes": nodes, "links": links,
            "note": "Only people with at least one collaboration are shown. "
                    "Hero/heroine roles come from TMDB billing order plus manual overrides."}


# ---------- Varanasi Watch ----------

def varanasi_watch(db: Session, today: Optional[date] = None, share_pct: float = 100.0) -> Optional[dict]:
    today = today or date.today()
    film = db.scalar(
        select(Film).where(Film.title == "Varanasi")
        .options(selectinload(Film.collections), selectinload(Film.ratings))
    )
    if film is None:
        return None

    days = (film.release_date - today).days if film.release_date else None
    countdown = {
        "release_date": film.release_date,
        "days_remaining": max(days, 0) if days is not None else None,
        "released": days is not None and days <= 0,
        "label": REPORTED,
    }

    # Earlier films that have both a budget and a worldwide figure.
    earlier = []
    for f in load_all_films(db):
        ww = amount(f, "worldwide")
        if f.id == film.id or f.budget_cr is None or ww is None:
            continue
        roi, roi_min = roi_values(f)
        earlier.append({**film_summary(f), "budget_cr": f.budget_cr, "budget_max_cr": f.budget_cr_max,
                        "worldwide_cr": ww, "roi": roi, "roi_min": roi_min})
    earlier.sort(key=lambda e: -e["budget_cr"])

    def scenario(name: str, budget: float) -> dict:
        needed = round(budget / (share_pct / 100), 2)
        return {
            "name": name, "budget_cr": budget, "collection_needed_cr": needed,
            "earlier_films_at_or_above": [e["title"] for e in earlier if e["worldwide_cr"] >= needed],
        }

    scenarios = []
    if film.budget_cr is not None:
        scenarios.append(scenario("Low end of reported budget", film.budget_cr))
        if film.budget_cr_max:
            scenarios.append(scenario("High end of reported budget", film.budget_cr_max))

    return {
        "film": film_summary(film),
        "countdown": countdown,
        "budget": sourced_budget(film),
        "facts": VARANASI_FACTS,
        "comparison": earlier,
        "break_even": {
            "share_pct": share_pct,
            "assumption": ("collection_needed = budget / share. 'share' is the part of worldwide gross "
                           "assumed to reach the producer. It is an adjustable assumption, not reported data. "
                           "At 100% this is simply gross = budget."),
            "scenarios": scenarios,
        },
        "note": "All Varanasi facts are Reported and may change; verify before the final release.",
    }