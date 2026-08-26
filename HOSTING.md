# Hosting & deploying this project (all free)

This walks you from "code on my laptop" to "a public GitHub repo where a robot runs
my tests on every change and publishes my docs." Every step costs £0.

You only host the **`build/`** project. The `knowledge/` folder is your private
study material — it doesn't need hosting (though you can keep it in the same repo or
a separate one; see the note at the end).

> Prerequisite: a free GitHub account (github.com) and git installed. You already
> have git — you used it in notebook 02.

---

## Step 1 — Make the build folder its own git repo

A portfolio repo should contain *just the project*, not the whole `data_engineer`
folder. So we initialise git inside `build/`.

```powershell
cd C:\Users\divya\Downloads\learning\data_engineer\10_cicd_data_pipelines\build

git init
git add .
git status        # sanity-check: you should NOT see .env, .venv, or warehouse.duckdb
                  # (they're in .gitignore). If you do, stop and fix .gitignore first.
git commit -m "Sales pipeline with CI/CD: ETL, dbt models, tests, GitHub Actions"
```

> Why the `git status` check matters: the single most common junior mistake is
> committing a secret or a giant data/venv folder. The `.gitignore` already prevents
> it — this step is you *verifying* it, which is a good habit.

---

## Step 2 — Create the repo on GitHub and push

1. Go to https://github.com/new
2. Name it something real, e.g. `sales-pipeline-cicd`. **Leave it empty** — no
   README, no .gitignore, no licence (you already have those locally).
3. Click *Create repository*. GitHub shows you a URL. Use it below.

```powershell
git remote add origin https://github.com/YOURNAME/sales-pipeline-cicd.git
git branch -M main
git push -u origin main
```

Refresh the repo page — your code is now on GitHub.

---

## Step 3 — Watch CI run (this is the magic moment)

GitHub automatically finds files in `.github/workflows/` and runs them. Because you
just pushed to `main`, the **CI** workflow already started.

1. On your repo page, click the **Actions** tab.
2. You'll see a run named **CI**. Click it, then click the `build-and-test` job.
3. Watch the steps execute live: checkout → set up Python → install → lint → pytest →
   ETL → dbt build. Each gets a green tick.

If anything is red, click the failed step to read its log top-to-bottom. The most
common first-time causes are covered in notebook 10's troubleshooting section.

---

## Step 4 — Add the status badge

The badge is the live `passing`/`failing` image at the top of your README.

1. Open `build/README.md`. The first lines already contain a badge:
   ```markdown
   ![CI](https://github.com/YOURNAME/REPO/actions/workflows/ci.yml/badge.svg)
   ```
2. Replace `YOURNAME/REPO` with your actual `username/repository`.
3. Commit and push:
   ```powershell
   git add README.md
   git commit -m "Add CI status badge"
   git push
   ```
4. Refresh the repo — a green **CI passing** badge now sits at the top. (GitHub also
   builds the badge URL for you under Actions → CI → ⋯ → *Create status badge*.)

---

## Step 5 — Protect `main` so red builds can't merge (this is what makes CI real)

CI that *exists* is nice. CI that's *enforced* is the job. Branch protection blocks
merging unless CI is green.

1. Repo → **Settings** → **Branches** → **Add branch ruleset** (or *Add rule* for the
   classic UI).
2. Target branch: `main`.
3. Enable **Require status checks to pass before merging**, and select the
   **`Lint, test, and build`** check (it appears after CI has run at least once).
4. (Recommended) Enable **Require a pull request before merging**.
5. Save.

Now nobody — including you — can merge a branch into `main` while CI is red. That's
the safety net working.

### Try the whole loop once (do this — it's the lesson)
```powershell
git switch -c break-it
# open pipeline/transform.py and break something, e.g. change the revenue formula
git commit -am "deliberately break revenue to watch CI catch it"
git push -u origin break-it
```
Open a pull request on GitHub for `break-it`. Watch CI go **red** and the merge button
get blocked. Then fix it, push again, watch it go **green**, and merge. That loop —
red, fix, green — is the entire point of this project. Do it once for real.

---

## Step 6 — Publish the dbt docs to GitHub Pages (the "CD" half)

The `deploy.yml` workflow builds your dbt documentation site and deploys it to GitHub
Pages whenever you push to `main`. You just need to switch Pages on.

1. Repo → **Settings** → **Pages**.
2. Under **Build and deployment → Source**, choose **GitHub Actions**.
3. Push anything to `main` (or Actions → *Deploy dbt docs* → **Run workflow**, thanks
   to the `workflow_dispatch` trigger).
4. When the `Deploy dbt docs` workflow finishes, Settings → Pages shows your live URL,
   something like `https://YOURNAME.github.io/sales-pipeline-cicd/`. That's your dbt
   docs — model lineage, descriptions, tests — hosted, public, free. Link it from
   your CV.

---

## Step 7 — (Optional but classy) run the pipeline on a schedule

Right now CI runs on changes. You can *also* run the pipeline nightly — a free
"Airflow in the cloud" using GitHub Actions' cron. Add this workflow as
`.github/workflows/scheduled.yml`:

```yaml
name: Nightly pipeline
on:
  schedule:
    - cron: "0 6 * * *"   # 06:00 UTC daily
  workflow_dispatch:
permissions:
  contents: read
jobs:
  run:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: build
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - uses: actions/setup-python@0b93645e9fea7318ecaed2b359559ac225c90a2b  # v5.3.0
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -r requirements.txt
      - run: python scripts/generate_data.py
      - run: python -m pipeline.etl
      - run: dbt build --project-dir dbt_sales --profiles-dir dbt_sales
```

Mention this in interviews: "I also schedule the pipeline with a cron-triggered
Actions workflow." It checks the *orchestration* box for free.

---

## Secrets — the rule you never break

This project uses DuckDB, so it has no real secret. But the moment you swap in a cloud
database, you'll have a connection string. Never commit it.

- **Locally:** put it in `build/.env` (already git-ignored). Copy `.env.example` to
  start.
- **In CI:** repo → Settings → **Secrets and variables → Actions → New repository
  secret**. Add e.g. `DB_URL`. Reference it in a workflow as `${{ secrets.DB_URL }}`
  and expose it to a step via `env:`.

If you ever *do* commit a secret: assume it's compromised, rotate it (change the
password/key at the source) immediately, then remove it from history. Don't just
delete the line in a new commit — it's still in the git history.

---

## Where to host the `knowledge/` folder (optional)

Three sensible options:

- **Don't host it.** Keep it local as study material. Simplest.
- **Same repo, separate folder.** Fine, but a recruiter opening the repo sees teaching
  clutter. If you do this, say so in the README so the `build/`-vs-`knowledge/` split
  is clear.
- **A separate "learning-log" repo.** Nice if you want to show your learning journey
  publicly. The notebooks render directly on GitHub, so they're readable in the
  browser with no setup.

For a clean portfolio, host **`build/`** as its own repo and keep `knowledge/` local
or in a separate learning repo.

---

## Recap — what you now have hosted

- A public GitHub repo with a real data pipeline.
- A green **CI badge** proving every change is tested.
- **Branch protection** so broken code can't reach `main`.
- A live **GitHub Pages** dbt docs site.
- (Optional) a **scheduled** nightly run.

That is a genuinely strong, end-to-end portfolio piece — and every word of the resume
line ("CI/CD with GitHub Actions running automated tests, SQL linting, and dbt builds
on every commit") is now literally true of your repo.
