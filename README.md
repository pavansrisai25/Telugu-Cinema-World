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