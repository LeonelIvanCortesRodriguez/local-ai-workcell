# Security boundary

This repository is a synthetic, one-computer simulation. Its input gate accepts only small SVG documents whose first text node is `SYNTHETIC DEMO`. Do not submit private files or operate the workflow with credentials, remote nodes, or production data.

The manifest contains the job ID and ordered state trail. The separate redacted event log contains states, phases, generic worker labels, and reason codes without a job ID or document text. Result files contain checksums, derived counts, and a manual-review flag. Local output is created in the directory chosen by the runner; that directory is excluded from the source package.

The project has no network client, authentication layer, or production deployment design. A security issue in a future public repository should be reported privately to its configured maintainer contact. No public contact endpoint is configured in this local candidate.
