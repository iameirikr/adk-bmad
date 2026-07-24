# Eval sets

`review_gate_blocks_on_critical_finding.evalset.json` is a real, `adk eval_set create`-scaffolded
eval set (correct schema, verified against google-adk 2.5.0) — currently with **zero eval cases**.
It's a starting point, not a populated test suite: eval cases need an actual recorded
trajectory/response, which means running adk-bmad once against a real model provider and a fixture
story with a deliberately unresolved `decision_needed`/`patch` finding, then capturing that run:

```bash
# 1. Run adk-bmad for real against a fixture that should fail the review gate
adk run src   # walk it through a story you've rigged to fail review

# 2. Convert that session into an eval case
adk eval_set add_eval_case src tests/eval/review_gate_blocks_on_critical_finding.evalset.json \
  --session_id <the session id from step 1>

# 3. Run it
adk eval src tests/eval/review_gate_blocks_on_critical_finding.evalset.json
```

We deliberately didn't hand-author fabricated eval cases here — an eval case is supposed to assert
against a *real* recorded trajectory, and faking one would just be a green checkmark that verifies
nothing. If you add real cases (this one, or new ones for the loop's completion condition, the
complexity-based model escalation, etc.), please contribute them back.
