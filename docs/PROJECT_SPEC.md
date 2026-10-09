# PROJECT SPEC: "Telugu Cinema to the World" Film Market Analytics Dashboard

Owner: Mondem Pavan Sri Sai
Purpose: Portfolio and resume project for the Indian film industry.
Story: How Telugu cinema grew from a regional industry into a pan-India and global force (Baahubali, RRR, Pushpa 2, Kalki 2898 AD, and the upcoming Varanasi).

---

## 1. Scope

### In scope (version 1)
1. **Search** for a film with autocomplete, leading to a film page.
2. **Film page:** poster, backdrop, trailer link, language, release date, director, cast and crew with photos and roles, budget (reported), collections by market, TMDB and IMDb ratings, similar films, "compare with another film" button.
3. **Analytics pages**
   - Overview: total films, top grossers, year-wise trend, animated counters.
   - Language share over time.
   - Pan-India growth: Telugu films' Hindi-belt and overseas earnings over time.
   - Budget vs collection scatter plot with return on investment (ROI).
   - Hero view: a hero's filmography and results.
   - Duel mode: two films side by side (budget, ROI, ratings, collections).
4. **Collaboration network graph:** who has worked with whom (directors, heroes, music directors).
5. **Timeline slider:** "Telugu to the World", from Baahubali (2015) to Varanasi (2027).
6. **Varanasi Watch:** countdown to 7 April 2027, reported budget, comparison with earlier big films, break-even calculator (slider for the collection needed).
7. **Optional:** a "Book / see ratings" link-out button to BookMyShow or District (link only, no scraping).

### Out of scope for now (possible later upgrades)
- YouTube comments and audience sentiment analysis
- Critics panel
- Remuneration data
- Scraping BookMyShow, District or X
- Login / user accounts

---

## 2. Data rules (important)
- Use only legal public sources: **TMDB API**, **IMDb non-commercial datasets**, **Kaggle datasets**, **Wikipedia lists** of highest-grossing Indian films.
- Never scrape sites whose terms forbid it. Never copy review text.
- Every budget and collection figure must store: `source_name`, `source_url`, `fetched_on`, and a label **"Reported"** (these figures vary across sources; trackers such as Sacnilk state their numbers are independent and not reconciled to producer-announced figures).
- Never invent data. If a value is missing, show "Not available".
- Store money in **₹ crore**. Keep the original currency and the conversion note.
- Varanasi facts are reported and may change: release date 7 April 2027, reported budget range ₹1,000-1,400 crore, reportedly shot in IMAX 1.43:1. Show them as "Reported" and verify before the final release.

---

## 3. Tech stack

| Layer | Tools |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy, Pydantic, Pandas |
| Database | SQLite (local), PostgreSQL on AWS RDS |
| Data loading | Requests, TMDB API, IMDb TSV datasets, CSV import |
| Frontend | React (Vite), Tailwind CSS, Framer Motion, Recharts and D3 (network graph, map) |
| DevOps | Docker, Git, GitHub, GitHub Actions |
| AWS | S3 + CloudFront (frontend), EC2 + ALB or Lambda + API Gateway (API), RDS (database), EventBridge + Lambda (scheduled data refresh), Secrets Manager (API keys), IAM, CloudWatch |

---

## 4. Database schema (starting point)

- `films`: id, tmdb_id, title, language, release_date, director, budget_cr, runtime, overview, poster_url, backdrop_url, trailer_url
- `people`: id, tmdb_id, name, photo_url, known_for
- `film_crew`: id, film_id, person_id, role (hero, heroine, villain, director, music, cinematographer, producer), character_name
- `collections`: id, film_id, market (india_net, hindi_belt, overseas, worldwide), amount_cr, source_name, source_url, fetched_on
- `ratings`: id, film_id, source (tmdb, imdb), score, vote_count, fetched_on
- `film_links`: id, film_id, site (bookmyshow, district), url (optional link-outs)

Useful derived values (SQL or Pandas): ROI = worldwide collection / budget; language share = language total / overall total; Hindi-belt share = hindi_belt / india_net.

---

## 5. API endpoints (FastAPI)

- `GET /api/search?q=` : autocomplete search
- `GET /api/films/{id}` : full film page data
- `GET /api/people/{id}` : person and filmography
- `GET /api/analytics/overview`
- `GET /api/analytics/language-share`
- `GET /api/analytics/pan-india`
- `GET /api/analytics/budget-vs-collection`
- `GET /api/compare?a={id}&b={id}`
- `GET /api/network` : collaboration graph (nodes and links)
- `GET /api/varanasi` : Varanasi Watch data
- `GET /api/health` : health check for the load balancer

---

## 6. UI direction (make it unique and engaging)
- Cinematic dark theme; the film's backdrop fades in behind the page; smooth page transitions.
- Animated counters; hover cards on cast photos.
- "Telugu to the World" timeline slider that grows the charts as it moves.
- Collaboration web (network graph).
- Pan-India map showing regional share.
- Duel mode for two films.
- Varanasi Watch with countdown and break-even slider.
- Fully responsive for mobile; accessible colour contrast.

---

## 7. Build phases (one chat per phase)

| Phase | Deliverable | Time |
|---|---|---|
| 1 | Repo structure, schema, seed data for about 15-20 films | Day 1-2 |
| 2 | TMDB and IMDb loaders, cleaning code, CSV import for collections | Day 3-5 |
| 3 | FastAPI endpoints with tests | Day 6-8 |
| 4 | React app: search, film page, analytics pages, theme | Day 9-14 |
| 5 | Network graph, timeline slider, Varanasi Watch | Day 12-15 |
| 6 | Docker, AWS setup, GitHub Actions deploy | Day 15-18 |
| 7 | README, screenshots, live link, resume wording | Day 19-21 |

Seed film list (suggested): Baahubali: The Beginning, Baahubali 2, RRR, Pushpa: The Rise, Pushpa 2, Kalki 2898 AD, Salaar, Magadheera, Eega, Sye Raa Narasimha Reddy, Saaho, Ala Vaikunthapurramuloo, Jawan, Pathaan, KGF Chapter 2, Kantara, Varanasi (upcoming).

---

## 8. Working rules for the assistant
- I am a fresher. Explain each step simply, then give complete working code.
- Work one phase at a time and wait for my confirmation.
- The assistant cannot push to my GitHub or AWS. Give exact commands for me to run, and I will paste back any errors.
- Never put API keys in code or chat. Use a `.env` file locally and AWS Secrets Manager in production.
- Keep the code clean and commented, with a README section for each phase.

---

## 9. Definition of done
- [ ] Search finds a film and opens a full film page
- [ ] All analytics pages load with real, sourced data
- [ ] Duel mode, timeline, network graph and Varanasi Watch work
- [ ] Runs on mobile and desktop
- [ ] Deployed on AWS with a public link
- [ ] Code on GitHub with README, screenshots and a CI/CD workflow
- [ ] Every figure shown has a source and is labelled "Reported"

---

## 10. Resume wording (final version, after the build)
"Built and deployed a full-stack film market analytics dashboard (FastAPI, React, PostgreSQL, AWS) analysing Indian box-office data by language, budget, hero and market, to study the growth of Telugu cinema in the Hindi and overseas markets."
