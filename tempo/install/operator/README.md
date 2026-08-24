# Tempo — Tempo Operator (Kubernetes)

The Tempo Operator manages Tempo deployments via the `TempoStack` CRD.

## Install operator

```bash
# Via OLM (OpenShift)
# Or via manifests:
kubectl apply -f https://github.com/grafana/tempo-operator/releases/latest/download/tempo-operator.yaml
```

## Deploy a TempoStack

```bash
kubectl apply -f tempostack.yaml
kubectl get tempostacks -n tempo
```

## Notes

- The operator manages lifecycle, scaling, and upgrades.
- Requires object storage configured in the `TempoStack` CR.
- For simpler deployments, use the [Helm charts](../helm/) directly.

Official source: [Tempo Operator](https://grafana.com/docs/tempo/latest/set-up-for-tracing/setup-tempo/deploy/kubernetes/operator/).
