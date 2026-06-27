# DNS & SSL

All products live under one hostname; routing is by path, not by subdomain.

```
ai.myndlabs.tech  ──A/AAAA──▶  HTTPS Load Balancer  ──▶  Cloud Run (mynd-core)
```

## Records

| Host | Type | Target |
| --- | --- | --- |
| `ai.myndlabs.tech` | A / AAAA | HTTPS LB IP (or `CNAME` to the Cloud Run domain mapping) |

## TLS

- Google-managed certificate for `ai.myndlabs.tech` on the load balancer
  (or Cloud Run domain mapping, which provisions a managed cert automatically).
- HTTP → HTTPS redirect enabled at the LB.

## Notes

- No per-product subdomains are required. `ai.myndlabs.tech/eng`,
  `/grc`, `/sales`, … all resolve to the same service; the
  `ProductContextMiddleware` derives the product from the first path segment.
- If per-product custom domains are ever needed, add additional domain mappings
  that point at the same service and set a default slug per domain.
