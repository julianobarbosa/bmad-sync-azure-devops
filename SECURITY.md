# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest  | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

1. **Do not** open a public GitHub issue for security vulnerabilities
2. Email the maintainer directly or use [GitHub's private vulnerability reporting](https://github.com/cfpeterkozak/bmad-sync-azure-devops/security/advisories/new)
3. Include a description of the vulnerability and steps to reproduce

## Security Considerations

This workflow handles Azure DevOps Personal Access Tokens (PATs):

- PATs are read from the `AZURE_DEVOPS_EXT_PAT` environment variable only — never from files
- PATs are never logged, printed, or written to output files
- The `devops-sync-config.yaml` file stores connection settings but never credentials
- Scripts do not transmit data to any service other than the configured Azure DevOps organization

### Best Practices for Users

- Use PATs with the minimum required scope: **Work Items: Read, write, & manage**
- Set PAT expiration to the shortest practical duration
- Never commit PATs to version control
- Add `.env` to your `.gitignore` (already included in this project's `.gitignore`)
