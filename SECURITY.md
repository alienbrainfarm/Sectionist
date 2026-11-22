# Security Policy

## Supported versions

Sectionist has no versioned releases yet. Security fixes land on the `main`
branch only, so please make sure an issue still reproduces there before
reporting it.

| Version        | Supported |
| -------------- | --------- |
| `main`         | Yes       |
| Anything older | No        |

## Reporting a vulnerability

**Please do not open a public issue, pull request or discussion for a security
problem.**

Report it privately through GitHub instead:

1. Go to the repository's **Security** tab.
2. Choose **Report a vulnerability**. You can also go straight to
   <https://github.com/alienbrainfarm/Sectionist/security/advisories/new>.
3. Describe the problem and include:
   - what an attacker could do and what they would need (local access, a
     crafted audio file, network access to the backend, and so on)
   - steps or a minimal file that reproduce it
   - the commit you tested and your operating system and Python version
   - a suggested fix, if you have one

Only the maintainers can see what you submit. You should get a first reply
within 7 days. We will keep you informed while we work on a fix, and we will
credit you in the advisory unless you ask us not to.

## Scope

Sectionist is a desktop app. Its Flask backend is meant to serve only the local
frontend, and it listens on `127.0.0.1` by default.

These are in scope:

- Problems in the backend's handling of uploaded files, such as path traversal,
  writing outside the temporary directory, or resource exhaustion from crafted
  audio.
- Leaking file paths, stack traces or other internal details in API responses.
- Problems in the frontend, the `tools/` scripts or the CI workflows.

These are out of scope:

- Problems that only exist because the backend was exposed to an untrusted
  network on purpose, for example with `SECTIONIST_HOST=0.0.0.0` or
  `SECTIONIST_DEBUG=1`. Neither setting is supported for untrusted networks.
- Vulnerabilities in third-party dependencies such as librosa, PyTorch, Demucs
  or Qt that Sectionist does not make worse. Please report those upstream.
  Do tell us if Sectionist needs to update or pin a dependency because of one.
