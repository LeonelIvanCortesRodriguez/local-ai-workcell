# v0.2.0 release procedure

This procedure governs the combined v0.1 walkthrough and v0.2 synthetic process proof. The earlier public baseline was not tagged or released as `v0.1.0`, so no retroactive release is implied. `pyproject.toml` identifies this source as `0.2.0`. Create the `v0.2.0` GitHub release only after the checks below pass on the committed source.

## Gate and package

From the repository root, with Python 3.11+ and Tesseract installed, run the tests on the exact candidate commit. On Windows PowerShell:

```powershell
$env:WORKCELL_V2_INTEGRATION = '1'
python -m unittest discover -s tests -v
python tests/mutation_check.py
python scripts/privacy_scan.py
python scripts/refresh_demo.py
git diff --exit-code -- index.html
python -m workcell.cli demo --output out-v1
python -m workcell.cli verify --output out-v1
python -m workcell.v2 demo --output out-v2
python scripts/package.py --output release
Get-FileHash -Algorithm SHA256 release/local-ai-workcell-public.zip
Get-FileHash -Algorithm SHA256 release/CONTENT_INVENTORY.sha256
```

Use absent or empty `out-v1`, `out-v2`, and `release` directories. Record the two hashes and compare every `CONTENT_INVENTORY.sha256` entry with the ZIP member bytes. Confirm that the public ZIP has only fictional fixtures and no generated SQLite queue. The GitHub Actions matrix for Python 3.11–3.14 must pass on the committed candidate before publishing the release; a local run alone does not satisfy this gate.

## Publish only after approval

1. Review the candidate diff, commit the accepted source with the `Leonel` project noreply identity, and push that exact commit to `main` after publication is authorized.
2. Wait for all four GitHub Actions matrix jobs at that commit to pass. If any job fails, keep the release unpublished and fix the source in a new reviewed candidate.
3. Regenerate the package from that commit and verify that its ZIP and inventory hashes match the accepted candidate. Create an annotated `v0.2.0` tag on the verified commit and push the tag.
4. In the repository's GitHub Releases UI, create a `v0.2.0` release from that tag. Attach exactly `local-ai-workcell-public.zip` and `CONTENT_INVENTORY.sha256`; put both SHA-256 values in the release notes. Explain that v0.1 is the static walkthrough and v0.2 is a local synthetic process proof, with no remote-node claim. Check both downloaded assets against the recorded hashes before announcing the release.
5. Confirm the Pages URL displays the accepted `index.html` and that its v0.2 method/report links resolve. Add the Pages URL to the repository website field and relevant topics only with the same publication authorization.

The badge in README reflects GitHub's actual workflow state. Confirm it points to the same commit before creating the release.

## Rollback

Keep the accepted candidate ZIP, inventory, tag commit, and the previous published commit recorded in the handoff. If a released page or package fails, revert the release commit on `main` and push the revert after review; Pages will return to the prior content when its build completes. Mark the affected GitHub release as withdrawn or superseded in its notes while preserving the tag and assets for traceability. A corrected release gets a new version and a fresh audit; do not replace the assets behind an existing checksum.
