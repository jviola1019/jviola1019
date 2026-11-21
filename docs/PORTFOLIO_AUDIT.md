# Portfolio audit and provenance

**Inspection date:** 2026-11-21. This document records what the profile README actually links and what is illustrative; it does not certify the predictive quality or deployment readiness of individual projects.

## Public-project curation

- **RAE** — public; product screenshot `fantasy_football_dashboard/.github/assets/hero.png` at commit `359c7d0a761e066f086b3a294346d5acaf995cfb`. Research headline remains constrained by the 115-draft holdout verdict.
- **REDRAFT** — public; the custom four-stage SVG is an *editorial process diagram*, never described as a screenshot. Release state is a research alpha; latest published release evidence reports failed statistical gates.
- **Gridiron Lab** — public; sourced football data, conditional retrospective evaluations and synthetic games must not be conflated. Model card and validation documents are the authoritative evidence.
- **EPOCH** — public; displayed screenshot `worldsim/docs/images/desktop-world.png` is anchored to `7547284b9f05576f37e9589194a07c418393c3ef`, the inspected source commit. Repository default branch at inspection was `claude/epoch-civilizations-unbound-dap8pc`.
- **Horrible Industries** — public; `assets/office.svg` is original illustrative artwork rather than a gameplay screenshot. Economic model is fictional.
- **NFL and NBA research / Gridiron DNA Lab** — public; included as supporting work, without invented success rates.

Private or unavailable repositories are deliberately excluded. Public status was checked using connected GitHub repository metadata, not assumed from a readable source file.

## Design and evidence controls

- Profile, REDRAFT process, and research-workflow SVGs are **original conceptual graphics**, supplied in dark and light versions. No chart represents an empirical result.
- RAE and EPOCH visuals are actual source-repository screenshots, anchored to inspected commits. There are no fabricated application captures.
- No remote JavaScript widgets, iframe content, custom script execution, visitor tracking, false CI badges or externally hosted font files.
- GitHub Markdown is the primary medium. Responsive picture sources provide separate mobile activity graphics, but GitHub rendering itself must still be checked manually in desktop/mobile dark and light themes.
- The manifest `data/projects.json` is the curated public-project allowlist for activity; a private repository must never be added to it. The rendered activity chart is a partial selection, not the entirety of account activity.

## Checks to reproduce

```sh
python3 scripts/check_profile.py
python3 -m py_compile scripts/render_activity.py scripts/check_profile.py scripts/test_activity.py
python3 -m unittest discover -s scripts -p 'test_*.py' -v
```

The refresh requires network access to GitHub's API and a token with appropriate public-metadata read access. Failure to retrieve a tracked repository should fail without overwriting the previous activity assets. Links to pinned screenshots should be checked before changing commit references.

## Review checklist

- [x] Remove dead/unavailable project links and exclude private work.
- [x] Preserve evidence disclosures and avoid unvalidated performance claims.
- [x] Show actual available screenshots with source provenance.
- [x] Provide descriptive image text and conceptual labeling.
- [x] Organize featured work for product, simulation, and modeling capabilities.
- [x] Provide light/dark design assets and a compact mobile activity version.
- [ ] Confirm final GitHub-rendered mobile/dark/light layouts by human visual inspection.
- [ ] Confirm workflow run results on the published revision.

The final two review items must not be marked complete merely because XML parsing or local tests passed.
