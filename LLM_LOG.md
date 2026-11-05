# LLM use log

The project brief requires declaring when and how LLMs were used.
One line per session: date | tool | what I asked | what it produced | what I checked or changed myself.

| Date | Tool | What I asked | What it produced | What I checked / changed |
|---|---|---|---|---|
| 26-27 Oct 2026 | Claude (chat) | Brainstorm project ideas from the brief; refine the Wikipedia product-attention idea; check originality and existing tools | Shortlist of ideas, literature (Da, Engelberg & Gao 2011; Pyun 2024), list of existing tools, project plan and roadmap | Challenged the ideas (what to do with the signal, reporting season, originality); chose the product + click-through angle myself |
| 5 Nov 2026 | Claude | Set up the project folder and write the first data-pull script | Folder structure, README, `src/fetch_pageviews.py` | |
| 5 Nov 2026 | Claude Code | Run the first real data pull, check it, set up Git | Real pageviews 2017–4 Nov 2026 and chart; found and fixed the 14 Sep 2026 rename of "Novo Nordisk" to "Novo (company)" (script now adds up old + new titles); `.gitignore` and local Git repository | |
| 5 Nov 2026 | Claude Code | Test whether product-to-company click-through exists in the clickstream | `src/fetch_clickstream.py` (streams monthly files, keeps only our rows); results for Sep 2018, Sep 2024, Oct 2026: Semaglutide → Novo clicks present every month, conversion ≈ 0.9%, 1.0%, 2.5% | |
| 5 Nov 2026 | Claude Code | Draft the company/product universe and check it automatically | Draft of 73 companies / 159 products (`universe_draft.csv`); `check_universe.py` (titles, views, Oct 2026 clicks, price history); `prepare_review.py` → `universe_review.csv` with keep/drop/fix/decide suggestions for my hand check | |
| 5 Nov 2026 | Claude Code | Apply the suggested picks and finalise the universe | `finalise_universe.py` → `products_to_companies.csv` (68 companies, 140 products; old company titles verified; Google used for Alphabet; Meta company series from Dec 2019); recheck: every product has clicks to its company page | |

| 6 Nov 2026 | Claude Code | Download page views for the whole universe | `fetch_pageviews.py` (all 208 articles, 2017–4 Nov 2026) and shared `wiki_api.py`; found and fixed 11 product renames (e.g. Hoka renamed twice) and a missed Block title; fixed unpublished days showing as zero views | |
