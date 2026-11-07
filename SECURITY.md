# Security and disclosure

This package is an experiment, not a certification or production security layer.
Review downloaded source and compare its digest with a trusted publication record.
Checksums identify bytes; anyone able to rewrite a package can rewrite checksums.

External candidate code is disabled by default. `--accept-external-code` is explicit
consent, not sufficient isolation by itself: the launcher additionally requires
Linux bubblewrap with new user/PID/IPC/network namespaces, dropped capabilities,
a read-only `/usr` runtime and candidate files, no host home or credentials,
cleared environment, bounded output/address space/CPU and a two-second deadline.
Scratch resides in the configured persistent TMPDIR. Unavailable isolation fails;
there is no automatic unisolated fallback or installation of dependencies.

`isolation_checks.py` tests host-path/environment exclusion, read-only mounts,
no default network route, timeout and invalid/oversized output rejection. These
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
