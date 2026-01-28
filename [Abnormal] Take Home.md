# **PRD: AI-Enhanced Incident Management Communications**

## **Key Assumptions**

**Stakeholders & roles (assumptions)**
The primary users are Incident Commanders (ICs). In practice, Technical Support and Engineers often serve as ICs and own external status page communications during customer-impacting incidents.

Engineers are both contributors and reviewers, providing the technical understanding of what’s broken, what’s impacted, and current mitigation progress; they also implicitly share responsibility for the accuracy of external messaging. Technical Support helps ensure messaging is customer-centered, clear, and aligned with what customers are experiencing/asking.

External customers are a critical stakeholder, as they are the primary consumers of incident communications and are directly impacted by service disruptions. Clear, timely, and accurate updates are essential to maintaining customer trust, reducing uncertainty, and preserving confidence in the product during incidents.

**Current workflow**
I assume that the current workflow is as follows: 

* Trigger: A customer-impacting incident (or credible signals of one) triggers the need to post to the status page.  
* Phases: Updates generally follow status phases like Investigating → Identified → Monitoring → Resolved.  
* Information sources: ICs synthesize updates from PagerDuty alerts (detection, severity, ownership) and Slack incident threads (ongoing investigation context). Engineers concurrently consult operational data sources (e.g., logs/metrics/deployments), but that synthesis is largely manual and distributed.  
* Drafting & review: Drafting and review happen under time pressure. Even when support "owns" communications, engineering still spends time relaying technical context and validating language.

**Pain points (what's broken today)**

There are 4 main buckets of pain points in this process today: 

1. Time loss in drafting/review loops: Writing, editing, and getting quick alignment slows the first update and subsequent updates.  
2. High cognitive load at the worst time: During active mitigation, engineers (and ICs) must context-switch from debugging to communications, creating unavoidable cognitive overhead.  
3. Inconsistent message quality: Tone, structure, and completeness vary by author and time pressure during incidents.  
4. Communication risk: Over-sharing internal details (system names, internal jargon, internal hypotheses), under-communicating customer impact/scope, and incorrect timestamps / duration statements

**Explicit operating assumptions for the AI system**

I assume four operating principles that are in scope for this system. First, there should be a human-in-the-loop for publishing. AI produces a draft; a human approves/edits before posting. Next, a draft should be available within 15–30 minutes of detection, ideally earlier, to reduce "time to first external comms." To build a reliable, useful system, we target a draft that is ~90% there to ensure highly usable drafts that reduce cognitive load. 

## **North Star Vision and Scope**

**North star vision**
Enable Incident Commanders to generate external-facing incident communications across all phases (Investigating, Identified, Monitoring, Resolved) that are clear, consistent, and customer-appropriate, while reducing manual effort, time-to-first-update, and engineers' cognitive load during active incidents.

**Product thesis (why this matters)**
Status page updates throughout the incident lifecycle are high-leverage moments where customers need reassurance, engineers are busy diagnosing/mitigating, and communication quality and tone directly impact customer trust.

An AI system that can reliably produce strong phase-appropriate drafts, grounded in real incident signals and transparent evidence, creates immediate operational value without needing to automate the full incident lifecycle.

**MVP scope** 

The MVP scope is a standalone UI prototype that:

* **Supports phase-aware draft generation** for Investigating and Identified phases 
* **Ingests multiple incident data sources** (e.g., Slack incident thread excerpts, PagerDuty incident metadata, CloudWatch logs, Prometheus metrics, GitHub deployments)
* **Uses a three-stage AI pipeline**:
  1. **LLM Evidence Extraction**: Intelligently extracts structured evidence from raw incident data, adapting to any file format or schema variation
  2. **LLM Draft Generation**: Produces phase-appropriate status update drafts following style guide and tone requirements
  3. **Quality Evaluation**: Combines deterministic checks with LLM-as-judge scoring across multiple dimensions
* **Outputs transparent evidence artifacts** showing what data supported each claim, enabling trust and rapid review
* **Provides comprehensive quality scoring** using:
  * A defined rubric (clarity, completeness, customer focus, internal-leakage checks, factual grounding)
  * Deterministic checks (length, forbidden internal terms, required fields, phase-specific requirements)
  * LLM-as-judge scoring for subjective dimensions (tone, clarity, appropriateness)

Core MVP deliverable: **"From messy incident signals → phase-aware, publishable-quality draft + transparent evidence + comprehensive quality evaluation."**

This prototype is a standalone UI where the incident commander selects their current phase (Investigating, Identified, etc.) and uploads available incident data to quickly produce a high-quality status update draft.

**Next Steps / Features (Non-goals for this prototype)**

1. Generating all four phases (Investigating, Identified, Monitoring, Resolved) - prototype focuses on Investigating + Identified as proof of concept
2. Building a rich edit/collaboration workflow (multi-reviewer, comments, approvals, edit with AI)
3. Implementing publishing integrations (status page API, PagerDuty/Slack bots, automated posting)
4. Performing full root cause analysis or remediation guidance (beyond what's needed to describe customer-facing impact conservatively)
5. Real-time ingestion/streaming (webhooks, log streams); the prototype uses file-based inputs / provided dataset
6. Automated phase detection (prototype requires user to select phase manually)
7. Surgical fixes capability: Allow ICs to request targeted edits to specific parts of the draft (e.g., "make the impact description less technical", "add more detail about affected regions", "soften the timeline commitment") without regenerating the entire message, preserving approved sections
8. Multiple draft variants: Generate 2-3 alternative draft options simultaneously with different tones or levels of detail (e.g., conservative vs. detailed, technical vs. customer-friendly) so ICs can choose the best fit for their specific customer base and incident context

## **High-level User Experience and User Stories** 

**High-level UX (happy path)**

1. **Incident detected**: PagerDuty alert triggers, and an incident commander (Support/Engineering) is assigned
2. **Open the assistant**: IC opens the standalone "Incident Comms Assistant" UI
3. **Select incident phase**: IC indicates where they are in the incident lifecycle (Investigating, Identified, Monitoring, or Resolved)
4. **Upload incident data**: IC uploads/attaches available incident files (e.g., Slack thread excerpt, PagerDuty incident JSON, metrics/logs/deployments). The system accepts any combination of files—missing data is handled gracefully
5. **AI three-stage processing**: In parallel with ongoing engineering investigation, the assistant:
   1. **Evidence Extraction**: LLM extracts structured evidence from uploaded files (incident metadata, symptoms, diagnosis, timeline, internal terms to avoid)
   2. **Draft Generation**: LLM generates phase-appropriate status update using extracted evidence and style guide
   3. **Quality Evaluation**: System evaluates draft using deterministic checks + LLM-as-judge scoring
6. **Review + trust signals**: IC reviews the draft alongside:
   1. Extracted evidence showing what data supported each claim
   2. Quality evaluation report (dimension scores, warnings, recommendations)
   3. Transparency about which data sources were used and why
7. **Publish**: IC copies the draft into the status page and posts

**Primary user stories (MVP)**

1. **Phase-aware draft generation**: As an Incident Commander, I want to generate appropriate status updates for different incident phases (Investigating, Identified) from messy incident signals, so customers receive timely and accurate communications as the incident progresses
2. **Reduce comms cognitive load on engineering**: As an Engineer on-call / assisting IC, I want the system to produce a customer-appropriate draft without me having to translate internal technical details into external language, so I can stay focused on diagnosis and resolution
3. **Trust, safety, and transparent grounding before posting**: As an Incident Commander, I want to see what the draft is based on (extracted evidence + source-level grounding) and whether it passes quality/leakage checks, so I can confidently publish without over-sharing or making unsupported claims
5. **External customer value**: As an external customer, I want timely and accurate incident communications so I can understand service impact and maintain trust in the product during disruptions


## **Implementation Approach and Technical Design Thinking** 

**Design principles**

1. **Grounded over clever**: Prefer conservative, source-backed language to avoid hallucinations and over-claiming
2. **Structured before generative**: Convert raw incident signals into a structured intermediate representation before asking an LLM to write prose. This is achieved through the three-stage pipeline
3. **Separation of concerns**: Distinct stages for extraction → generation → evaluation to simplify debugging and iteration. Each stage is independently testable and improvable
4. **AI-native flexibility**: Use LLMs for tasks that require flexibility (varying data formats, schema changes) rather than brittle hardcoded parsing. This makes the system adaptable to real-world incident data messiness
5. **Fail safely**: If evidence is incomplete/contradictory, generate a more conservative draft and explicitly lower confidence scores with clear warnings

**System architecture (high level)**

### Inputs (multi-source):

* PagerDuty incident metadata (severity, service name, timestamps)
* Slack incident thread excerpts (human timeline, hypotheses, mitigation notes)
* CloudWatch logs (error messages indicating failure mode)
* Prometheus metrics (latency/error rates over time)
* GitHub deployments (recent changes correlated with incident timing)

### Three-Stage AI Pipeline:

**Stage 1: LLM-Powered Evidence Extraction**

The system uses an LLM to intelligently extract structured evidence from raw incident data, avoiding brittle hardcoded parsing:

* **Input**: All uploaded files (any combination) + selected phase context
* **LLM analyzes files and extracts**:
  * Incident metadata (title, severity, start time in PT, affected service)
  * Customer-facing symptoms (with confidence levels and evidence sources)
  * Investigation status (root cause identified?, diagnosis summary, mitigation action)
  * Timeline of key events
  * Internal terms to avoid (service names, database identifiers, employee names, PR numbers)
  * Supporting evidence (deployment correlations, error patterns, metrics summary)
* **Output**: Structured JSON evidence artifact (saved for transparency and evaluation)

**Why LLM for extraction?**
* Handles varying data formats and schema changes without code updates
* Adapts to new data sources automatically (e.g., Opsgenie instead of PagerDuty)
* Correlates information intelligently across multiple files
* Phase-aware filtering (extracts only relevant information per phase)
* Gracefully handles missing or incomplete data

**Stage 2: LLM-Powered Draft Generation**

The system generates customer-facing communication using the extracted evidence:

* **Input**: Structured evidence from Stage 1 + phase-specific prompt + style guide (status_page_examples.md)
* **LLM generates draft** with:
  * Title (clear, concise)
  * Status (Investigating / Identified / Monitoring / Resolved)
  * Message body (recommended 60-150 words; hard fail <45 or >160)
  * Next update timing
* **Phase-specific generation guidance**:
  * **Investigating**: Conservative language, acknowledge issue without claiming cause
  * **Identified**: State cause identified, explain mitigation without technical details
  * **Monitoring**: Note fix deployed and metrics improving
  * **Resolved**: Provide timeline summary and apologize for impact
* **Constraints applied**: No internal terms, no unsupported claims, follow tone guidelines

**Stage 3: Multi-Dimensional Quality Evaluation**

The system evaluates draft quality using both deterministic rules and LLM-as-judge:

**Deterministic Checks (Fast, Reliable)**:
* Length validation (recommended 60–150 words; hard fail <45 or >160)
* Internal term leakage detection (check against extracted internal terms list)
* Required fields present (customer impact, affected service, action, next update)
* Phase-specific requirements (e.g., "Investigating" should not claim root cause)

**LLM-as-Judge Evaluation (Subjective Quality)**:
* **Input**: Draft + Evidence + Style Guide
* **LLM scores across dimensions**:
  * Clarity and customer focus (0.0-1.0)
  * Tone consistency with brand voice (0.0-1.0)
  * Appropriate technical detail balance (0.0-1.0)
  * Factual grounding / no hallucinations (0.0-1.0)
  * Phase appropriateness (0.0-1.0)
* Each dimension includes rationale and status (pass/warning/fail)
* **Model**: gpt-4o-mini

**Aggregate Results**:
* Overall quality score
* Confidence level (High/Medium/Low)
* List of warnings or concerns
* Specific improvement suggestions

**Output Packaging for Human Review**:
* Draft message in copy/paste format
* Extracted evidence (transparent about what data drove each claim)
* Quality evaluation report (scores + rationales)
* Clear indication of which data sources were used
* Warnings about missing data or lower confidence areas

**MVP implementation shape** 

* **Frontend**: Streamlit for speed (standalone browser-accessible UI with phase selector, file upload, evidence display, draft display, quality scores)
* **Backend**: FastAPI in Python:
  * Stage 1: Evidence extraction service (LLM call with structured output)
  * Stage 2: Draft generation service (LLM call with phase-specific prompts)
  * Stage 3: Evaluation service (deterministic rules + LLM-as-judge)
  * Returns draft + evidence + evaluation report
* **LLM**: OpenAI-compatible API via OpenRouter (models vary by stage)

## **Phased Rollout Plan**

**Crawl**

* **Goal**: Prove that this minimum viable proof-of-concept delivers real value!
* **Users + use case**: ICs handling lower-severity customer-impacting incidents, supporting "Investigating" and "Identified" phase status updates
* **Focus**: The system focuses on AI-driven, phase-aware draft generation using a three-stage pipeline (evidence extraction, draft generation, quality evaluation) to reduce cognitive load and accelerate time to first external communication while maintaining strict safety and accuracy constraints
* **Success**: Measured primarily by median time from incident detection to published status update, alongside quality guardrails including the percentage of drafts published without material correction and the number of post-publish corrections required
* **Progression to Walk phase**: Gated by demonstrated user trust and adoption, reflected in consistent real-incident usage and reliance on AI-generated drafts with minimal human rework

**Walk**

* **Goal**: Broaden usefulness to different use cases
* Expand usage to higher-severity incidents and support additional status phases (Monitoring and Resolved) while maintaining evidence grounding
* Improve signal extraction and correlation reliability through feedback loops from human edits and post-incident reviews
* **Success**: Measured by sustained adoption across multiple incident types, continued reduction in median detection-to-publish time, and stable quality metrics with low correction rates

**Run**

* **Goal**: Become the default comms workflow with high trust + high automation
* Fully embed the assistant into the incident response workflow with real-time or near real-time data ingestion, native integrations with incident management and status page tools (e.g., Slack, PagerDuty), automated surgical fixes via LLM-as-a-judge, build out edit experience
* Support the full incident communication lifecycle, generating updates across all phases with strong evidence grounding and confidence controls
* **Success**: Reflected in consistently fast and reliable customer communications, high user trust with minimal manual intervention, reduced operational burden on engineering and support teams, and improved customer satisfaction during incidents

## ​​**Success Metrics and Evaluation Framework**

**Product / outcome metrics (measured in real incident operations)**

* **North Star**: Median time from incident detection to published external status update
* **Adoption**:
  * % of eligible incidents where ICs generate drafts in the assistant
  * % of incidents where the published update is based primarily on the AI draft
* **Editorial efficiency**:
  * Time from first draft → publish
  * “Material edit” rate (human had to change meaning/claims vs. minor copy edits)
  * Edit distance / rewrite frequency prior to publishing

**Prototype-implemented quality metrics (what the current product actually returns)**

* **Overall quality score**:
  * `confidence_score` (0.0–1.0) = LLM-as-Judge weighted overall score across 5 dimensions
  * `confidence_level` mapping: High (≥0.8), Medium (0.6–0.8), Low (<0.6)
* **Deterministic guardrails (pass/warning/fail)**:
  * Length validation (recommended 60–150 words; hard fail <45 or >160)
  * Internal term leakage detection (scan draft against extracted `internal_terms_to_avoid`)
  * Required fields present (impact, affected service, action, next update timing)
  * Phase-specific requirements (e.g., Investigating must not claim root cause)
* **Transparency / grounding signals**:
  * `evidence_mappings`: per-claim/source provenance (e.g., “PagerDuty”, “CloudWatch Logs”, “Incident Context”)
  * `internal_terms_avoided`: which internal terms were successfully excluded/translated
  * `data_sources_used`: which inputs contributed to the draft

**Guardrail / safety metrics (operationalized via the prototype’s checks + outputs)**

* **Internal information leakage rate**: % drafts failing leakage detection
* **Unsupported causal language rate** (esp. Investigating): % drafts failing phase-specific checks
* **Completeness rate**: % drafts passing “Required fields present”
* **Quality distribution**: histogram of `confidence_score` over time / by incident type

**AI Output Quality Evaluation System**

1. **Deterministic and Rules-Based Checks**
   1. Validation that all required communication fields are present
   2. Enforcement of length and structure constraints per incident phase
   3. Blocklist and pattern detection for internal terminology and sensitive identifiers
   4. Detection of causal language or definitive claims without supporting evidence
   5. Evidence grounding verification ensuring each key statement is traceable to an input signal
2. **LLM-as-a-Judge Evaluation (Subjective Quality)**
   1. Clarity and customer focus
   2. Tone consistency with brand voice
   3. Appropriate technical detail balance
   4. Factual grounding / no hallucinations
   5. Phase appropriateness

Each draft receives dimension-level scores with brief rationales to support transparency and iteration.
