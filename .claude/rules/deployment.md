# Deployment

## Least-Privilege Account Model

Never grant sudo to service accounts. Use two separate accounts:

- **Personal admin user** — has sudo, used for system administration (apt, nginx, certbot, ufw)
- **`venturekeep` service account** — no sudo, used only for app operations (Docker, git, backups)

Switch to the service account with `sudo su - venturekeep`. System tasks always run from the personal account.

**Why:** If the app runtime is compromised, the attacker is confined to the unprivileged service account and cannot escalate to root. This also keeps audit trails clean — sudo logs show which human performed privileged actions.
