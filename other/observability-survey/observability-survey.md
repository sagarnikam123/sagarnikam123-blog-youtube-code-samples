# Observability Survey

> **Purpose:** Understand how engineering and product teams currently use observability tools, identify key pain points, and gather concrete requirements to modernize our observability stack.  
> **Target Audience:** Software Engineers, Tech Leads, Engineering Managers, DevOps / SRE, QA, Product Managers.  
> **Format:** Google Forms / Microsoft Forms (with conditional branching).  
> **Estimated Time:** 8–10 minutes core; 12–15 minutes with optional Sections 5–9.  
> **Form Builder Note:** Enable *"Go to section based on answer"* for Q1 to streamline paths for non-engineering roles.
> **Last Updated:** 29-08-2026
---

## Section 1: About You

1. **What is your primary role?** *(Single choice)*
   - Software Engineer / Developer
   - Senior / Staff / Principal Engineer
   - Tech Lead / Engineering Manager
   - DevOps / SRE / Platform Engineer
   - QA / Test Engineer
   - Product Manager *(Form Tip: Skip Sections 5 (Alerting) & 6 (OTel & Instrumentation); Sections 7–8 are still relevant)*
   - Other: ___

2. **Which team / department do you belong to?** *(Short answer, optional)*
   - [ Free text ]

3. **How long have you been with the company?** *(Single choice)*
   - Less than 6 months
   - 6 months – 1 year
   - 1 – 3 years
   - 3+ years

4. **How would you rate your familiarity with observability concepts (logs, metrics, traces, profiling)?** *(Linear scale 1–5)*
   - 1: Beginner (Aware of concepts, rarely use tools directly)
   - 2: Basic (Check basic logs/dashboards when pointed to them)
   - 3: Intermediate (Regularly query logs, metrics, and traces for debugging)
   - 4: Advanced (Build custom dashboards, alerts, and instrument applications)
   - 5: Expert (Design distributed observability architectures and data pipelines)

5. **When you joined, how easy was it to get access and documentation for our observability stack?** *(Single choice — Form Tip: Use Multiple Choice rather than Linear Scale to accommodate the N/A option)*
   - 1 - Very difficult (unclear access process, missing docs)
   - 2 - Difficult (took significant time/tickets)
   - 3 - Neutral / Figured it out with peer help
   - 4 - Easy (clear docs and quick access)
   - 5 - Very easy (seamless self-service onboarding)
   - N/A (Was here prior to current setup)

---

## Section 2: Current Observability Usage & Tool Breakdown by Signal

6. **Which observability capabilities do you actively use today?** *(Select all that apply)*
   - [ ] Backend Logs (Application, system, audit)
   - [ ] Infrastructure & Application Metrics (CPU, memory, custom business metrics)
   - [ ] Distributed Traces (APM, end-to-end request tracing)
   - [ ] Continuous Profiling (CPU/memory flame graphs, thread dumps)
   - [ ] Database & Middleware Observability (RDS, DynamoDB, Kafka, Redis metrics & slow queries)
   - [ ] Frontend / Real User Monitoring (RUM, Web Vitals, browser errors)
   - [ ] Synthetic / Uptime Monitoring (Health checks, API pingers)
   - [ ] CI/CD & Build Pipeline Observability (Test metrics, deploy tracking)
   - [ ] Alerting & Dashboards
   - [ ] None of the above

7. **In which environments do you primarily rely on observability tooling?** *(Select all that apply)*
   - [ ] Production
   - [ ] Staging / Pre-prod / UAT
   - [ ] Development / Sandbox
   - [ ] Local environment debugging

8. **How frequently do you interact with observability tools?** *(Single choice)*
   - Multiple times a day
   - Daily
   - A few times a week
   - Only during incidents / outages
   - Rarely / Never

9. **Which tool(s) do you currently use for LOGS?** *(Select all that apply — Form Tip: optionally add a follow-up single-choice for primary tool)*
   - [ ] Amazon Managed Grafana (AMG) / Loki
   - [ ] Self-hosted / OpenSource Grafana + Loki
   - [ ] AWS CloudWatch Logs
   - [ ] OpenSearch / Elasticsearch / Kibana
   - [ ] Apache SkyWalking (Log Analysis)
   - [ ] Datadog Logs
   - [ ] Direct CLI / Console output (`kubectl logs`, `docker logs`, stdout)
   - [ ] I do not query/view logs
   - [ ] Other: ___

10. **Which tool(s) do you currently use for METRICS & DASHBOARDS?** *(Select all that apply — Form Tip: optionally add a follow-up single-choice for primary tool)*
    - [ ] Amazon Managed Grafana (AMG) + Prometheus
    - [ ] Self-hosted / OpenSource Grafana + Prometheus
    - [ ] Grafana + VictoriaMetrics
    - [ ] AWS CloudWatch Metrics
    - [ ] Apache SkyWalking (Metrics & Topology)
    - [ ] Datadog Metrics & Dashboards
    - [ ] I do not query/view metrics
    - [ ] Other: ___

11. **Which tool(s) do you currently use for TRACES & APM (Distributed Tracing)?** *(Select all that apply — Form Tip: optionally add a follow-up single-choice for primary tool)*
    - [ ] Apache SkyWalking
    - [ ] Grafana Tempo (AMG or Self-hosted)
    - [ ] Jaeger
    - [ ] AWS X-Ray
    - [ ] Datadog APM / Tracing
    - [ ] OpenTelemetry Collector + Custom Exporter
    - [ ] Zipkin
    - [ ] I do not use distributed tracing / APM
    - [ ] Other: ___

12. **Which tool(s) do you currently use for CONTINUOUS PROFILING & DEEP DEBUGGING?** *(Select all that apply)*
    - [ ] Grafana Pyroscope
    - [ ] Apache SkyWalking Profiling
    - [ ] Datadog Continuous Profiler
    - [ ] JVM Tools (`async-profiler`, `jstack`, heap/thread dumps)
    - [ ] Go `pprof`
    - [ ] Python profilers (`py-spy`, `cProfile`)
    - [ ] I do not use profiling tools
    - [ ] Other: ___

13. **Which tool(s) do you currently use for FRONTEND / REAL USER MONITORING (RUM) & ERROR TRACKING?** *(Select all that apply)*
    - [ ] Sentry
    - [ ] AWS CloudWatch (Synthetics / RUM)
    - [ ] OneUptime
    - [ ] Datadog RUM / Browser Monitoring
    - [ ] LogRocket / Bugsnag
    - [ ] Firebase Crashlytics / Google Analytics
    - [ ] Custom in-house logging / API error logs
    - [ ] I do not monitor frontend/client-side apps
    - [ ] Other: ___

14. **What format are your application logs in?** *(Select all that apply)*
    - [ ] **Structured JSON** (e.g., `logstash-logback-encoder`, Log4j2 `JsonTemplateLayout`, ECS / Elastic Common Schema)
    - [ ] **Standard Logback / Log4j Pattern Layout** (e.g., `%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger - %msg`)
    - [ ] **MDC / Context-Enriched Text** (Pattern text containing Mapped Diagnostic Context tags like `[traceId=..., spanId=..., tenantId=...]`)
    - [ ] **Key-Value / Logfmt** (e.g., `timestamp=... level=INFO service=auth-service trace_id=... msg="..."`)
    - [ ] **Unstructured / Free-form Plain Text** (Custom print statements, raw text output)
    - [ ] **Web / Access Log Format** (e.g., Spring Boot / Tomcat access logs, Common/Combined Log Format)
    - [ ] **Multiline Raw Stack Traces** (Standard Java `Throwable.printStackTrace()` across multiple lines)
    - [ ] **Mixed formats** across different microservices / legacy modules
    - [ ] I don't know
    - [ ] Other: ___

---

## Section 3: Pain Points & Debugging Bottlenecks

15. **What are your biggest pain points with the current observability setup?** *(Select up to 4 — Form Builder Tip: Enable response validation "Select at most 4")*
    - [ ] Tool sprawl & fragmented workflows (switching between too many tabs/tools)
    - [ ] Hard to correlate logs, metrics, and traces for a single request/incident
    - [ ] Slow query performance / timeouts on dashboards and log queries
    - [ ] Broken or split multiline Java stack traces / unparsed exception logs
    - [ ] Missing or dropped data (data gaps, incomplete traces, dropped logs)
    - [ ] Ingestion latency (logs/metrics take minutes to show up after an event)
    - [ ] Too many noisy / non-actionable alerts (alert fatigue)
    - [ ] Missing critical alerts / finding out about outages from users first
    - [ ] Complex query syntax (e.g., PromQL, LogQL) with high learning curve
    - [ ] Lack of self-service (need tickets/permissions to create dashboards or add telemetry)
    - [ ] Lack of documentation, runbooks, and training
    - [ ] Short data retention limits (data expires before analysis is done)
    - [ ] Lack of clear dashboard and alert ownership (stale or broken dashboards)
    - [ ] High or untracked infrastructure/SaaS cost
    - [ ] Other: ___

16. **How long does it typically take you to identify the root cause of an incident?** *(Single choice)*
    - < 5 minutes
    - 5 – 15 minutes
    - 15 – 30 minutes
    - 30 – 60 minutes
    - 1 – 2 hours
    - > 2 hours
    - Usually require escalation / cannot solve independently

17. **How quickly do telemetry data (logs/metrics/traces) become queryable after generation?** *(Single choice)*
    - Real-time (< 30 seconds)
    - Near real-time (30 seconds – 2 minutes)
    - Delayed (2 – 5 minutes)
    - Significantly delayed (> 5 minutes)
    - I don't know / haven't measured

18. **Describe the single most frustrating bottleneck when debugging issues with our current tools:** *(Open text, optional)*
    - [ Free text ]

---

## Section 4: Future Requirements & Platform Preferences

19. **What are your top priorities for improving our observability stack?** *(Select up to 3 — Form Builder Tip: Enable response validation "Select at most 3")*
    - [ ] Unified "Single Pane of Glass" (correlated logs, metrics, traces, and deploy events in one UI)
    - [ ] Sub-second search & fast query performance
    - [ ] Real-time log tailing and live stream debugging
    - [ ] High-quality out-of-the-box dashboards for our common tech stack
    - [ ] Actionable alerting with integrated runbook links and PagerDuty/Slack routing
    - [ ] Turnkey OpenTelemetry (OTel) auto-instrumentation
    - [ ] Frontend Real User Monitoring (RUM) & web performance tracking
    - [ ] AI-driven anomaly detection & automated root cause recommendations
    - [ ] Transparent cost and usage visibility per team/service
    - [ ] Self-service telemetry pipeline configuration (sampling, filtering, masking)

20. **Platform Architecture Preference:** *(Single choice)*
    - Strongly prefer a **Single Unified Platform** (e.g., all signals inside Grafana Stack or Datadog)
    - Moderately prefer a **Single Unified Platform**
    - Neutral / No preference
    - Moderately prefer **Best-of-Breed Specialized Tools** for each signal
    - Strongly prefer **Best-of-Breed Specialized Tools**

21. **What level of self-service do you expect?** *(Single choice)*
    - **Full Self-Service:** I configure instrumentation, queries, dashboards, and alerts directly via code/UI.
    - **Guided Self-Service:** Platform team provides templates, Terraform modules, and SDK wrappers; I deploy and tweak.
    - **Managed Service:** Platform team builds and maintains all dashboards, alerts, and pipelines on request.

22. **For each activity below, what is your appetite and current ability to do it yourself?** *(Matrix — Google Forms: Multiple-choice grid | MS Forms: Likert. One choice per row)*
    | Activity | Want to & already do it myself | Want to, but lack access/skills today | Prefer the platform team does it | Not relevant to my role |
    |---|---|---|---|---|
    | **Create / edit dashboards** | ◻ | ◻ | ◻ | ◻ |
    | **Create / edit alerts & alert rules** | ◻ | ◻ | ◻ | ◻ |
    | **Add / change instrumentation (logs, metrics, traces) in my code** | ◻ | ◻ | ◻ | ◻ |
    | **Configure telemetry pipeline (sampling, filtering, routing, masking)** | ◻ | ◻ | ◻ | ◻ |
    | **Manage data retention / storage policy for my services** | ◻ | ◻ | ◻ | ◻ |

    > *"Want to, but lack access/skills today" is the key gap — it tells us where to grant access or run enablement.*

23. **Do you currently have visibility into your team's observability costs / data ingestion volume?** *(Single choice)*
    - Yes, we actively monitor and optimize our usage & cost (with tags/dimensions)
    - Rough awareness, but no exact numbers or per-service cost breakdown
    - No visibility, but would like to know
    - No visibility / not relevant to my role

24. **How long do you need each telemetry signal retained (queryable) to do your job?** *(Matrix — Google Forms: Multiple-choice grid | MS Forms: Likert. One choice per row)*
    | Signal | < 7 days | 7–30 days | 1–3 months | 3–6 months | 6–13 months | > 13 months (compliance/audit) |
    |---|---|---|---|---|---|---|
    | **Logs** | ◻ | ◻ | ◻ | ◻ | ◻ | ◻ |
    | **Metrics** | ◻ | ◻ | ◻ | ◻ | ◻ | ◻ |
    | **Traces** | ◻ | ◻ | ◻ | ◻ | ◻ | ◻ |

    > *Tip: consider your longest realistic lookback — incident post-mortems, capacity trend analysis, and any compliance/audit mandate.*

---

## Section 5: Alerting & Incident Response *(Optional)*

25. **How would you rate the overall quality and actionability of current alerts?** *(Linear scale 1–5)*
    - 1: Very Poor (Constantly noisy, mostly false positives, ignored)
    - 2: Poor (High noise-to-signal ratio)
    - 3: Average (Useful for major outages, but requires filtering)
    - 4: Good (Mostly actionable with clear triage paths)
    - 5: Excellent (Every alert is actionable, tied to SLOs/error budgets with runbook links, zero noise)

26. **When an alert fires or an incident begins, where do you start your investigation?** *(Select up to 2)*
    - [ ] Service dashboards / Grafana
    - [ ] Log search / aggregation
    - [ ] Distributed trace timeline / APM
    - [ ] Service Level Objective (SLO) / Error budget burn rate alerts
    - [ ] Recent deployment / Git commit history
    - [ ] Ask in team Slack / Teams channels
    - [ ] Other: ___

27. **Are runbooks / triage guides readily available and updated for your services?** *(Single choice)*
    - Yes, linked directly inside alert notifications
    - Yes, maintained in wiki / repository docs
    - Outdated or incomplete
    - No runbooks exist
    - I don't know

---

## Section 6: OpenTelemetry (OTel) & Instrumentation *(Optional - Engineering)*

28. **What is your familiarity and adoption of OpenTelemetry (OTel)?** *(Single choice)*
    - Actively using OpenTelemetry SDKs / Collectors in production
    - Currently experimenting or migrating to OpenTelemetry
    - Familiar with the concept and standards, but not using it yet
    - Heard the name, unclear on how it works
    - Not familiar with OpenTelemetry

29. **What primary programming languages/frameworks do your services run on?** *(Select all that apply)*
    - [ ] Java / Kotlin / JVM
    - [ ] Python
    - [ ] Go
    - [ ] TypeScript / Node.js
    - [ ] .NET / C#
    - [ ] Rust
    - [ ] Frontend (React / Angular / Vue / Mobile)
    - [ ] Other: ___

30. **What would make instrumenting your services significantly easier?** *(Select all that apply)*
    - [ ] Zero-code Auto-Instrumentation (e.g., eBPF, Java agent, runtime hooks)
    - [ ] Standardized internal shared libraries / starter kits with pre-configured OTel
    - [ ] Sample repositories with reference implementations
    - [ ] Hands-on workshops / Office hours with the Platform team
    - [ ] Self-service CI/CD validation for telemetry schema compliance
    - [ ] Other: ___

---

## Section 7: Strategy, Standards & Tooling Direction *(Optional)*

> Inspired by industry benchmarks (e.g., the annual CNCF and Grafana Labs Observability Surveys). Helps align our roadmap with where the wider industry is heading.

31. **What are the most important criteria when selecting a new observability tool?** *(Select up to 3 — Form Builder Tip: Enable response validation "Select at most 3")*
    - [ ] Cost / total cost of ownership
    - [ ] Ease of use / low learning curve
    - [ ] Interoperability & open standards (OpenTelemetry, Prometheus, OTLP)
    - [ ] Ability to correlate signals (logs + metrics + traces)
    - [ ] Scalability to handle large telemetry volumes
    - [ ] Vendor lock-in avoidance / ease of switching backends
    - [ ] Data retention & query performance
    - [ ] AI / ML capabilities
    - [ ] Security & compliance (RBAC, audit, data residency)
    - [ ] Other: ___

32. **How important are open source / open standards (OpenTelemetry, Prometheus, OTLP) to our observability strategy?** *(Single choice)*
    - Essential (a hard requirement for any tool we adopt)
    - Very important
    - Somewhat important
    - Not important
    - No opinion

33. **What is our current investment stage for each standard?** *(Matrix — Google Forms: Multiple-choice grid | MS Forms: Likert)*
    | Standard | Not on radar | Investigating | Building POC | In production (some) | In production (most/all) |
    |---|---|---|---|---|---|
    | **Prometheus** | ◻ | ◻ | ◻ | ◻ | ◻ |
    | **OpenTelemetry** | ◻ | ◻ | ◻ | ◻ | ◻ |

34. **How is observability delivered/owned in our organization today?** *(Single choice)*
    - **Centralized platform team** runs the platform and provides best practices/support, but product teams own their own service observability
    - **Fully managed by a central ops team** separate from product teams (they own uptime/performance in prod)
    - **Siloed / per-team** — each team picks and runs its own tools, no central standard
    - **Embedded SREs** within product teams
    - I don't know

35. **How is our observability infrastructure hosted?** *(Single choice — leads/platform team best placed to answer; pick "I don't know" if unsure)*
    - Fully self-managed (we run Grafana/Prometheus/etc. ourselves)
    - Fully SaaS / managed (e.g., Amazon Managed Grafana, Datadog, Grafana Cloud)
    - Hybrid (mix of self-managed and SaaS)
    - I don't know

36. **How do you expect our observability spend to change next year?** *(Single choice)*
    - Increase — broader adoption / more services onboarded
    - Increase — higher vendor/SaaS bills
    - Increase — investing for higher ROI (better tooling)
    - Stay about the same
    - Decrease — more efficient operations / consolidation
    - I don't know

---

## Section 8: AI in Observability *(Optional)*

> Gauges team appetite, trust, and practical blockers for AI-assisted observability workflows.

37. **How valuable would AI be for each of these observability use cases?** *(Matrix — Google Forms: Multiple-choice grid | MS Forms: Likert)*
    | Use case | Not valuable | Somewhat valuable | Very valuable | Critical | Not sure |
    |---|---|---|---|---|---|
    | Surface anomalies/issues before they cause downtime | ◻ | ◻ | ◻ | ◻ | ◻ |
    | Forecast and spot trends (capacity, cost) | ◻ | ◻ | ◻ | ◻ | ◻ |
    | Assist with root cause & correlation analysis | ◻ | ◻ | ◻ | ◻ | ◻ |
    | Generate dashboards, alerts, or queries | ◻ | ◻ | ◻ | ◻ | ◻ |
    | Help new users quickly understand the system | ◻ | ◻ | ◻ | ◻ | ◻ |
    | Take autonomous actions (auto-remediation, workflows) | ◻ | ◻ | ◻ | ◻ | ◻ |

38. **How comfortable are you with AI taking autonomous actions (auto-remediation, triggering workflows) in production?** *(Single choice)*
    - Very comfortable — I'd let it act with minimal oversight
    - Comfortable with guardrails and approvals
    - Neutral / unsure
    - Uncomfortable — assistance only, humans decide
    - Strongly opposed — no autonomous action

39. **How important is it that AI explains its reasoning (sources, query logic, confidence levels)?** *(Single choice)*
    - Critical / essential
    - Very important
    - Somewhat important
    - Not important
    - Not sure

40. **What would most likely prevent you from using AI for observability tasks?** *(Single choice)*
    - Too much manual input of required context
    - It breaks too often / doesn't adapt to our environment
    - Lack of customization for our stack
    - Accuracy / trust concerns (hallucinations, wrong RCA)
    - Cost of AI features
    - Security / data privacy concerns
    - Nothing — I'd adopt it readily
    - Other: ___

41. **Are you monitoring AI / LLM-based applications (agentic workflows, model latency/cost/quality)?** *(Single choice)*
    - Yes, in production
    - Building a POC / experimenting
    - Investigating
    - Not on our radar
    - We don't run AI/LLM applications

---

## Section 9: Benchmarking & Open Feedback *(Optional)*

42. **What observability tools did you use in your PREVIOUS organization/company?** *(Select all that apply per signal)*
    - **Logs:**
      - [ ] Splunk
      - [ ] ELK Stack / OpenSearch / Kibana
      - [ ] Grafana Loki
      - [ ] Datadog Logs
      - [ ] AWS CloudWatch / GCP Cloud Logging
      - [ ] Sumo Logic
      - [ ] Other: ___
    - **Metrics & Dashboards:**
      - [ ] Grafana + Prometheus / Mimir / VictoriaMetrics
      - [ ] Datadog Metrics
      - [ ] New Relic
      - [ ] Dynatrace
      - [ ] AWS CloudWatch Metrics / GCP Cloud Monitoring
      - [ ] Other: ___
    - **Distributed Traces & APM:**
      - [ ] Datadog APM
      - [ ] Dynatrace
      - [ ] New Relic APM
      - [ ] Jaeger / Grafana Tempo
      - [ ] AWS X-Ray / Google Cloud Trace
      - [ ] Honeycomb / Lightstep
      - [ ] Apache SkyWalking
      - [ ] Other: ___
    - **Continuous Profiling & Frontend / Error Tracking:**
      - [ ] Sentry
      - [ ] Datadog Profiler / Datadog RUM
      - [ ] Grafana Pyroscope
      - [ ] LogRocket / Bugsnag
      - [ ] Other: ___
    - **Other tools / platforms used in past companies:** *(Free text)*
      - [ Free text ]

43. **Compared to your previous company or ideal setup, how does our current observability maturity rate?** *(Single choice)*
    - Much better here
    - Somewhat better here
    - Comparable
    - Somewhat worse here
    - Much worse here
    - N/A (First company / no prior baseline)

44. **What specific tool, workflow, or practice from past experience would you recommend we adopt?** *(Open text)*
    - [ Free text ]

45. **Any additional comments, wishlist items, or feedback for the Observability / Platform team?** *(Open text)*
    - [ Free text ]

---

## Appendix: Analyzing Results in Grafana (Internal - Optional)

For interactive analysis of the responses (inspired by how Grafana Labs analyzes its own Observability Survey):

1. **Collect** via Google Forms → responses land in a Google Sheet automatically.
2. **Preprocess** — split multi-select answers and free-text into their own columns; handle "Other" answers manually. Multi-value cells don't transform cleanly downstream.
3. **Load** the Sheet into BigQuery (or use the Google Sheets data source directly) so you can transform with SQL rather than chained Grafana transformations.
4. **Visualize** in Grafana — bar/pie/geomap panels for most questions; Business Charts (Apache ECharts) panel for multidimensional data (bubble/stacked bar).
5. **Add demographic filter variables** — Role (Q1), Team (Q2), Tenure (Q3), Familiarity (Q4). Combine into one `$filters` variable reused across every panel:
   ```sql
   `Role` IN (${role}) AND `Tenure` IN (${tenure}) AND `Familiarity` IN (${familiarity})
   ```
6. **Note (Google Forms limits):** no answer stack-ranking, no multi-language, limited conditional/multi-part questions — this survey uses "select up to N" instead of ranking to stay within those limits. For richer logic, use MS Forms or a dedicated survey platform.

---

## Analysis Guide (Internal - For Platform / Observability Team)

| Analytical Dimension | Indicator & Questions | Actionable Outcome / Strategic Decision |
|---|---|---|
| **Tool Sprawl & Primary Adoption per Signal** | Q9 (Logs), Q10 (Metrics), Q11 (Traces), Q12 (Profiling), Q13 (Frontend) | Identifies the most heavily used tools per telemetry signal and quantifies fragmentation/overlap across teams. |
| **Unified vs. Best-of-Breed** | Q20 | Determines whether to invest in unified suite (Grafana/Datadog) vs. multi-vendor pipeline. |
| **MTTR & Investigation Blockers** | Q16, Q17, Q18, Q25 | Correlate root cause discovery time with ingestion delay and correlation gaps. |
| **Signal Gaps (RUM / Profiling / Traces)** | Q6, Q7, Q11, Q12, Q13 | Highlights missing signal layers (e.g., client-side errors, non-prod telemetry). |
| **Log Maturity & Standardization** | Q9, Q14 | Quantifies structured vs. raw log split; guides log parser/schema standardization. |
| **Self-Service Appetite vs. Ability (per activity)** | Q22 | Splits respondents into "already self-sufficient", "wants access/enablement" (the actionable gap — grant RBAC or run training), and "prefers managed" for dashboards, alerts, instrumentation, pipeline, and retention. |
| **Retention Requirements per Signal** | Q24 | Compares desired logs/metrics/traces retention against current limits; drives tiering, downsampling, and compliance-retention policy per signal. |
| **Alert Actionability & Fatigue** | Q15, Q25, Q27 | Alert Quality Index (1–5). Identifies need for alert cleanup, SLO routing, and runbook linkage. |
| **OTel Migration Readiness** | Q28, Q29, Q30 | Identifies target language SDK priorities (e.g., Java vs. Python) and auto-instrumentation demand. |
| **Self-Service vs. Platform Support** | Q21, Q22, Q30 | Shapes platform team engagement model (Terraform modules vs. office hours vs. managed setups). |
| **Cost & Ingestion Awareness** | Q15, Q23 | Identifies necessity for chargeback/showback dashboards and automated data tiering/retention policies. |
| **Onboarding & Access Friction** | Q5, Q15 | Correlate onboarding ease with tenure; identifies access/permission and documentation gaps that slow new-joiner productivity. |
| **Tool Selection Criteria** | Q31 | Ranks what actually drives adoption (cost, ease, interop, AI) — the north star for tool evaluation/RFP scoring. |
| **Open Standards Commitment** | Q32, Q33 | Prometheus vs. OTel investment stage; guides how hard to standardize on OpenTelemetry and avoid lock-in. |
| **Ownership & Delivery Model** | Q34 | Centralized vs. siloed vs. embedded. Correlate with satisfaction (Q25, Q43) — centralized teams tend to report higher satisfaction. |
| **Hosting Model & Spend Trajectory** | Q35, Q36 | SaaS vs. self-managed split and next-year spend direction/reason; informs build-vs-buy and budget planning. |
| **AI Appetite & Trust Gap** | Q37, Q38, Q39 | Value-per-use-case vs. comfort with autonomy; transparency demand. Assistance is widely welcomed; autonomous action is the trust frontier. |
| **AI Adoption Blockers** | Q40, Q41 | Top blocker (usually manual context input) and whether LLM/agentic apps are even in scope to observe. |
| **Past Tool Experience & Industry Benchmark** | Q42, Q43, Q44, Q45 | Uncovers industry tools engineers are already proficient in (e.g., Splunk, New Relic, Datadog) to guide tool evaluation and minimize onboarding friction. |
