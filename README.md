# GitHub Engagement Stats

Nightly snapshots of stars, views, and clones for your public GitHub repos with no dependencies and minimal setup. Also generates a Markdown report with totals and per-repo breakdowns ([example](stats.md)).

By default it discovers every public repo you own with 2+ stars. You can override this if you want to track a different set.

## Quick start

1. **Fork** this repo.
2. **Enable Actions** when GitHub prompts you.
3. Done. The workflow runs nightly at 00:07 UTC and appends one row per repo to `data/*.csv`. It also rebuilds `stats.md` as a simple dashboard.

You can trigger it manually via **Actions > "GitHub traffic snapshot" > Run workflow** if you don't want to wait.

### Optional: Personal Access Token

The default `GITHUB_TOKEN` can only see traffic for the current repository. If you want traffic stats across all your repos, create a PAT with `public_repo` scope and add it as a repository secret called `PUBLIC_REPOS_TOKEN`.

### Optional: Configuration variables

In **Settings > Variables**, you can set:

- `MIN_STARS`: change the auto-discover threshold (default is 2)
- `TARGET_REPOS`: comma-separated list like `owner1/repoA,owner2/repoB` to track specific repos instead of (or in addition to) the auto-discovered ones

## Customising

- **Track only specific repos**: set `TARGET_REPOS` and it takes priority over auto-discovery.
- **Add extra repos**: leave `TARGET_REPOS` empty and list them in `config.yml` instead; they get merged with the discovered set.
- **Change the schedule**: edit the `cron:` line in `.github/workflows/stats.yml`.
- **Stop CI commits**: remove the final commit step in the workflow.

## Running locally

```bash
git clone https://github.com/<you>/github-engagement-stats.git
cd github-engagement-stats

# Supply a PAT (only "public_repo" scope needed)
export GITHUB_TOKEN=ghp_yourTokenHere

# Optional overrides
export MIN_STARS=1
export TARGET_REPOS=you/special-repo

# Collect stats
python fetch_stats.py

# Generate the markdown report
python generate_report.py
```
