# D4 Operational Runbook

Operational procedures for the `d4-sample` service (namespace `d4-sample`).
Commands assume `kubectl` is pointed at the target cluster
(`kubectl config use-context kind-d4-cluster` for local kind).

> Naming: Deployment / Service / ServiceAccount / PDB / HPA are all `d4-sample`;
> the ConfigMap is `d4-config`.

---

## 1. Deploy / upgrade

```bash
# Local kind (build + side-load + apply + verify, one shot)
make deploy                              # scripts/deploy-and-verify.sh

# Manual / remote cluster
kubectl apply -k k8s/overlays/dev        # or overlays/prod
kubectl rollout status deployment/d4-sample -n d4-sample --timeout=120s
```

A rollout uses `maxUnavailable: 0, maxSurge: 1` + `minAvailable: 1` PDB, so at
least one pod always serves traffic during the update.

## 2. Rollback

```bash
kubectl rollout history deployment/d4-sample -n d4-sample
kubectl rollout undo    deployment/d4-sample -n d4-sample            # previous revision
kubectl rollout undo    deployment/d4-sample -n d4-sample --to-revision=<N>
kubectl rollout status  deployment/d4-sample -n d4-sample
```

For prod, the image is digest-pinned in `k8s/overlays/prod/kustomization.yaml`;
roll back by pointing the digest at the previous image and re-applying.

## 3. Probe / health debugging

```bash
kubectl get pods -n d4-sample -o wide
kubectl describe pod -n d4-sample <pod>          # Events: probe failures, OOMKilled, ImagePull
```

| Symptom | Likely cause | Check |
|---|---|---|
| Pod stuck `0/1`, never Ready | readiness `/ready` failing | `kubectl logs`, then `curl` the pod (port-forward) |
| `CrashLoopBackOff` | startup error / liveness kill | `kubectl logs --previous`, look for the JSON `error` field |
| Restarts climbing | liveness `/health` failing under load | check `http_request_duration_seconds` p99, CPU throttling |

Probe contract: startup `/health` (≤60s budget: 30×2s), liveness `/health`
(10s period), readiness `/ready` (5s period). All target container port 8000.

## 4. Logs

Structured JSON on stdout — one object per request with `request_id`, `method`,
`path`, `status_code`, `duration_ms`.

```bash
kubectl logs deployment/d4-sample -n d4-sample --tail=100
kubectl logs deployment/d4-sample -n d4-sample -f                  # follow
kubectl logs deployment/d4-sample -n d4-sample | jq 'select(.status_code>=500)'
# Trace one request end-to-end by its echoed X-Request-ID header:
kubectl logs deployment/d4-sample -n d4-sample | jq 'select(.request_id=="<id>")'
```

## 5. Events / cluster state

```bash
kubectl get events -n d4-sample --sort-by=.lastTimestamp | tail -30
kubectl get deploy,rs,pods,svc,hpa,pdb,netpol -n d4-sample
```

## 6. Resource / scaling issues

```bash
kubectl top pods -n d4-sample                    # needs metrics-server
kubectl get hpa d4-sample -n d4-sample           # current vs target CPU, replica count
kubectl describe hpa d4-sample -n d4-sample      # scaling decisions / events
```

- **OOMKilled** (`describe pod` → Last State): raise `resources.limits.memory`
  (base 128Mi / prod 256Mi) in the overlay, re-apply.
- **CPU throttling** (latency up, CPU pinned at limit): raise `limits.cpu` or let
  the HPA scale out (CPU target 70%, base max 5 / prod max 10 replicas).
- **HPA not scaling**: confirm metrics-server is installed and `kubectl top`
  returns data; an HPA with `<unknown>` targets has no metrics source.

## 7. Metrics

```bash
kubectl port-forward -n d4-sample svc/d4-sample 18080:80
curl -s http://127.0.0.1:18080/metrics | grep -E 'http_requests_total|http_request_duration'
```

In-cluster scraping: annotation-based (`prometheus.io/scrape` on the pod) works
out of the box; the Prometheus Operator path is `k8s/base/servicemonitor.yaml`
(apply after installing kube-prometheus-stack).

## 8. Network policy

Ingress is default-deny; only port 8000 is reachable, and only from the
`d4-sample`, `ingress-nginx`, and `monitoring` namespaces (see
`k8s/base/networkpolicy.yaml`). If an in-cluster client gets connection
timeouts, confirm its namespace is allowed and that the CNI enforces
NetworkPolicy (kind's default `kindnet` does **not** — use Calico/Cilium to
test enforcement).

## 9. Teardown

```bash
kubectl delete -k k8s/overlays/dev        # remove app objects, keep cluster
make down                                 # delete the kind cluster
```
