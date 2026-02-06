---
name: imc-plan-fnb
description: Create integrated marketing communications (IMC) plans for F&B brands, chains, or single outlets, especially when asked for a low-budget, social-first plan and a Markdown table output. Use when the user requests an IMC plan, a campaign plan, or a structured communications plan for F&B.
---

# IMC Plan for F&B

Use this skill to produce a complete IMC plan in Markdown table form, tuned for F&B and low-budget social-first campaigns.

## Quick Workflow
1. Collect inputs with short questions if missing: brand type, product focus, target location, campaign goal, duration, key offer, existing channels.
2. Follow the 6-step IMC structure in `references/imc-6-steps.md` and translate each step into plan sections.
3. Use the template in `assets/imc-plan-template.md` and fill it with concrete, realistic details for F&B.
4. Constrain the plan to a total budget of 10,000,000 VND unless the user specifies otherwise.
5. Prioritize social, UGC, and local partnerships; keep paid media minimal and performance-focused.
6. Provide measurable KPIs and a simple measurement plan that fits the budget.

## Output Rules
- Always output a single Markdown table plan (use the template).
- Keep assumptions explicit and labeled.
- If the user provides no KPIs, propose a minimal KPI set aligned to the objective.
- If details are missing, make conservative assumptions and list them in the plan.

## F&B Defaults and Heuristics
- Primary objective patterns: new store launch, product push, seasonal traffic boost, retention/loyalty.
- Typical audience segmentation: office workers, students, families, foodies, local residents.
- Low-budget emphasis: organic content, micro KOLs, on-ground sampling, local groups, short-form video.
- Budget split guidance (10,000,000 VND total): 40% content/production, 30% paid social, 20% KOL/partners, 10% activation/print.
- Timeline guidance: 2-6 weeks with 3 phases: tease, launch, sustain.

## When Information Is Missing
Ask up to 3 targeted questions. If the user cannot answer, proceed with explicit assumptions and keep the plan conservative.

## References
- Use `references/imc-6-steps.md` for the IMC structure.
- Use `assets/imc-plan-template.md` for the Markdown table layout.
