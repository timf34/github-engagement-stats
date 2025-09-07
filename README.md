# 📊 GitHub Engagement Stats

**Nightly, dependency-free snapshots of ⭐ stars, 👁 views and 📥 clones for all your public repos – zero set-up.**  
Also auto-generates a clean Markdown report with totals and per-repo breakdowns: [**see example ›**](stats.md)

*By default the action discovers every public repo you own that has **≥ 2 stars**.  
Want to track a different set? Just tell it!*

---

## 🚀 Fork-and-forget in 3 clicks

1. **Fork** this repo to your personal account or org.  
2. Enable **Actions** when GitHub prompts you.  
3. *(Optional)* Open **Settings → Variables** and tweak:
   * `MIN_STARS` – raise/lower the auto-discover threshold (default **2**).
   * `TARGET_REPOS` – comma-separated list like
     `owner1/repoA,owner2/repoB` (adds or replaces the auto list).
4. *(Optional)* Add a Personal Access Token with `public_repo` scope as
   secret **PUBLIC_REPOS_TOKEN** if you want to collect traffic stats for
   other repositories you own.

That’s it. The workflow runs every night at 00:07 UTC and appends one row per repo to `/data/*.csv`.  
It also builds `/stats.md` as a lightweight dashboard of total/lifetime stats.

Run it straight away via **Actions → “📊 GitHub traffic snapshot” → Run workflow** if you don’t want to wait.

---

## 🔧 Customising

* **Track only certain repos** – set `TARGET_REPOS` (auto-discover still runs but the explicit list wins).  
* **Include extra repos** – keep `TARGET_REPOS` empty and list them in `config.yml` instead; they’ll be *added* to the discovered set.  
* **Change the schedule** – edit the `cron:` line in `.github/workflows/stats.yml`.  
* **Stop committing from CI** – remove `--commit` in that same workflow step.

All configuration lives in **repo settings**. The workflow uses
`secrets.PUBLIC_REPOS_TOKEN` when present; otherwise it falls back to the
default `GITHUB_TOKEN`, which can only see the current repository's traffic.

---

## 🖥 Run locally 

```bash
git clone https://github.com/<you>/github-engagement-stats.git
cd github-engagement-stats

# 1.  Supply a Personal Access Token (only "public_repo" scope needed)
export GITHUB_TOKEN=ghp_yourTokenHere

# 2.  Optional overrides
export MIN_STARS=1
export TARGET_REPOS=you/special-repo

# 3.  Snapshot!
python fetch_stats.py           # add --commit to create a local git commit

# 4. Generate your markdown report
python generate_report.py
