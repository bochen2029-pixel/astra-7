# Persona-test sysprompt assembly (local-only)

Sysprompts assembled per-variation by concatenating the K8 base + a chosen addendum:

```bash
cat /tmp/k8_base.md persona_tests/addenda/baseline.md > persona_tests/sysprompts/k8_baseline_v1.md
```

The K8 base is operator-local (canonical Katherine sysprompt). Addenda are in `persona_tests/addenda/` and committed. Final assembled sysprompts go here and are gitignored.
