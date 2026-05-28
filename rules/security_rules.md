# Security Rules

## Authentication
- Never hardcode credentials or API keys
- Use environment variables for sensitive configuration
- Implement rate limiting for authentication endpoints

## Data Validation
- Validate all user inputs before processing
- Use parameterized queries to prevent SQL injection
- Sanitize HTML output to prevent XSS attacks

## File Operations
- Validate file paths to prevent directory traversal
- Check file permissions before reading/writing
- Never execute user-provided file paths
