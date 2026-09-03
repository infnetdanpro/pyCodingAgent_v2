# Python Testing Skills

## Unit Testing Best Practices

### Test Structure
- Follow AAA pattern: Arrange, Act, Assert
- Keep tests independent and isolated
- Use descriptive test names that explain the scenario
- One assertion per concept (multiple asserts OK if testing same behavior)

### Fixtures and Setup
- Use pytest fixtures for reusable setup/teardown
- Scope fixtures appropriately (function, module, session)
- Keep test data minimal and focused
- Use parametrization for testing multiple inputs

### Mocking and Patching
- Mock external dependencies (APIs, databases, file systems)
- Use unittest.mock or pytest-mock
- Only mock what you don't control
- Verify mock calls with assertions

### Coverage Goals
- Aim for 80%+ code coverage
- Focus on branch coverage, not just line coverage
- Test edge cases and error conditions
- Don't chase 100% coverage at expense of test quality

### Test Categories
- Unit tests: Fast, isolated, no I/O
- Integration tests: Test component interactions
- End-to-end tests: Full system workflows
- Property-based tests: Test invariants with hypothesis

## Example Test Pattern

```python
import pytest
from unittest.mock import Mock, patch

class TestUserService:
    @pytest.fixture
    def mock_db(self):
        return Mock()
    
    @pytest.fixture
    def user_service(self, mock_db):
        return UserService(mock_db)
    
    def test_create_user_success(self, user_service, mock_db):
        # Arrange
        user_data = {"name": "John", "email": "john@example.com"}
        
        # Act
        result = user_service.create_user(user_data)
        
        # Assert
        assert result.name == "John"
        mock_db.insert.assert_called_once_with(user_data)
    
    @pytest.mark.parametrize("invalid_email", ["bad", "no@domain", "@missing.local"])
    def test_create_user_invalid_email(self, user_service, invalid_email):
        # Arrange
        user_data = {"name": "John", "email": invalid_email}
        
        # Act & Assert
        with pytest.raises(ValueError):
            user_service.create_user(user_data)
```
