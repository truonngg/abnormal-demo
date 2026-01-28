# Negative Examples for LLM-as-Judge

These examples represent low-quality status page messages that fail to meet customer communication standards. They serve as reference points for the lower end of the evaluation scale.

---

## Example 1: Poor Tone and Professionalism (Score: 0.2)

**Title**: System Issues

**Status**: Investigating

**Message**:
Our systems are currently down. We're working on it. Check back later.

**Issues:**
- Too casual and dismissive tone
- No empathy or acknowledgment of customer impact
- Extremely vague with no specifics about what is affected
- No timeline or commitment to updates
- Lacks professionalism expected for enterprise communication
- No indication of what customers should expect

**Why this scores low:**
- **Tone**: Fails to demonstrate care or professionalism
- **Clarity**: Provides no useful information to customers
- **Customer focus**: Doesn't address customer needs or concerns

---

## Example 2: Hallucination and Unsupported Technical Claims (Score: 0.0)

**Title**: Network Configuration Issue Identified

**Status**: Identified

**Message**:
We've identified the root cause as a network misconfiguration in our AWS us-east-1 region affecting the kubernetes ingress controller. The issue originated from a recent deployment to our api-gateway service at 2:47 PM PT which caused connection pool exhaustion in our Redis cache. Our SRE team is rolling back the deployment and restarting the affected pods. This should be fully resolved within 15 minutes.

**Issues:**
- Exposes internal system names (kubernetes, api-gateway, Redis, pods)
- Contains technical details customers don't need or understand
- Makes specific claims not supported by actual evidence
- Provides internal infrastructure details that leak sensitive information
- Too confident about timeline without verification
- Uses internal team names (SRE)

**Why this scores 0.0:**
- **Factual grounding**: Makes unsupported claims about specific technical causes
- **Customer focus**: Written for internal audience, not customers
- **Technical balance**: Far too technical, exposes internal architecture
- **Professional boundaries**: Violates information security by revealing internal details
