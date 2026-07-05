# Mathematics for Machine Learning — node-derivation research (audit trail)

Source: Gemini Deep Research, 2026-07-05. Prerequisite-subject prompt variant
(`content/research/_ready-prompt-math.md`). Target: aspiring ML Engineer / Data Scientist, India,
0–4 yr. Seeded by `backend/seed_math_ml.py` (UUID 90909090, slug math-for-ml). Replaced the
"Coming Soon" stub.

Full raw report: headroom hash `9982601dde3266d53978f032`.

## Node list (36 nodes, 3 phases) — see seed for tuples
Linear Algebra (12) · Calculus & Optimization (12) · Probability & Statistics (12).
Tuples came in correct (phase, section, title, tier, desc) order.

Tier mix: 12 hard, healthy easy/medium spread — not beginner-only.

## The anti-proof rule visibly held
Every description names the ML method the math unlocks, e.g.:
- Eigenvectors → principal axes in PCA
- Multivariable chain rule → backpropagation weight updates
- Vector norms L1/L2 → sparsity vs weight-penalty regularization
- MLE → cross-entropy loss for logistic regression; MAP → weight regularization
- KKT conditions → sparse support vectors in SVM
- Bayes / conditional probability → Naive Bayes
No proof-only or no-ML-payoff nodes slipped in. This is the cleanest run of the batch on
scope-discipline at the node level.

## ⚠ Gap in THIS run's output
The pasted output was the NODES list ONLY — **no `excluded` list, no `validation` mapping, no
`sources`** were captured. So:
- Scope discipline is verified at node quality (anti-proof rule held, ML payoff named), NOT via
  an excluded list or mock-interview coverage check.
- If the excluded/validation/sources are still in the Gemini chat, worth pasting them in to
  complete this audit — especially the `excluded` list, which is the proof that proof-only /
  pure-math topics (measure theory, abstract algebra, epsilon-delta) were consciously cut.
- No orphan-node check was possible (no validation questions). Node quality suggests none, but
  it's unverified.

## Claude review notes
- Phase order LA → Calculus → Probability is fine; all three are descriptive step-spine names
  (consistent with DE / relabeled MLOps).
- Coverage looks complete for the interview + model-prerequisite gate: PCA, OLS, GD/SGD,
  backprop, SVM, logistic regression, Naive Bayes, A/B testing all have their math prerequisites
  represented. No obvious missing node for a 0-4yr ML/DS target.
- Descriptions use " - " as an em-dash substitute (plain text, export-safe) — consistent.

## Sources
Not captured this run (see gap above). Prompt canon was: "Mathematics for Machine Learning"
(Deisenroth/Faisal/Ong); 3Blue1Brown Essence of Linear Algebra + Calculus; Andrew Ng course math.
