# Telugu Cinema to the World

Film market analytics dashboard showing how Telugu cinema grew from a regional
industry into a pan-India and global force. Full plan: `docs/PROJECT_SPEC.md`.

## Data policy
Only public, legal sources (TMDB API, IMDb non-commercial datasets, Kaggle,
Wikipedia). Every budget/collection figure is labelled "Reported" with source
and date. Missing values show "Not available". Nothing is invented.

## Phase 1: Setup and schema
```bash
cd backend
python -m venv venv && venv\Scripts\activate   # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env                          # Mac/Linux: cp
python -m app.seed
uvicorn app.main:app --reload
```
Health check: http://127.0.0.1:8000/api/health

## Phase 2: Data loaders
```bash
python -m app.loaders.tmdb_loader        # film details, cast/crew, TMDB rating
python -m app.loaders.imdb_loader        # IMDb rating (official dataset)
python -m app.loaders.csv_import budgets
python -m app.loaders.csv_import collections
python -m app.loaders.report             # data coverage per film
```
Budgets and collections come from `backend/data/*.csv`, each row with source name,
URL and fetch date, and are labelled "Reported".

## Attribution
This product uses the TMDB API but is not endorsed or certified by TMDB.
Ratings information courtesy of IMDb (https://www.imdb.com), used under its
non-commercial dataset terms.
