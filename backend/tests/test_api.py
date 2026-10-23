"""API tests. Numbers come from the fake data in conftest.py."""
from datetime import date

from app import services


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


# ---------- search ----------

def test_search_prefix_first_and_case_insensitive(client):
    titles = [f["title"] for f in client.get("/api/search?q=ALP").json()]
    assert titles == ["Alpha"]


def test_search_ignores_punctuation(client):
    titles = [f["title"] for f in client.get("/api/search?q=gamma the film").json()]
    assert titles == ["Gamma: The Film"]


def test_search_punctuation_only_returns_nothing(client):
    assert client.get("/api/search?q=!!").json() == []


def test_search_requires_query(client):
    assert client.get("/api/search").status_code == 422


# ---------- film page ----------

def test_film_page_with_sources(client, ids):
    data = client.get(f"/api/films/{ids['Alpha']}").json()
    assert data["budget"]["label"] == "Reported"
    assert data["budget"]["source_name"] == "Budget Src"
    assert data["worldwide"]["amount_cr"] == 600
    assert data["roi"] == 6.0
    assert {r["source"] for r in data["ratings"]} == {"tmdb", "imdb"}
    assert [c["role"] for c in data["crew"]] == ["director", "hero", "music"]


def test_missing_values_are_not_available_never_zero(client, ids):
    data = client.get(f"/api/films/{ids['Delta']}").json()
    assert data["budget"]["label"] == "Not available"
    assert data["budget"]["amount_cr"] is None
    assert data["worldwide"]["label"] == "Not available"
    assert data["roi"] is None
    assert data["ratings"] == []


def test_newest_source_is_the_headline_and_roi_range(client, ids):
    data = client.get(f"/api/films/{ids['Beta']}").json()
    assert data["worldwide"]["amount_cr"] == 1800
    assert len(data["collections"]) == 2          # both sources are still shown
    assert data["roi"] == 9.0                      # 1800 / 200
    assert data["roi_min"] == 7.2                  # 1800 / 250


def test_similar_films_rank_shared_crew_first(client, ids):
    similar = client.get(f"/api/films/{ids['Alpha']}").json()["similar"]
    assert similar[0]["title"] == "Beta" and "2" in similar[0]["reason"]
    assert similar[1]["title"] == "Delta"
    assert "Alpha" not in [s["title"] for s in similar]


def test_film_not_found(client):
    assert client.get("/api/films/9999").status_code == 404


def test_imdb_can_be_hidden(client, ids, monkeypatch):
    monkeypatch.setattr(services.settings, "show_imdb_ratings", False)
    data = client.get(f"/api/films/{ids['Alpha']}").json()
    assert [r["source"] for r in data["ratings"]] == ["tmdb"]


# ---------- people ----------

def test_person_filmography(client, person_ids):
    data = client.get(f"/api/people/{person_ids['Hero One']}").json()
    assert [c["film"]["title"] for c in data["filmography"]] == ["Alpha", "Beta"]
    assert data["stats"]["films_with_roi"] == 2
    assert data["stats"]["average_roi"] == 7.5     # (6.0 + 9.0) / 2


def test_person_not_found(client):
    assert client.get("/api/people/9999").status_code == 404


# ---------- analytics ----------

def test_overview(client):
    data = client.get("/api/analytics/overview").json()
    assert data["total_films"] == 5
    assert data["upcoming_films"] == 1
    assert data["films_with_worldwide"] == 3
    assert data["top_grossers"][0]["title"] == "Beta"
    assert "dataset" in data["note"]


def test_language_share(client):
    data = client.get("/api/analytics/language-share").json()
    overall = {r["language"]: r["share_pct"] for r in data["overall"]["languages"]}
    assert overall == {"Telugu": 70.6, "Hindi": 29.4}      # 2400 vs 1000 of 3400
    assert data["years"][0]["year"] == 2015


def test_pan_india_only_where_a_source_states_it(client):
    data = client.get("/api/analytics/pan-india").json()
    assert data["coverage"]["with_hindi_belt"] == 1
    by_title = {f["title"]: f for f in data["films"]}
    assert by_title["Alpha"]["hindi_belt_share_pct"] == 25.0    # 100 / 400
    assert by_title["Alpha"]["overseas_share_pct"] == 20.0      # 120 / 600
    assert by_title["Beta"]["hindi_belt_share_pct"] is None


def test_budget_vs_collection_excludes_incomplete_films(client):
    data = client.get("/api/analytics/budget-vs-collection").json()
    assert [p["title"] for p in data["points"]] == ["Alpha", "Beta", "Gamma: The Film"]
    assert data["excluded_films"] == 1                           # Delta


# ---------- compare ----------

def test_compare(client, ids):
    data = client.get(f"/api/compare?a={ids['Alpha']}&b={ids['Delta']}").json()
    assert data["a"]["roi"] == 6.0
    assert data["b"]["budget"]["label"] == "Not available"


def test_compare_errors(client, ids):
    assert client.get(f"/api/compare?a={ids['Alpha']}&b={ids['Alpha']}").status_code == 400
    assert client.get(f"/api/compare?a={ids['Alpha']}&b=9999").status_code == 404


# ---------- network ----------

def test_network_counts_shared_films(client):
    data = client.get("/api/network").json()
    pair = [l for l in data["links"] if l["weight"] == 2]
    assert len(pair) == 1 and pair[0]["films"] == ["Alpha", "Beta"]   # Dir One + Hero One
    assert {n["name"] for n in data["nodes"]} == {"Dir One", "Hero One", "Music One"}


def test_network_rejects_unknown_role(client):
    assert client.get("/api/network?roles=wizard").status_code == 400


# ---------- Varanasi ----------

def test_varanasi_countdown_is_computed_from_the_date(db_session):
    data = services.varanasi_watch(db_session, today=date(2027, 4, 1))
    assert data["countdown"]["days_remaining"] == 6
    assert data["countdown"]["released"] is False
    after = services.varanasi_watch(db_session, today=date(2027, 5, 1))
    assert after["countdown"]["days_remaining"] == 0 and after["countdown"]["released"] is True


def test_varanasi_break_even_uses_adjustable_share(db_session):
    data = services.varanasi_watch(db_session, today=date(2027, 4, 1), share_pct=50)
    low, high = data["break_even"]["scenarios"]
    assert low["collection_needed_cr"] == 2000 and high["collection_needed_cr"] == 2800
    assert low["earlier_films_at_or_above"] == []
    full = services.varanasi_watch(db_session, today=date(2027, 4, 1), share_pct=100)
    assert set(full["break_even"]["scenarios"][0]["earlier_films_at_or_above"]) == {"Beta", "Gamma: The Film"}


def test_varanasi_endpoint(client):
    data = client.get("/api/varanasi?share_pct=50").json()
    assert data["budget"]["amount_cr"] == 1000 and data["budget"]["amount_max_cr"] == 1400
    assert data["budget"]["label"] == "Reported"
    assert data["break_even"]["share_pct"] == 50
    assert all(f["label"] == "Reported" for f in data["facts"])
    assert client.get("/api/varanasi?share_pct=0").status_code == 422