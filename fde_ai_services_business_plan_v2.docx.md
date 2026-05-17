![][image1]

**TachTech Engineering \- AI Security Services Business Plan (v2)**

**Secure-AI services for AI-native companies. Pillar-led delivery, embedded engineering, productized agentic platform.**

**The TL;DR**

**Forward Deployed AI Security Engineering.**

We are building a security-services firm purpose-built for AI-native technology companies ($20M-$300M revenue, agentic developer culture, AWS-plus-Snowflake-plus-GitHub estate) to assess, harden, and operate the security posture that the foundation-model labs and the SaaS platforms have left behind. Engagements are two-phase: a 14-day on-site Rapid Assessment & Incident Response, followed by a 9-week Pillar-Based Remediation organized along four pillars (Application, Identity, Observability, Endpoint). Every engagement converts to a 12-to-24-month AHO Managed Platform contract running TachTech's productized agentic-security stack inside the customer's cloud boundary.

**The unlock is the four-pillar pod model.** A pillar architect supports up to three concurrent Phase 2 engagements plus an unlimited number of Phase 3 managed accounts because the platform IP and the runbook library carry the marginal load. This is what separates us from a Big-4 staff-augmentation engagement (too slow, too generalist), a boutique pen-test firm (one finding, no platform), and an MSSP (alert routing only, no transformation).

**The platform IP is shipped, not roadmap.** SOC Alpha (a four-agent alert fidelity layer compressing alert volume 85-90% before it reaches an analyst or SOAR; production-deployed in both AWS and GCP variants), AHO (Kubernetes-native middleware orchestrating the full agentic-security stack), claude-otel (OpenTelemetry harness for AI-agent telemetry), RevOps (unified SOC operations platform), Falcon Manager Pro (production multi-tenant CrowdStrike management on GKE), panther-siem (detection-as-code library), mlPcapAnalyzer (network forensics toolkit), and the MITRE ATT\&CK Coverage Dashboard at tachtechlabs.com. Every platform is in customer hands and producing audit-grade evidence today.

**Security posture is the differentiator, not a feature.** Every engagement assumes the client is securing AI-native developer workflows and AI-native production systems, not adapting traditional controls to an AI surface. Our default architecture: data classification before design, least-privilege federated identity, DLP at the model boundary, full audit logging with HMAC integrity, human-in-the-loop on consequential agent actions. SOC 2 Type II within 18 months. The CISO and the auditor leave the engagement with the same evidence package.

**Cloud marketplaces are the accelerant.** Listing on AWS, Azure, and GCP lets clients burn down underutilized cloud commits on our services, shortening sales cycles 40-60% and unlocking co-sell with provider field teams. AWS by month 6, Azure by month 9, GCP by month 12\.

**Year-one target: 8-10 Phase 1 assessments converted to 6-8 Phase 2 engagements; $11M-$14M revenue; 3 AHO managed contracts signed; SOC 2 Type I attestation.** The single most important leading indicator is the first Phase 3 renewal, which should sign in month 21 and which proves the recurring book is durable.

**The window is 18 to 30 months** before the hyperscalers offer turnkey AI-agent governance, the Big 4 catches up on AI-incident IR, and the AI-native cohort starts hiring internal AI security leads. Speed matters. Reference-class wins matter more.

**Executive Summary**

We are building a security-services firm for high-velocity, AI-native technology companies, the Series B through Series D cohort building product on top of foundation models and shipping multiple times a day. Engagements are two-phase: a 14-day on-site assessment producing an auditor-grade roadmap mapped to SOC 2, ISO 27001, AWS FSBP, CIS Benchmarks, NIST 800-53, MITRE ATT\&CK and D3FEND; followed by a 9-week embedded remediation engagement organized along four pillars, each owned by a named senior architect with binding outcome acceptance criteria. Beyond Phase 2, the engagement converts to a 12-to-24-month managed platform contract that locks in recurring revenue and continuous detection-content uplift.

Our delivery unit is a pillar pod, not an individual. Pillar architects support multiple accounts because the pod owns shared tooling, a productized platform stack, reusable runbooks, and standardized acceptance-criteria frameworks. This is the economic unlock that separates us from a body-shop staff-aug firm and from a Big-4 practice that is structurally too expensive for the AI-native mid-market.

We believe the window for this firm is open for roughly 18 to 30 months. The IP is built, the methodology (Agentic Harness Orchestration, AHO) is proven in field engagements, and the first reference customer is already in delivery. The question is the velocity at which we convert reference-class wins into a repeatable engine.

**Market Opportunity**

The foundation-model labs (Anthropic, OpenAI, Google) and the major SaaS platforms (Snowflake, Datadog, GitHub) are racing to ship capability. Neither cohort is racing to help a 250-person AI-native technology company harden the developer estate that builds against those models, lock down the data plane that stores the customer evidence those agents reason over, or instrument the agentic workflows that have replaced the deterministic batch jobs of the prior generation. That gap is the opportunity, and it is widening.

The AI-native client cohort experiences pain in a specific sequence. The sequence is what makes the engagement model possible: each pain point creates demand for the next program, until the customer is on a managed platform with quarterly tuning.

1. **A real or imminent incident.** A supply-chain compromise of an AI tooling package, a stolen developer PAT pivoting into an over-privileged CI/CD secret, an agentic role with SELECT on a credentials table, a leaked Snowflake ACCOUNTADMIN session running mass SELECT \*. Major customers pause contracts. Revenue is at risk within days.

2. **An audit they cannot pass.** SOC 2 Type II in flight with 30-60 failing controls; a CIS Snowflake Foundations score with three FAIL-CRITICAL controls; an AWS FSBP standard at 60% pass with thousands of open Inspector vulnerabilities. The deal that closes this year is the one whose security review clears in days; the deal that does not close is the one stuck in security review for months.

3. **An AI surface they do not understand.** Engineers using Claude Code, Cursor, and Copilot at full saturation with no telemetry into what the agents are doing. Production agents accessing data warehouses with role grants nobody has audited. MCP servers connecting customer infrastructure to model providers without a defensible data-flow diagram, without a DLP layer at the model boundary, without an audit trail per tool call.

The three pain points compound. Our engagement is the one that addresses all three on a single shared timeline, with one weekly report that the CISO, the CFO, the CRO, and the auditor can each read for their own purposes.

**Ideal Customer Profile**

$20M-$300M annual revenue or recently raised Series B/C/D rounds with active enterprise sales motion; 100-1,500 employees with 30-60% engineering; AI-native product or AI-native developer culture; cloud estate centered on AWS with significant Snowflake or BigQuery footprint; identity stack on Okta or Entra; CI/CD on GitHub; recent breach, active enterprise security-review backlog, or CISO under board mandate to "own AI security."

Lead verticals: AI-native software and fintech, because reference selling compounds inside a vertical and security-review-as-purchase-gate is sharpest in those two cohorts. Healthtech, HR-tech, and legaltech follow once SOC 2 Type II \+ HIPAA Business Associate Agreements are in our delivery toolkit.

**The Three Service Programs**

The engagement archetype is **assess, embed, operate**. We package it as three named programs forming a single commercial funnel: Phase 1 qualifies, Phase 2 transforms, the managed program runs.

**Program 1 \- Rapid Assessment & Incident Response (Phase 1).** Two weeks, on-site, fixed-fee, four engineers. An Engagement Architect plus three pillar specialists embed inside the client's security and platform engineering organization on Day 1\. The 14-day shape is: on-site interviews and SIEM read on Days 1-4; tooling tenant reviews, data-plane audits, supply-chain forensics, and AI-agent surface inventory on Days 5-10; report writeup, executive read-out, and Phase 2 SOW build on Days 11-14.

The deliverable is a single auditor-grade integrated report covering: cloud security posture across AWS organization mapped to AWS FSBP, CIS, PCI DSS, NIST 800-53, and SOC 2 Type II; SIEM detection coverage gap analysis with attack-chain reconstruction (MITRE ATT\&CK and D3FEND mapped); identity surface least-privilege audit; supply-chain and CI/CD posture; data-plane audit (Snowflake or BigQuery role grants, masking policies, network policies, audit-log integrity); AI-agent surface inventory; SOC 2 / ISO 27001 audit gap with named owners; and the prioritized remediation roadmap (typically 50-80 numbered recommendations across 11-13 workstreams).

Phase 1 is **calibration plus commercial validation**. The client gets an auditor-grade artifact within 14 days. We get a fully-scoped Phase 2 SOW we can underwrite. Conversion rate to date is 100%. **Pricing: $150K-$250K**, delivered in 14 calendar days, on-site.

**Program 2 \- Pillar-Based Security Remediation (Phase 2).** Nine weeks, embedded, outcomes-based, four pillar architects plus a 2-3 engineer rotating bench. Each pillar carries a defined outcome schedule (8-12 outcomes per pillar plus 6-8 cross-cutting) with named accountable owners on both sides, defined success criteria mapped to compliance frameworks, and a binding acceptance gate at engagement close.

The four pillars are not a defense-in-depth restatement. Defense-in-depth is the attacker-facing narrative; the pillars are the **owner-facing narrative**. Each client team that has to execute work this quarter can read its pillar end-to-end and route every line item to a single accountable owner without translation. The auditor's walkthrough at engagement close is shorter for the same reason.

Cadence is fixed: a 30-minute Monday standup with security and engineering leadership; a Friday cross-architect synchronization; a single shared Linear board; one consolidated Friday written report distributed to client leadership and to TachTech's Director of Services. Every production-affecting change carries a change ticket, a log-mode-before-enforce window where applicable, a documented backout path, and multi-party approval. The cadence is what makes a 9-week timeline credible against 50-80 open recommendations. **Pricing: $850K-$1.6M**. Acceptance is metric-based; we do not bill hourly and we do not bill per ticket.

**Program 3 \- AHO Managed Platform & SOC Alpha (Annual Recurring).** Three tiers.

* **Foundation tier \- $360K/year.** SOC Alpha license, AHO platform license, monthly content updates, quarterly tuning, 24-hour SLA on critical issues.

* **Scale tier \- $720K/year.** Adds claude-otel fleet management, RevOps unified alert aggregation, 4-hour SLA, quarterly business reviews with security and engineering leadership.

* **Embedded tier \- $1.4M/year.** Adds named on-site engineer 2 days/week, quarterly red-team exercise, cross-tenant detection content access, annual penetration test of the AHO deployment.

A one-time 15-20% onboarding fee on the first-year managed contract covers platform deployment, customer-specific configuration, and runbook handoff. Renewals skip the fee.

A representative customer journey at the Scale tier: Phase 1 ($200K) \+ Phase 2 ($1.1M) \+ Phase 3 first year with onboarding ($846K) \+ Year 2 renewal ($720K) \+ Year 3 renewal ($720K) \= **$3.59M three-year customer value**.

**The Four-Pillar Delivery Framework**

The pillar framework is the IP that scales the firm. Each pillar carries a recurring outcome inventory across engagements; each is owned by a named senior architect; each maps cleanly to a single accountable client team.

**Pillar I \- Application Security.** Source code, CI/CD, IaC, container supply chain, AWS workloads, data plane. The recurring outcomes: GitHub Actions hardening (SHA-pinned actions, harden-runner with egress-block, gitleaks pre-commit, CodeQL default setup, PR-blocking SAST/DAST/SCA, CODEOWNERS catch-all, branch protection on main); internal artifact registry (CodeArtifact \+ ECR with cosign signing, SLSA L3 attestation, syft-generated SBOM, Kyverno admission control); Terraform Cloud governance (workspace-scoped RBAC, Sentinel policy-as-code, drift detection); AWS landing zone (Control Tower with mandatory SCPs, Audit Manager registered before deprecation deadline, Security Hub aggregating across regions, GuardDuty four protection plans, Access Analyzer org zone-of-trust, Inspector v2, Config aggregator); Snowflake data-plane lockdown (ACCOUNTADMIN at CIS threshold, account-level network policy, tag-driven masking, row-access policies); Cloudflare WAF in enforce mode.

The Pillar I evidence package reads to a SOC 2 Type II auditor: every PR is scanned for secrets in CI; PRs introducing HIGH or CRITICAL vulnerabilities are blocked; CodeQL and a third-party SAST run in parallel; every production image is scanned, signed via cosign, attested with SLSA Level 3 provenance, and SBOM-bound; Dependabot covers every service; Control Tower with mandatory SCPs governs the AWS landing zone; tag-driven masking and account-level network policy govern the data plane; the WAF is in enforce mode. Every clause is grounded in a workflow file, a Terraform module, a commit SHA, or a Snowflake policy DDL.

**Pillar II \- Identity Security.** Humans, service accounts, agents; credentials; authorization graph. The recurring outcomes: OIDC federation everywhere (GitHub Actions to AWS via OIDC with environment-scoped role ARNs, Snowflake WIF for service accounts, Vault JWT auth from CI); HashiCorp Vault as the production secrets platform with namespace-by-team-and-environment architecture, dynamic-engine-preferred ladder, rotation/TTL policy, Okta OIDC plus Control Groups for break-glass, HMAC-verified audit log; Snowflake identity hardening (admin count reduction, MFA enforcement, service-account WIF migration, JIT contractor accounts, dormant cleanup); just-in-time access program (standing high-privilege replaced by JIT elevation, multi-party approval on god-tier roles, documented break-glass tested quarterly); OIDC broker for AI agents (per-agent identity tokens with name, role, calling user, tight TTL, unlocking per-agent attribution for detection); unified HMAC audit pipeline; crown-jewel event catalog (versioned in monorepo, paged on every fire).

**Pillar III \- Observability Security.** SIEM and everything that feeds it; log-source health; correlation rules; cost monitoring; AI-telemetry pipeline. The recurring outcomes: SIEM detection coverage closure (every confirmed attack-chain stage carries HIGH or CRITICAL detection mapped to MITRE ATT\&CK Enterprise v15; alerting, signal, and correlation rules deployed as code); log-source health program; SOC Alpha alert-fidelity layer deployed inside the customer cloud boundary (four parallel agents producing 85-90% alert volume compression); claude-otel AI-agent telemetry instrumentation; RevOps unified alert aggregation across SIEM/EDR/CSPM; customer-owned vendor log pipeline (SNS-to-SQS distribution making vendor offboarding a routine change); Datadog cost discipline; MITRE ATT\&CK coverage visualization (live coverage heatmap); executive security dashboard.

**Pillar IV \- Endpoint Security.** Workstation as unit of trust; applications; network paths; content boundaries. The recurring outcomes: EDR fleet hardening (vulnerability scanning enabled, deep-visibility telemetry to SIEM, STAR-class rule lifecycle hygiene, Falcon Manager Pro for CrowdStrike multi-tenant management); Kandji managed-software policy (PR-reviewed allowlist, audit-and-remediate Custom Script payloads, drift detection); tiered patching cadence with severity-bound SLAs; Tailscale network-path enforcement to sensitive admin SaaS; browser-isolation 60-day bake-off (Island plus two alternates); Google Advanced Protection Program rollout; EDR profile validation pipeline for Linux developer machines (the falcon-sensor-uat Packer \+ QEMU \+ GCE golden-image factory pattern).

**Platform IP \- What We Deploy Inside the Customer**

The pillar framework is the engagement IP. The platform stack is the recurring-revenue IP. Sales should know each platform by name, by URL, and by what it replaces in the customer's stack.

* **SOC Alpha.** Four-agent alert classification (LLM rule-logic, vector-search historical context, change correlation, statistical outlier) deployed inside the customer cloud boundary, downstream of their SIEM. Compresses alert volume 85-90% before reaching an analyst or SOAR. Run-rate cost envelope \~$635-$1,080/month at 60K alerts/month, one to two orders of magnitude below commercial alert-triage SaaS. AWS-native and GCP-native variants in production. Reference: github.com/TachTech-Engineering/socalpha1.

* **AHO (Agentic Harness Orchestration).** Kubernetes-native middleware orchestrating the full agentic-security stack as a single deployable platform. Per-tenant namespace isolation, AHO operator reconciling agent deployments, control plane orchestrating the SOC Alpha synthesis workflow, GitOps configuration via Flux or Argo CD, per-tenant evidence package generation for SOC 2/ISO 27001/CIS. Built on the production K8s deployment know-how from Falcon Manager Pro on GKE.

* **claude-otel.** OpenTelemetry harness for Claude Code and other agentic developer tools. Captures agent turns, tool invocations, full API responses, per-session totals (cost, tokens, cache hits, MCP server state). Three-format output (TSV, Markdown, JSONL with inlined response bodies). Verified on Linux and macOS arm64.

* **RevOps.** Unified SOC operations platform aggregating Panther, CrowdStrike, SentinelOne, Microsoft Defender, AWS Security Hub, Wiz, GuardDuty into one analyst surface. AI-powered alert clustering, Monaco-based rule editor, SPL-to-Panther converter, rule-health dashboard, case management, threat-intel feed ingestion. Reference: github.com/TachTech-Engineering/revops.

* **Falcon Manager Pro.** Production multi-tenant CrowdStrike Falcon detection management platform on GKE behind Cloudflare with Strict TLS. React \+ Flask, FalconPy SDK, FQL search, hash-based bulk operations, MITRE ATT\&CK auto-mapping. Live at falconmanagerpro.com.

* **panther-siem.** TachTech's contributed Panther detection content. Detection-as-code library covering AWS, GitHub, Okta, Snowflake, Vault, GuardDuty, SentinelOne, CrowdStrike. Customer monorepo gets a TachTech-authored fork at engagement start; cross-tenant content updates flow through the Phase 3 managed contract. Reference: github.com/TachTech-Engineering/panther-siem.

* **mlPcapAnalyzer.** Scapy-based network forensics toolkit for threat hunting and beacon detection. Identifies cleartext HTTP/FTP/Telnet/SMTP/DNS/POP3/IMAP traffic, generates timestamped Markdown reports, performs CoV-based beacon detection. Dockerized for SOC analyst onboarding.

* **MITRE ATT\&CK Coverage Dashboard.** Flutter Web application rendering full ATT\&CK Enterprise matrix with live coverage heatmapping from CrowdStrike correlation rules, IOA rules, and alerts. Live at tachtechlabs.com (currently 351 techniques covered, 74% coverage).

* **Kubernetes tooling portfolio.** kubectl-neat, kubectl-whoami, rbac-lookup; plus the falcon-sensor-uat Packer \+ QEMU \+ GCE golden-image factory for EDR sensor RFM certification on Linux developer machines (Arch, CachyOS, Ubuntu LTS).

**Methodology \- Agentic Harness Orchestration (AHO)**

The engagement velocity we commit to (50-80 recommendations remediated in 9 calendar weeks across four concurrent pillars) is the product of a delivery methodology that uses agent-orchestrated workflows for the work that scales linearly with effort, freeing the architect's time for the work that scales superlinearly with judgment.

AHO has three load-bearing properties: (1) a phase-iteration-run versioning scheme that maps every commitment to an acceptance gate; (2) an agent-augmented architect role that produces 2x-3x the engineering throughput of an architect on the same problem without the agent harness; (3) a continuous self-observation loop where every artifact carries its own observability.

The methodology is the IP that survives engagement closeout. The customer can run their next pillar of work to the same discipline whether TachTech is in the room or not. That property is what makes the customer's exit option a real option, which is what makes the renewal decision a real decision rather than a captive one.

**Security Posture \- Built In, Not Bolted On**

Every engagement assumes the client is securing AI-native developer workflows and AI-native production systems, not adapting traditional controls to an AI surface. AI agents are a fundamentally new category of security risk: they touch sensitive data, make autonomous decisions, call APIs on behalf of humans, and operate across system boundaries that traditional security tooling was never designed to watch. Most of the market will learn this the hard way through breaches, data leaks, and regulatory actions.

The default architecture we deploy: **data classification before design** (every workflow gets a data inventory before build, with a data handling specification every engineer references); **least-privilege federated identity** (scoped credentials, no long-lived keys, OIDC everywhere); **DLP at the model boundary** (redaction and classification before any data reaches a foundation model; ZDR-routed model calls for regulated data); **output filtering and guardrails** (declarative, version-controlled DLP on agent outputs; an agent drafting a customer email cannot accidentally include an SSN pulled from an internal record); **full audit logging** with HMAC integrity on every producer; **human-in-the-loop by default** for consequential actions (the agent's autonomy boundary is a customer risk-tolerance decision, not an engineer's ambition); **prompt injection and jailbreak defense** (input sanitization, output validation, tool-call restrictions, anomaly monitoring); **secrets management in Vault** with rotation, no commits, no logging.

Our own house: SOC 2 Type II within 18 months, HIPAA readiness by year two, background checks and offboarding discipline, separation of duties inside the pod, incident response plan with quarterly tabletop exercises, annual third-party pentest of our internal platform and a representative customer deployment. In regulated verticals (financial services, healthcare, insurance), security posture is often the decisive factor in vendor selection. Two vendors with similar technical proposals but different security postures are not in the same competitive bracket. The one with the mature security story wins, and wins at higher prices.

**Pricing and Packaging**

The default contract pattern is two-phase services followed by a managed annual contract. We do not bill hourly. We do not bill per ticket. We do not bill per agent built. The annual managed contract is paid quarterly; Phase 1 and Phase 2 are paid on milestone acceptance.

Hourly billing caps gross margin at consulting-shop economics and incentivizes the wrong delivery behavior on both sides. Per-outcome billing during Phase 2 incentivizes scope-cutting on the customer side and outcome-padding on the delivery side. The annual managed contract aligns the firm with long-term customer outcomes and protects the platform-leveraged unit economics that justify the firm's existence as a going concern.

Discount discipline: no off-list discounting on Phase 1 or Phase 2\. Phase 3 carries a multi-year discount (12% on a 24-month contract, 18% on a 36-month contract) deployed selectively. Marketplace fees compress gross margin by \~3-5% per deal; we do not discount off list to compensate because the commit-burn dynamic on the customer side already covers the differential.

**Go-to-Market**

The fastest path to first revenue is direct founder-led sales into the chosen verticals, leveraging existing relationships in the AI-native cohort and the broader cybersecurity executive community. The motion is familiar: multi-stakeholder, champion-driven, executive sponsor required, technical-buyer-and-budget-buyer split common.

Beyond founder-led sales, four channels matter:

**Vertical conferences.** Each target vertical has two or three must-attend events. AI-native software has Defcon, Black Hat, RSA, the AI Engineer Summit, and the Anthropic / OpenAI / hyperscaler developer conferences. Fintech has Money 2020, Finovate, FS-ISAC. Sponsored roundtables and speaking slots are how mid-market executives discover new categories of vendor. Slow-build but compounds.

**Reference selling within verticals.** Once two or three reference customers exist within a vertical, every subsequent deal in that vertical closes 30-40% faster. The reference customers are packaged into named, sanitized, customer-approved case studies. The case study set is the leading indicator of commercial leverage in year two.

**Strategic partnerships.** Anthropic (the AI-native cohort's primary model provider; partnership target month 9), CrowdStrike (Falcon Manager Pro as the multi-tenant management plane; month 12), Panther Labs (every engagement uses or installs Panther; month 6 \- this is an early, fast partnership), Snowflake (the data-plane work is a high-stakes Pillar I outcome; month 9). Secondary partnerships develop opportunistically: HashiCorp, Wiz, Datadog, GitHub, Cloudflare, Tailscale, Kandji.

**Cloud marketplaces.** Listing on AWS, Azure, and GCP. The mid-market AI-native cohort is disproportionately likely to be running behind their EDP/MACC/GCP commit draw-down curve. A 12-month managed contract in the $360K-$1.4M range is a near-perfect burn vehicle: large enough to materially move commit consumption, small enough to clear procurement without board approval. Marketplace-purchased services close 40-60% faster than traditional procurement.

Sequencing: AWS first (most mature services marketplace, highest co-sell density), Azure second (strongest co-sell motion via the Microsoft AI Cloud Partner Program), GCP third (smaller mid-market base but high-fit on technology-adjacent customers because of Vertex AI). AWS by month 6, Azure by month 9, GCP by month 12\.

The marketplace listing is necessary but insufficient. The real value is the co-sell relationship with the cloud provider field teams. We hire a Cloud Alliances lead by month 12 to 15 whose sole job is managing these relationships and pulling co-sell opportunities into the pipeline.

Paid digital marketing should not be expected to work at our deal sizes in years one and two. The buyers discover us through their professional network and through the conferences.

**Team and Hiring Plan**

**Year 1, months 0-3.** Founders (commercial and technical), three pillar architects (Application, Identity, Observability), an Endpoint specialist contractor on retainer, two engineering bench resources, one Director of Services. Enough to run two to three concurrent engagements at staggered start dates and build the platform IP at production grade.

**Year 1, months 3-9.** Add Endpoint pillar architect full-time. Add two more bench engineers. Add the first Account Manager. Add a Detection Engineering specialist owning the cross-tenant content library.

**Year 1, months 9-12.** First dedicated seller. Cloud Alliances lead. Platform Engineering specialist owning AHO production operations.

**Year 2\.** Second seller; Vertical Specialists for AI-native software and fintech; Head of Engineering owning the platform IP roadmap; Data Engineering specialist for the SOC Alpha agent stack and embedding/vector-store pipeline; Linux endpoint specialist for the falcon-sensor-uat pattern at scale.

The hiring bar: pillar architects at the senior-staff or principal engineer level, comparable to where the customer's own platform engineering organization hires; bench engineers at senior level with one specialty and rotation flexibility; Account Managers from enterprise cybersecurity sales backgrounds; sellers as quota-carrying enterprise sellers with prior experience in AI/ML or cloud-native security. The worst hire for the firm is a brilliant engineer who resents customer presence; the best hire is a good engineer who sees the customer relationship as part of the system being designed.

Compensation: pay top-of-market base plus meaningful equity. The pillar architect is the role that creates the firm's IP; they should be compensated as IP creators, not as billable resources.

**Financial Model \- Starting Assumptions**

Fully loaded engineer cost (salary, benefits, equity, tooling, on-site travel, overhead): \~$290K/year for bench engineers, \~$390K for pillar architects, \~$440K for Director-and-above.

A representative year-one portfolio: 10 Phase 1 engagements at $200K average ($2.0M, 55% gross margin); 8 Phase 2 conversions at $1.1M average ($8.8M, 44% gross margin); 3 Phase 3 partial-year contracts at the Scale tier ($540K, 65% gross margin). **Year-one total revenue: \~$11.3M; year-one gross margin: \~$5.3M (47%).** Sales and marketing at \~25% of revenue, G\&A at \~15%, R\&D at \~12%. Year-one operating margin break-even to mildly negative, which is correct: the firm is investing in platform IP and year-two scaling preparation.

**Year 2: 18-24 customers, $10M-$14M revenue, recurring book at 25%; operating margin 8%-14%.** **Year 3: 35-45 customers, $20M-$28M revenue, recurring book at 35%; operating margin 18%-24%.**

The single most-sensitive number in the model is **pillar-architect utilization**. Every 10 percentage points of utilization swings net margin by \~8 points. Target: 60-65% in year one, 65-70% in year two, 70%+ in year three with platform IP carrying the marginal load. Tracking weekly is non-negotiable.

**Risks and Mitigations**

**Commoditization by large consultancies.** Accenture, Deloitte, EY, KPMG, IBM Security are all building AI security practices fast. Our defense is speed, vertical depth, productized platform, and operate-and-maintain economics they cannot price competitively against the AI-native mid-market. Their structural cost base is double or triple ours; the day they target our deal sizes is the day their utilization model breaks.

**Foundation-model disintermediation.** Easier building creates more agents, more attack surface. Our moat is not building agents; it is running agentic-security platforms reliably at scale. As models improve, our per-engagement cost drops and our margins expand.

**Hyperscaler turnkey AI security.** Multi-cloud SOC Alpha (AWS and GCP today, Azure roadmap), multi-vendor RevOps consolidation, and embedded transformation work the hyperscalers do not provide. The hyperscaler relationship is co-sell, not displacement; their platform makes our integration work easier, not harder.

**Customer in-housing.** 20-30% of customers will internalize. Counter: move upmarket faster than they can hire; maintain cross-tenant detection content advantage; price the managed engagement such that fully-loaded internalization is more expensive than continuing.

**AI-agent reliability and security incidents inside our deployments.** The platform architecture is isolated to the customer cloud boundary; every action logged with tamper-evident retention; secrets in Vault with customer-managed keys; quarterly drills against our own platform; E\&O and cyber insurance with limits matching the largest contract values. A single well-handled incident in year two strengthens reputation; a poorly-handled one ends the firm.

**Key-person risk.** Platform IP and runbook library are the structural counter; every architect can pick up any customer because nothing in the engagement is bespoke at the platform level.

**Detection-content staleness.** The cross-tenant detection content library is load-bearing; the Detection Engineering specialist's KPIs are coverage against published MITRE ATT\&CK update cadence and against incident-pattern data from our customer experience.

**Foundation-model provider dependency.** The internal platform abstracts provider choice behind a TachTech-controlled interface; self-hosted Ollama models in the SOC Alpha agent stack ensure the substrate is not single-provider-dependent.

**Regulatory action against AI-agent deployments.** EU AI Act, US state-level AI regulation, sector-specific regulation. Forward regulatory posture is part of the platform IP roadmap; regulatory tracking is a Director-of-Services-level responsibility.

**Eighteen-Month Milestones**

**Month 3\.** First three Phase 1 engagements complete. First two Phase 2 engagements signed. Initial outcome inventory templates per pillar shipped. Initial AHO \+ SOC Alpha v1 deployment in the first customer environment. SOC 2 Type I engagement kicked off.

**Month 6\.** Six Phase 1 complete; four Phase 2 active. Panther Labs partnership signed. AWS Marketplace live. First reference case study published. SOC 2 Type I attestation achieved. Detection content library v1 with 200+ rules.

**Month 9\.** Eight Phase 1 complete; six Phase 2 active or completed; first Phase 3 contract signed. Anthropic and Snowflake partnerships signed. Azure Marketplace live. SOC 2 Type II audit window started.

**Month 12\.** Ten Phase 1 complete; eight Phase 2 completed; three Phase 3 contracts signed. CrowdStrike partnership signed. GCP Marketplace live. AHO platform v2 released (multi-tenant Helm with GitOps deployment). Year-one revenue at $11M-$14M.

**Month 15\.** 12-15 active customers. Vertical Specialists hired. AHO platform v3 released (Azure variant of SOC Alpha shipped). SOC 2 Type II attestation achieved.

**Month 18\.** 18-24 active customers. $14M+ trailing-twelve-month revenue. Recurring book at 22%+ of revenue. Detection content library v3 with 1,500+ rules. Customer advisory board operational with 8-10 customers.

**Open Questions for Leadership**

Before sharpening this plan into the version we pitch externally, leadership should work through:

* Which sub-vertical within "AI-native software" gets the first Vertical Specialist hire? The first reference customer's vertical disproportionately governs the next five.

* Capitalization plan: bootstrapped, friends-and-family, seed round, growth round? Platform engineering investment ($2M-$3M) compresses to months 0-9 if seed-funded, spreads across years one and two if bootstrapped.

* Founder split: who owns commercial; who owns technical and platform; who owns the AHO roadmap; who owns the first ten customer relationships; who owns hiring decisions through the first twenty hires.

* IP ownership and contract structure: TachTech retains platform IP (AHO, SOC Alpha, claude-otel, Falcon Manager Pro, RevOps, mlPcapAnalyzer) and the cross-tenant runbook and detection libraries; customer owns customer-specific configuration and detection content authored against their environment. Contract language needs to be precise.

* The first five reference customers: 10-15% off list across Phase 1 \+ Phase 2 in exchange for explicit reference rights and case-study participation. Reference value exceeds discount cost by an order of magnitude.

* Geographic strategy: US-first; UK and EU in year three; APAC in year four. The on-site requirement may relax for Phase 3, expanding the addressable market materially.

* Acquisition optionality: large consultancies, hyperscalers, security-platform companies in years three through five. Platform IP drives the multiple; customer relationships drive the certainty.

**Appendix \- Public Capability Inventory**

| Capability | URL | Summary |
| :---- | :---- | :---- |
| TachTech Labs (ATT\&CK Dashboard) | tachtechlabs.com | Live MITRE ATT\&CK Enterprise coverage heatmap |
| Falcon Manager Pro | falconmanagerpro.com | Production multi-tenant CrowdStrike management on GKE |
| SOC Alpha (GCP variant) | github.com/TachTech-Engineering/socalpha1 | Four-agent SOC alert triage on GCP |
| RevOps | github.com/TachTech-Engineering/revops | Unified Security Operations Platform |
| panther-siem | github.com/TachTech-Engineering/panther-siem | Panther detection content library |
| mlPcapAnalyzer | github.com/TachTech-Engineering/mlpcapanalyzer | Scapy-based network forensics toolkit |
| falcon-sensor-uat | github.com/TachTech-Engineering/falcon-sensor-uat | RFM certification pipeline for Falcon on Arch Linux |
| kubectl-neat / kubectl-whoami / rbac-lookup | github.com/TachTech-Engineering | Kubernetes utility portfolio |

[image1]: <data:image/png;base64,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>