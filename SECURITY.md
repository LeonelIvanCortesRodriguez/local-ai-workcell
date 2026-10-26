# Security boundary

This repository is a synthetic, one-computer simulation. Its input gate accepts only small SVG documents whose first text node is `SYNTHETIC DEMO`. Do not submit private files or operate the workflow with credentials, remote nodes, or production data.

The manifest contains the job ID and ordered state trail. The separate redacted event log contains states, phases, generic worker labels, and reason codes without a job ID or document text. Result files contain checksums, derived counts, and a manual-review flag. Local output is created in the directory chosen by the runner; that directory is excluded from the source package.

The v0.1 demo has no network client, authentication layer, or production deployment design. The separate v0.2 experiment accepts only the committed synthetic PNG fixtures and uses an ephemeral authentication key for local loopback worker registration. It has no TLS, remote-worker admission, arbitrary upload, or production deployment design. Its SQLite output stays in an ignored local directory.

The repository is public, but a private vulnerability reporting route has not yet been confirmed. Do not post credentials or private documents in a public issue. Enabling GitHub private vulnerability reporting is a publication follow-up for the owner; this file does not claim that it is already available.
