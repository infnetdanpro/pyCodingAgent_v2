# sec Rules

## auth
- Never hardcode creds or API keys
- Use env vars for sensitive config
- impl rate limiting for auth endpoints

## Data Validation
- Validate all user inputs b4 processing
- Use parameterized queries to prevent SQL injection
- Sanitize HTML output to prevent XSS attacks

## File ops
- Validate file paths to prevent dir traversal
- Check file permissions b4 reading/writing
- Never run user-provided file paths
