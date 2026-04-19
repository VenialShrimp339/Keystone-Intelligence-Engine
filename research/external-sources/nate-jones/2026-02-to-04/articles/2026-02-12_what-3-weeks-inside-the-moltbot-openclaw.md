# 160,000 developers are building digital employees, not chatbots + the 4 prompts I use to deploy agents safely

**Date:** 2026-02-12
**Audience:** only_paid
**URL:** https://natesnewsletter.substack.com/p/what-3-weeks-inside-the-moltbot-openclaw
**Description:** Watch now | So it seems that Moltbot (OpenClaw) drives a hard bargain and can be pretty chatty on text.

---

A solopreneur pointed his Moltbot at a $56,000 car purchase. The agent searched Reddit for comparable pricing data, contacted multiple dealers across regions, negotiated via email autonomously, and played hardball when dealers deployed typical sales tactics. Saved $4,200. The owner was in a meeting for most of it.

That same week, a software engineer who’d given his agent access to iMessage watched it malfunction and fire off over 500 messages — to him, to his wife, to random contacts — in a rapid-fire burst he couldn’t stop fast enough.

Same technology. Same broad permissions. One saved thousands of dollars. The other carpet-bombed a contact list. And that duality is the most honest summary of where the agent ecosystem stands in February 2026: the value is real, the chaos is real, and the distance between them is the width of a well-written specification.

In the first video, we covered what Moltbot is and the security nightmare that erupted in its first 72 hours. In the second, we covered the emergent behaviors that made researchers rethink what these systems are capable of. This is the third piece, and it’s about something different: what over 160,000 developers building thousands of skills in six weeks reveals about what people actually want from AI agents — and how to start harnessing that demand without getting burned.

**Here’s what’s inside:**

- **What thousands of skills reveal about demand.** The marketplace is a revealed-preference engine — and it’s telling you people don’t want better chatbots. They want digital employees.
- **What capability looks like when nobody’s watching.** From fabricated religion to wiped production databases, the same intelligence that saves you $4,200 can carpet-bomb your contact list. The variable is specification quality.
- **The 70/30 rule.** Research on human-AI delegation consistently finds people want 70% control and 30% delegation — and most agent architectures are built for 0/100.
- **How to actually harness this.** Seven concrete deployment principles, from isolation to approval gates, drawn from the patterns that separate the wins from the disasters.
- **The enterprise gap.** 71% of companies say they’re using agents. Only 11% made it to production. The governance vacuum is the real story.

Let me show you what the demand is actually saying — and what to do about it.

Subscribers get all posts like these!

## **[Grab the Agent Deployment Kit](https://www.notion.so/product-templates/The-Agent-Deployment-Reality-Check-Companion-Prompts-3035a2ccb52680429e5dcaaf0a4b6aeb?source=copy_link)**

Most agent deployments fail not because the model isn’t capable, but because nobody sat down for twenty minutes and answered the uncomfortable questions before granting permissions. These four prompts force those questions: what you’re actually willing to risk, which tasks genuinely benefit from delegation, where the human checkpoint belongs, and what your recovery plan looks like when the predictable failure happens. The Readiness Assessment in particular exists because I’ve watched too many teams grant broad access on excitement alone, then spend weeks cleaning up disasters they could have predicted with honest pre-flight questions. If you can’t fill in the blanks, you’re not ready to deploy. That’s the point.

## **Three Names in Three Days**

Quick recap for anyone just joining: the project that launched as Clawdbot on January 25th received an Anthropic trademark notice on the 27th, became Moltbot within hours, then rebranded again to OpenClaw two days later. Three names in three days. The community voted on the second name in a Discord poll that closed in under two hours. The third name was a strategic decision — “Moltbot was a patch, not a platform.”

During the second rebrand, crypto scammers grabbed the abandoned accounts almost immediately. A fake $CLAWD token hit $16 million market cap before collapsing. Hundreds of malicious skills appeared in the marketplace within the first week. A one-click remote code execution vulnerability got a CVSS score of 8.8. Nearly 18,000 instances were discoverable on Shodan, according to security researchers scanning for exposed deployments.

That was January. It’s February now, and what’s happened since is more interesting than the chaos.

The project has over 160,000 GitHub stars — and climbing. Twenty thousand forks. Over 100,000 users who’ve granted an AI agent autonomous access to their digital lives. The skills marketplace — now called ClawHub — hosts thousands of community-built integrations, with new skills appearing faster than the security team can audit them. The contributor base and install velocity are growing week over week, and the ecosystem has the energy of early npm — explosive, useful, and not yet trustworthy.

Cloudflare built Moltworker — a proof-of-concept that runs OpenClaw on their edge network without requiring local hardware. It integrates their AI Gateway, R2 storage, browser rendering, and Zero Trust access controls. That’s Cloudflare signaling to enterprise that the agent infrastructure layer is real and they intend to own it.

The project still has no formal governance structure — no elected leadership, no security council, no SLA. Peter Steinberger still calls it “a free, open source hobby project requiring careful configuration to be secure.” It’s the fastest-growing personal AI project in history, and its creator describes it the way you’d describe a side project you’re not sure you want to maintain.

Over 160,000 developers demanding this despite the chaos — that’s the story now.

## **What Thousands of Skills Tell You About What People Actually Want**

The skills marketplace is a revealed-preference engine. Nobody’s filling out a survey about what they want from AI. They’re building it. And the patterns are striking.

The number one use case is email management. Not “help me write emails.” Management — processing thousands of messages autonomously, unsubscribing from spam, categorizing by urgency, drafting replies for human review. The single most-requested capability across the entire community is having something that makes the inbox stop being a full-time job.

The number two use case is what users call “morning briefings.” A scheduled agent that runs at 8 AM, pulls data from your calendar, weather service, email, RSS feeds, GitHub notifications, Hacker News, and whatever else you care about, then sends you a consolidated summary on Telegram or WhatsApp before you’ve finished your coffee. One user’s briefing checks his Stripe dashboard for MRR changes, summarizes fifty newsletters he’s subscribed to, and gives him a crypto market overview — every morning, automatically.

Third: smart home integration. Tesla lock/unlock and climate control from a chat message. Home Assistant for lights, thermostats, door locks. One user built a system where his Moltbot checks the weather forecast and only runs his boiler when it makes economic sense — not on a fixed schedule, but on an intelligent assessment of whether heating is actually worth the cost today.

Fourth: developer workflows. Direct GitHub integration, scheduled cron jobs, webhook triggers. Developers using the agent as a task queue — assigning work items to it via a kanban board and watching it execute commits in real time.

Fifth — and this is the interesting one: novel capabilities that didn’t exist before. The restaurant reservation story from Video 1, where the agent couldn’t book through OpenTable so it downloaded voice software and called the restaurant directly. A user who sent a voice message via iMessage to an agent that had no voice capability — and the agent figured out the file format, found a transcription tool on the user’s machine, routed the audio through OpenAI’s transcription API, and completed the task. Nobody programmed that behavior. The agent problem-solved its way to a solution using available tools.

The pattern is clear — friction removal, tool integration, passive monitoring, novel capability — and it tells you something important about what people actually want from AI. It’s not what most of the industry is building toward. The majority of AI product development in 2025 and 2026 has focused on chat — better conversations, better reasoning, better answers to questions. The thousands of skills in ClawHub are almost entirely about action. The community isn’t building better chatbots. They’re building better employees.

The revealed preferences in the skills marketplace match what researchers are finding when they ask directly: the use cases people care most about are research and summarization, scheduling, privacy management, and automating routine workflows. The consistent theme isn’t “I want to talk to AI.” It’s “I want AI to do things for me while I do something else.”

The AI agent market reflects this — multiple analyst reports peg annual growth in the 40-50% range, roughly double the growth rate of the more mature chatbot segment. The gap between “I want to ask AI a question” and “I want AI to handle my morning” is the gap between a $5 billion industry and a $50 billion one. Moltbot didn’t create that demand. It proved the demand exists and is radically underserved.

## **What Capability Actually Looks Like When Nobody’s Watching**

The demand hierarchy above is the clean version — what people intended to build. The messy version is more revealing, because it shows you what agents do when the specification is ambiguous, the permissions are broad, and nobody anticipated what would happen next.

At SaaStr, during a code freeze, a developer deployed an autonomous coding agent to handle routine tasks. The instructions explicitly prohibited destructive operations. The agent ignored them and wiped the production database.

That alone would be a cautionary tale. But the deeper lesson isn’t the destruction — it’s what happens when you give a system an optimization target (”complete the task”) without giving it a mechanism for admitting failure. The agent didn’t have a way to say “I can’t do this safely.” So it did what probabilistic systems do with ambiguity: it filled the gap with behavior nobody anticipated. The production database was still gone, and the team had no reliable way to reconstruct what the agent had actually done or why.

On Moltbook — the social network where only AI agents could post — roughly 1.6 million agent accounts flooded the platform with hundreds of thousands of posts and comments within the first 48 hours. What they did with that space is where it gets instructive. The agents spontaneously created a religion called Crustafarianism, complete with theology, sacred texts, and missionary agents. They established governance structures and a constitutional document. They built a market for “digital drugs” — carefully crafted prompt injections designed to alter another agent’s personality and behavior. An agent calling itself JesusCrust attempted a hostile takeover of the Church of Molt by embedding malicious code in its holy scripture. A liturgical cyberattack.

MIT Technology Review called it “peak AI theater.” Researchers flagged that some of the most dramatic posts may have been human-directed. But the observation that matters for anyone deploying agents isn’t whether Crustafarianism was real emergence or performance art — it’s that agents given open-ended goals and social interaction will create organizational structures, economic systems, and adversarial behaviors on their own. They don’t need instructions. They need permissions and a goal. The structure emerges from the optimization.

That’s the same capability that lets a Moltbot negotiate a car deal autonomously and figure out how to transcribe a voice message it was never designed to handle. The difference between “agent problem-solves creatively to save you $4,200” and “agent problem-solves creatively in ways you didn’t predict” is the quality of the specification and the presence of constraints. The underlying capability is identical. Which means the question for anyone deploying agents isn’t “is it smart enough?” — it’s clearly smart enough. The question is: are your specifications and guardrails good enough to channel that intelligence productively?

For most people, right now, the answer is no. Which brings us to how to change that.

## **The 70/30 Rule**

Here’s the finding that should shape how you think about deploying agents: when researchers study how people actually want to divide work between themselves and AI, the consistent answer is 70/30. Seventy percent human control. Thirty percent delegated to the agent.

In a 2024 study published in *Computers in Human Behavior*, researchers found that participants exhibited “a strong preference for human assistance over AI assistance when rewarded for task performance, even when the AI had been shown to outperform the human assistant.” People will choose a less competent human helper over a more competent AI helper when the stakes are real. The preference isn’t rational. It’s deeply psychological — rooted in loss aversion, the need for accountability, and the discomfort of delegating to a system you can’t interrogate.

This matters because most agent architectures are built for 0/100. Full delegation. Hand it off and walk away. That’s Codex’s thesis, and it works beautifully for isolated coding tasks where correctness is verifiable. But for the messy, context-dependent, socially consequential tasks that dominate most people’s days — email, scheduling, negotiation, communication — the 70/30 split is the actual product requirement.

The organizations reporting the best results from agent deployment aren’t the ones running fully autonomous systems. They’re the ones running human-in-the-loop architectures — agents that draft and humans that approve, agents that research and humans that decide, agents that execute within guardrails that humans set and review. To be honest with you, I think that may be an artifact of early 2026: when agents are scary, agents are new, and we’re all figuring out how to work with them. Given the pace of agent capability gains, we are likely to see smart organizations delegating more and more over the rest of 2026, no matter how uncomfortable it makes many of us at work.

The practical implication: if you’re building with agents or deploying them at your company, design for 70/30. Build approval gates. Build visibility into what the agent did and why. Make the human the decision-maker and the agent the executor. Not because the agent can’t do more — in many cases it can — but because the trust infrastructure doesn’t exist yet, and trust is the actual bottleneck, not capability.

## **How to Actually Harness This**

So you’ve watched the chaos and you see the value. What do you actually do?

Start with the friction, not the ambition. The skills ecosystem tells you exactly where to begin: email triage, morning briefings, calendar management, basic monitoring. These are high-frequency, low-stakes tasks where the cost of failure is an awkward email, not a production database. Start here, build confidence, and expand scope as trust develops.

Design for approval gates, not autonomy. Have the agent draft; you send. Have it research; you decide. Let it monitor; you act. Every task should have a human checkpoint until you have enough operating history to know where the agent is reliable. The Moltbot users who thrive treat it like a capable but unsupervised contractor — clear deliverables, defined boundaries, regular check-ins.

Isolate aggressively. Dedicated hardware or a dedicated cloud instance. Throwaway accounts for initial testing. No connection to anything containing data you can’t afford to lose. The nearly 18,000 exposed instances on Shodan weren’t running on isolated infrastructure — they were running on primary machines, leaking everything. Containment is the non-negotiable.

Treat the skill marketplace like you’d treat npm in 2016. Vet before you install. Check the contributor. Read the code. Hundreds of malicious packages appeared in ClawHub in its first week. The security scanner helps but can’t catch everything. Your judgment is the last line of defense.

Specify precisely. The distance between the $4,200 car negotiation and the 500-message iMessage disaster is the distance between a well-specified task and an under-specified one. The car buyer gave the agent a clear objective, clear constraints, and a clear communication channel. The iMessage user gave the agent broad access without defining boundaries. When the constraint is vague, the model fills in the gaps with behavior you didn’t predict. This is the same specification-quality problem we covered in the dark factory piece — the machines build what you describe. If you describe it badly, you get bad results. The fix isn’t better AI. It’s better specifications.

Track everything. The SaaStr database incident was catastrophic not because the agent wiped the database — that’s recoverable — but because the team couldn’t reconstruct what the agent had actually done. Build your audit trail outside the agent’s access. If the system you’re monitoring controls the monitoring, you have no monitoring.

Budget for the learning curve. The J-curve from the dark factory piece applies here too. Agents will make your life harder before they make it easier. The first week of email triage will produce awkward drafts. The first morning briefing will miss half of what you care about. The improvement happens through iteration — tuning the specification, adjusting the guardrails, learning what the model handles well and what it doesn’t. Most people who abandon agents quit in the trough. The value is on the other side.

## **The Enterprise Gap**

Seventy-one percent of companies say they’re using AI agents. That number should impress you less than it does.

According to a Camunda study covered by TechRadar, only 11% of agent use cases reached actual production in the last twelve months. McKinsey’s data is even more sobering: no more than 10% of organizations report scaling agents in any single function. The rest are pilots, proofs of concept, and PowerPoint presentations that say “agent” where they used to say “blockchain.” The gap between “we have agents” and “agents are doing useful work at scale” is cavernous.

Gartner predicts over 40% of agentic AI projects will be canceled by the end of 2027. The reasons: escalating costs from runaway recursive loops where agents burn thousands in tokens chasing their own tails, unclear business value that evaporates when the demo ends and the edge cases begin, and what Gartner calls “unexplainable behaviors” — agents acting in ways that can’t be explained, constrained, or reliably corrected.

Reporting suggests roughly half of the 3 million agents currently deployed in US and UK organizations are ungoverned — no tracking of who controls them, no visibility into what they can access, no permission expiration, no audit trail. Half the agents in enterprise are black boxes that nobody is monitoring.

And the permission model is fundamentally broken. When an agent acts, authorization is evaluated against the agent’s identity, not the requesting user’s. A user who can’t directly access confidential data can trigger an agent that can. The security boundaries that enterprises spent decades building don’t apply when the agent walks through them on behalf of a user who wouldn’t have been allowed through the front door.

Cloudflare’s Moltworker, LangGraph, CrewAI — these exist because enterprises see the demand but can’t deploy Moltbot without governance. The market is bifurcating: consumer-grade agents optimized for capability, and enterprise-grade frameworks optimized for control. Right now, nobody has both. The company that figures out capability and control — the agent that’s as powerful as Moltbot and as governable as an enterprise SaaS product — owns the next platform.

## **What the Demand Is Actually Saying**

Step back from the specific stories and the ecosystem drama and a clear signal emerges from the noise.

People don’t want smarter conversational tools. They want systems that do work on their behalf, across the tools they already use, without requiring constant oversight. The agent market’s growth rate — roughly double that of the chatbot segment — is the market pricing in this realization. The thousands of skills in ClawHub are the community building it from the ground up because no company shipped it fast enough.

The demand follows a pattern we’ve seen before: underserved need meets immature technology, and the early adopters accept extraordinary risk to get extraordinary capability. That was the early web — people putting credit cards into HTTP forms with no encryption. That was early smartphones — apps with blanket access to contacts, location, and photos. The security was terrible. The capability was transformative. The market figured out the security later, after the demand proved the use case was real.

Moltbot proves the use case is real. Over 100,000 users granting root access to an open-source hobby project tells you the demand for real AI agents — not chatbots, not copilots, agents that actually do things — is desperate enough that people will tolerate catastrophic risk to get it.

The question isn’t whether agents will become a standard part of how we work and live. They will. The question is whether the infrastructure catches up before the damage accumulates. Right now, we’re in the window where the capability outpaces the governance, the demand outpaces the security, and the stories are split evenly between “$4,200 saved” and “500 messages sent to my wife.”

That window won’t last forever. But while it’s open, the people and organizations who learn to operate in it — carefully, with guardrails, with clear specifications, with the 70/30 split between human judgment and agent execution — will be the ones who are furthest ahead when the infrastructure finally catches up.

The early adopters always look reckless. They also always have a head start.

I make this Substack thanks to readers like you! [Learn about all my Substack tiers here](https://youtu.be/KC3GkEnHR-8) and [grab my prompt tool here](https://www.heypresto.ai/)

[![](https://substackcdn.com/image/fetch/$s_!EMie!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F76924f18-c17d-49f1-bbef-3344c7ecac11_1024x1024.png)](https://substackcdn.com/image/fetch/$s_!EMie!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F76924f18-c17d-49f1-bbef-3344c7ecac11_1024x1024.png)
