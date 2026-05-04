# fg-data-profiling (oasis fork) — Context

## What this is
Fork of Data-Centric-AI-Community/fg-data-profiling (MIT, descended from ydataai/ydata-profiling MIT), maintained at oasis-main/fg-data-profiling.

## Why we forked
fg-data-profiling is a Pandas/Spark profiling tool descended from ydata-profiling/pandas-profiling. We fork to (a) integrate with the oasis-data storage layer, (b) match the oasis-data brand surface, and (c) bundle profiling reports as a service alongside argilla labeling under a unified oasis-data product.

## Strategic position
Part of the **oasis-data** cloud product line. Sibling forks:
- oasis-main/argilla — interactive labeling / curation UI
- oasis-main/fg-data-profiling — automated profiling / EDA

Both rebrand under the oasis-data umbrella with custom UI, better social collaboration features, and tighter integration with the rest of the Oasis ecosystem (oasis-auth, oasis-cloud, oasis-dashboard).

## Deployment trajectory (per oasis-claw pattern)
1. Local container (docker-compose) — running on dev laptops + LAN
2. LAN collaboration — multiple researchers pointing at one shared instance
3. Production — research-client deployments + public SaaS via oasis-cloud

## License posture
Upstream is permissive (Apache-2.0 / MIT). Fork retains upstream license for shared code; new oasis-specific modules are dual-licensed Apache-2.0 + commercial. Trademark: "oasis-data" branding in our distribution; preserve upstream NOTICE/copyright for redistributed code.

## Key upstream branches to track
- `develop` — upstream's active branch (our default)
- `main` — upstream's release branch
We rebase oasis-* feature branches off upstream develop weekly.
