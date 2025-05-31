# 📊 GitHub Engagement Stats

Minimal, dependency-free template that records **stars, views, clones** for
any public repository you own and appends one CSV row per day.

## 🏁 Quick start

1. **Fork this repo**.

2. Decide which repos to track:

   *Easiest*: open **Settings → Variables** and add  
   `TARGET_REPOS = owner1/repoA,owner2/repoB`.

   *Alternative*: edit `config.yml`:

   ```yaml
   repositories:
     - owner1/repoA
     - owner2/repoB
