# Design system

## Direction

A process dossier rather than a monitoring dashboard. Keep the existing deep green and neutral identity, but replace the abstract hero and uniform metrics with a literal summary, a readable process graphic, and a specific synthetic result.

## Typography and density

Use the existing system sans stack. Body copy is normally at least 16px, supporting text at least 14px, and 12px only for nonessential metadata. Headings must fit at 390px without compressed tracking; code/checksum excerpts use a monospace face and wrap safely.

## Tokens and states

Define independent light and dark tokens for background, surface, ink, line, and the restrained green accent. Amber marks waiting/retry, red marks failed/unresolved, green marks delivered; text labels and distinct line patterns repeat the meaning. Important text and controls meet AA contrast in both themes.

## Spacing and layout

The first viewport contains one literal sentence, problem, route graphic, result summary, and inspect action. The route should remain readable at 1366x768 and stack into a linear sequence at 390x844. Avoid nested cards, ornamental KPI grids, and repeated eyebrow labels.

## Information graphic

Show Request → coordinator → capability selection → mock worker → artifact and evidence → validation → delivered. A separate visible branch shows WAITING_WORKER and RETRY_PENDING before return to routing. The graphic uses only states in the synthetic manifest and has an accessible name and adjacent text description. Evidence handoffs are named, not implied by decorative arrows.

## Motion and interaction

If motion is used, it explains a state transition and has a complete static equivalent. Respect reduced motion. The state trail uses native `details` with clear focus and a 44px summary target. The primary action links to the specific job trail or reproduction instructions.

## Responsive behavior and rejected patterns

Check 1440x900, 1366x768, 1024x768, and 390x844 in both themes. No horizontal overflow, tiny actor labels, auto-playing video, fake distributed metrics, mascot copy, or hover-only information.
