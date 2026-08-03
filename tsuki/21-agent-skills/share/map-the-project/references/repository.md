# Repository Module

Use this module to make a repository intelligible to a user deciding what it is for, how it works, and whether its present shape serves that purpose. Do not issue a formal engineering audit unless requested.

## Discover

- Read repository instructions, README files, manifests, entrypoints, build and test commands, deployment configuration, and relevant architecture documents.
- Identify the product or service boundary, primary users, runtime paths, major packages, external services, data stores, and operational dependencies.
- Compare stated intent with visible implementation and tests. Treat generated files, vendored code, and lockfiles as supporting evidence unless they are central to the question.

## Map

Use only dimensions that clarify the decision:

- purpose and user journey;
- entrypoints, runtime and delivery path;
- module responsibilities and dependency direction;
- data ownership and external contracts;
- test, deployment, and operational feedback loops;
- change hotspots, known debt, and constraints.

Describe architecture in terms of responsibility and interaction, not an unannotated directory listing. Separate documented design from inferred behavior.

## Assess

Assess fit for the repository's current goal, scale, risk, and expected change. State whether the evidence supports a clear path for ordinary changes and operations. Escalate to `repo-audit` when the user needs severity-ranked findings, architecture evolution, or behavior-preserving remediation.
