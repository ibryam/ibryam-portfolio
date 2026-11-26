# Deploy Skill

Auto-loaded when the task involves deployment. Keeps deployment knowledge out of the main CLAUDE.md.

## Trigger Keywords

This skill is relevant when the user mentions: deploy, release, ship, publish, push to production, go live, rollout.

## Pre-Deploy Checklist

Before any deployment, verify:
- [ ] All tests pass locally and in CI
- [ ] No uncommitted changes (`git status` is clean)
- [ ] Environment variables are set in the target environment
- [ ] Database migrations are backwards-compatible (can run before code deploys)
- [ ] The change can be rolled back safely

## Deployment Process

See `deploy-config.md` for environment-specific commands and targets.

General order:
1. Run pre-deploy checklist
2. Tag the release: `git tag v[version]`
3. Run migrations (if any) before deploying new code
4. Deploy code
5. Verify: smoke test the critical path in production
6. Monitor logs for 10 minutes after deploy

## Rollback

If anything is wrong after deploy:
1. Revert to the previous tag immediately — ask the user before doing this
2. Run rollback migrations if needed
3. Investigate in the old version, fix forward in a new release

## Rules

- Never deploy directly to production without a staging verification first
- Always confirm with the user before triggering a production deploy
- Never force-push a release tag
