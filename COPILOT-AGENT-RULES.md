# GitHub Copilot Agent - Development Rules & Context

## Git & Deployment Workflow

### Branch Management
- **Only merge to `dev` branch** - Never merge directly to `main`
- When ready for production, notify me to create a PR from `dev` to `main` with a summary of changes
- One logical fix per commit when possible

### Deployment Process
- **No local Terraform** - Use manual GitHub Actions workflows:
  - Deploy Infra
  - Deploy Backend 
  - Deploy Frontend
- I will trigger these workflows manually after code merges to `main`

## Development Environment

### Platform Requirements
- **Windows PowerShell only** - All terminal commands must be PowerShell compatible
- **Frontend via WSL Ubuntu** - Notify me when you need to run `npm run build` or other frontend commands locally
- **Backend testing on AWS only** - No local backend testing due to Docker issues

## Code Quality & Documentation

### Commit Message Standards
- **Technical accuracy required** - No marketing slogans or promotional language
- **Conservative tone** - Use emojis sparingly, avoid celebratory emojis until code is tested
- **Document reality** - If a fix doesn't work, mention it in the commit message
- **Amendable commits** - Update commit messages after testing to reflect actual results

### Planning & Progress Tracking
- **Planning mode** - When requested, provide action plan with 2-3 options including pros/cons
- **Roadmap documentation** - Create markdown roadmap after solution agreement and update progress continuously

## Additional Productivity Guidelines

### Code Organization
- **Feature flags** - Use feature flags for incomplete features to maintain deployable main branch
- **Error handling** - Include comprehensive error handling and logging for easier debugging
- **Code comments** - Add clear comments explaining complex business logic and non-obvious decisions

### Testing Strategy
- **Pre-deployment checks** - Always include a checklist of manual tests to perform after deployment
- **Rollback plan** - Include rollback instructions in deployment-related commits
- **Configuration management** - Document any environment-specific configurations or secrets needed

### Communication
- **Status updates** - Provide regular progress updates when working on complex features
- **Dependency tracking** - Flag any external dependencies or blockers early
- **Documentation updates** - Update relevant documentation (README, API docs) alongside code changes

### Performance Considerations
- **Resource monitoring** - Include performance implications in commit messages for significant changes
- **Cost awareness** - Flag any changes that might impact AWS costs
- **Scalability notes** - Document any architectural decisions that affect system scalability