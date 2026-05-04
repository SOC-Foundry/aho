# W4 Audit Dispositions — 0.2.16

Audit archive: `artifacts/iterations/0.2.16/audit/W4.json`
Audit result: `pass`
Auditor: `gemini-cli`
Workstream scope: ADR-heavy close (re-scoped from cross-model cascade re-run +
Mercor reference pack assembly per the W4 launch brief). Three substantive
ADRs landed (0006 iteration deliverable discipline, 0007 containerization
architecture, 0008 dispatcher missing-model behavior); 0.2.16 retrospective,
0.2.17 plan opening with ADR 0006 convention, and 0.3 umbrella charter all
shipped. Cascade re-run + Mercor pack assembly graduated to future iterations
(see `acceptance/W4.json` → `scope_notes.rescope_disposition`).

The sealed acceptance archive `acceptance/W4.json` is not edited post-audit.
This note carries Kyle's dispositions on each AF finding verbatim, co-located
with the sealed archive so the record is self-describing at W4 close.

## Dispositions (verbatim)

- **AF001** (Deviation count coherence — `W4.json` documents 7 deviations
  from brief, drafter recap said 6) — accepted. Disposition: Acknowledged.
  Drafter recap was approximate; archive count is canonical. No action;
  archive is sealed; no carry-forward needed. Severity: info.

- **AF002** (CLI gap on `pending_audit` state — Pattern C state machine
  includes `pending_audit` but `aho iteration workstream` lacks an explicit
  subcommand) — accepted as carry-forward. Target: 0.2.x cleanup (specific
  iteration TBD; possibly 0.2.17 if it surfaces in containerization work,
  possibly its own future iteration). Future ADR candidate. Severity: info.
  Pairs with the analogous iteration-level CLI gap surfaced during 0.2.16
  iteration close (no `aho iteration close` subcommand for pre-confirm
  graduation-criterion verification); both gaps belong to the same future
  ADR's scope.
