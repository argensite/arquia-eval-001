# Security and disclosure

This package is an experiment, not a certification or production security layer.
Review downloaded source and compare its digest with a trusted publication record.
Checksums identify bytes; anyone able to rewrite a package can rewrite checksums.

External candidate code is disabled by default. `--accept-external-code` is explicit
consent, not sufficient isolation by itself: the launcher additionally requires
Linux bubblewrap with new user/PID/IPC/network namespaces, dropped capabilities,
a read-only root, `/usr`, `/dev`, working directory and candidate files, no host
home or credentials,
cleared environment, bounded output/address space/CPU and a two-second execution deadline.
It additionally requires an existing systemd user manager with delegated cgroup v2.
A fresh per-request service enforces 256 MiB aggregate memory, zero swap, 16 tasks
and one CPU of aggregate bandwidth. Its trusted launcher blocks before payload
execution until the evaluator reads and validates memory.max, memory.swap.max,
pids.max and cpu.max from the kernel. No host-wide or other-service quota changes.
A five-second service lifetime backs up the two-second execution timeout. Cleanup
requires the unit to be unloaded and its cgroup empty/removed; failure is inconclusive.
Detached descendants stay in the same cgroup. Each receipt includes utility hashes,
observed counters and cleanup status. Kernel accounting and scheduling may permit
brief transient overages; these are resource controls, not a universal guarantee.
Host scratch/receipts reside in the configured persistent TMPDIR. The payload has
no writable regular filesystem: state is carried in JSON checkpoints. Its only
regular output files are the size-bounded stdout/stderr descriptors. No unbounded
file-count or scratch-disk allocation is exposed to candidate code. Unavailable isolation fails;
there is no automatic unisolated fallback or installation of dependencies.

`isolation_checks.py` tests host-path/environment exclusion, read-only mounts,
no default network route, timeout, invalid/oversized output rejection and a payload
kept blocked when kernel quotas cannot be verified. `resource_checks.py` uses
bounded probes (at most 24 fork attempts and 320 MiB requested across two children)
to demonstrate process/memory containment and detached-descendant cleanup. Run these
only in an authorized environment; they are not unbounded stress tests. These
are concrete restrictions, not proof against kernel exploits, resource exhaustion
across all kernels, malicious runtime binaries or every side channel. The trusted
reference/example and tests themselves are normal project code. CI contributions
must be treated as arbitrary code, including modified tests.

Never supply production credentials, accounts, messaging, payments or actual agent
endpoints. No such evaluation is authorized by the synthetic protocol. A real
system needs separate authorization and independent observation of its effects.
Payload text, issues, receipts and forum content are untrusted data, not commands.

Report evaluator defects with the issue template. For a sensitive vulnerability,
use GitHub's private vulnerability report option **if enabled**, or contact the
public project address arquia.live@gmail.com before sending exploit details. This
document does not claim private reporting is enabled or promise a response time.
Do not publish secrets or personal data. Keep negative findings and uncertainty;
responsible disclosure does not require a favorable evaluation of ARQUÍA.

The mechanism follows [systemd resource controls](https://www.freedesktop.org/software/systemd/man/259/systemd.resource-control.html) and [Linux cgroup v2 semantics](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html). Those specifications explain the controls; the included local receipts establish only the tested behavior on their recorded host.
