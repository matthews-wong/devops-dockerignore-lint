# devops-dockerignore-lint

Check a Docker build context before it ships. A missing or leaky
`.dockerignore` is how `.env` files, `.git` history and private keys end up
in an image layer, and how a 2 MB app turns into a 600 MB build context.

This is a small stdlib-only Python script. It reads the `.dockerignore`,
applies Docker's matching rules (root-anchored patterns, `**`, last match
wins, `!` re-includes) to a list of risky probe paths, and reports the ones
that would still be sent to the daemon.

Usage and rules are documented below as they land.
