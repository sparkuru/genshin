# HackMyVM Lab Rules

Apply these rules to every lab below this directory.

## Ownership and safety

- Treat `writeup.md` as user-owned. Never create, edit, reformat, rename, move, or delete it unless the user explicitly asks for that file.
- Preserve `archive/` as immutable source material. Inspect it read-only, record hashes before extraction or conversion, and never overwrite, delete, mount read-write, or modify an archived artifact.
- Do not restore, rename, or overwrite unrelated user changes.
- Treat every target as vulnerable and untrusted. Default to loopback-only access, no bridged networking, no host networking, no privileged containers, no Docker socket mounts, and no writable broad host mounts.
- Do not download artifacts, start a target, run an exploit, retrieve flags, alter guest data, or scan undocumented endpoints unless the user explicitly asks.

## Lab layout

Use this layout for a lab at `<difficulty>/<NN>-<slug>/`. Do not create empty directories; create a component only when it has a concrete purpose.

```text
<difficulty>/<NN>-<slug>/
├── writeup.md             # user-owned; read-only by default
├── archive/               # original downloaded artifacts; ignored by Git
├── lab.md                 # agent-maintained facts, scope, and reproduction status
├── runtime/
│   ├── compose/           # tracked Compose files, Dockerfiles, and lifecycle wrappers
│   ├── qemu/              # tracked QEMU configuration and lifecycle wrappers
│   ├── images/            # derived disks/images; ignored by Git
│   └── state/             # overlays, PIDs, sockets, and logs; ignored by Git
├── scripts/               # tracked inspection and validation helpers
├── exploit/               # tracked, scoped PoCs or exploit helpers when requested
└── evidence/              # tracked, curated inventory and validation evidence
```

Use lowercase `<slug>` names with hyphens. Keep all generated material inside its lab; never place lab-specific files directly under a difficulty directory or the collection root.

## Durable files

Create or update `lab.md` only when agent assistance is requested. Keep it factual and concise:

- machine name, source URL, difficulty, and artifact hashes;
- artifact classification and reproduction tier;
- required host tools, loopback endpoints, and reset command;
- generated files, validation result, and known fidelity limitations.

Keep text configuration and reproducibility scripts versioned. Keep large derived images, mutable overlays, PID files, sockets, and runtime logs under ignored `runtime/images/` or `runtime/state/`. Do not commit flags, passwords, tokens, private keys, or large binary derivatives.

## Runtime and scripts

- Follow `$normalize-the-vm` when preparing a target. Preserve the QEMU/KVM path for VM-derived targets unless the skill's Docker eligibility gate is fully satisfied.
- Put Compose files and Dockerfiles in `runtime/compose/`; put QEMU arguments and wrappers in `runtime/qemu/`. If both exist, name wrappers explicitly: `run-compose.sh`, `stop-compose.sh`, `run-qemu.sh`, and `stop-qemu.sh`.
- Make lifecycle scripts non-interactive and idempotent. Validate arguments, quote paths, write mutable state only under `runtime/state/`, and clean up only PIDs/files that the script created.
- Bind every published or forwarded service port to `127.0.0.1`. Record the selected endpoint and its verification in `lab.md` or `evidence/`.
- Do not use `sudo`, `--privileged`, `network_mode: host`, Docker socket mounts, bridged/TAP networking, or recursive cleanup against a broad path without explicit user authorization.

## Exploit helpers and evidence

- Create files under `exploit/` only when the user requests a PoC, exploit, or challenge automation. Scope the default target to `127.0.0.1`; require an explicit target argument for any other address.
- Do not execute an exploit merely because it was created. Do not include retrieved flags or live credentials in the repository.
- Store only compact, reproducible evidence: hashes, sanitized command output, configuration excerpts, and documented endpoint checks. Do not store full disk copies, uncontrolled logs, or unreviewed sensitive captures.

## Completion

- Validate generated scripts with syntax checks and the narrowest safe lifecycle check available.
- Report the files created or changed, commands run, loopback listeners verified, and any unvalidated assumptions.
