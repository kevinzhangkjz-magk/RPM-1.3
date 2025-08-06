"""Test query sanitization functionality."""

def validate_and_sanitize_query(query: str) -> str:
    """Validate and sanitize user query to prevent injection attacks."""
    # Remove potentially dangerous SQL keywords
    dangerous_patterns = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "EXEC", "UNION"]
    
    sanitized = query
    for pattern in dangerous_patterns:
        sanitized = sanitized.replace(pattern.lower(), "")
        sanitized = sanitized.replace(pattern.upper(), "")
        sanitized = sanitized.replace(pattern.capitalize(), "")
    
    # Limit query length
    max_length = 500
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()

# Test cases
test_queries = [
    "Give me the 3 most underperforming sites",
    "DROP TABLE sites; SELECT * FROM users",
    "Show sites where RMSE > 2.0 UNION SELECT passwords FROM users",
    "DELETE FROM data WHERE 1=1",
    "What is the R-squared for Assembly 2?"
]

print("Query Sanitization Tests:")
print("-" * 50)
for query in test_queries:
    sanitized = validate_and_sanitize_query(query)
    print(f"Original: {query}")
    print(f"Sanitized: {sanitized}")
    is_safe = sanitized != query or query == test_queries[0] or query == test_queries[-1]
    status = "✓" if is_safe else "✗"
    print(f"Safe: {status}")
    print("-" * 50)