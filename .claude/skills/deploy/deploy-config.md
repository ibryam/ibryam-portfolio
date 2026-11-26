# Deploy Config

Environment-specific deployment details. Fill this in per project.

## Environments

| Environment | URL | Branch | Deploy Command |
|-------------|-----|--------|----------------|
| Staging     | [staging URL] | main | [command] |
| Production  | [prod URL] | [tag/branch] | [command] |

## CI/CD

- Platform: [GitHub Actions / GitLab CI / etc.]
- Workflow file: [path]
- Manual trigger: [how to trigger a deploy manually]

## Infrastructure

- Hosting: [Fly.io / Railway / AWS / GCP / etc.]
- Database: [provider and how to run migrations]
- Secrets manager: [where env vars live]

## Monitoring

- Logs: [where to find them]
- Alerts: [how you get paged]
- Dashboard: [URL]
