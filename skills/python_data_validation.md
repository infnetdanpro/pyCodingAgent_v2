# Python Data Validation Skills

## Type Hints and Annotations

### Basic Type Hints
- Use `str`, `int`, `float`, `bool` for primitives
- Use `list[T]`, `dict[K, V]`, `tuple[T, ...]` for collections
- Use `Optional[T]` or `T | None` for nullable values
- Use `Union[T, U]` or `T | U` for multiple types

### Advanced Types
- `Callable[[ArgType], ReturnType]` for functions
- `Literal["value1", "value2"]` for specific values
- `TypedDict` for dictionary structures
- `Protocol` for structural subtyping
- `Generic[T]` for generic classes

## Runtime Validation Libraries

### Pydantic (Recommended)
```python
from pydantic import BaseModel, Field, validator, EmailStr
from datetime import datetime
from typing import Optional

class User(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(ge=0, le=150)
    created_at: datetime = Field(default_factory=datetime.now)
    bio: Optional[str] = None
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('name cannot be empty')
        return v.title()
    
    class Config:
        extra = 'forbid'  # Reject unknown fields

# Usage
user = User(id=1, name="john", email="john@example.com", age=30)
```

### Data Classes with Validation
```python
from dataclasses import dataclass, field
from typing import List, Optional
import re

@dataclass
class Product:
    name: str
    price: float
    tags: List[str] = field(default_factory=list)
    discount: Optional[float] = None
    
    def __post_init__(self):
        if self.price < 0:
            raise ValueError("price must be positive")
        if self.discount is not None and not 0 <= self.discount <= 100:
            raise ValueError("discount must be between 0 and 100")
```

## Custom Validators

### Decorator Pattern
```python
from functools import wraps
from typing import Callable, Any

def validate_types(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # Add type checking logic
        return func(*args, **kwargs)
    return wrapper

def validate_positive(field_name: str):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if kwargs.get(field_name, 0) <= 0:
                raise ValueError(f"{field_name} must be positive")
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

### Schema Validation
```python
from marshmallow import Schema, fields, validate, validates, ValidationError

class UserSchema(Schema):
    id = fields.Int(required=True, validate=validate.Range(min=1))
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True)
    role = fields.Str(validate=validate.OneOf(['admin', 'user', 'guest']))
    
    @validates('username')
    def validate_username(self, value):
        if not value.isalnum():
            raise ValidationError('Username must be alphanumeric')

schema = UserSchema()
result = schema.load({'id': 1, 'username': 'john123', 'email': 'john@example.com'})
```

## Best Practices

### Input Validation Rules
- Validate at system boundaries (API endpoints, file I/O)
- Fail fast on invalid input
- Provide clear error messages
- Never trust user input
- Sanitize output as well as validating input

### Performance Considerations
- Use static type checking (mypy, pyright) for compile-time validation
- Choose validation library based on needs (Pydantic for speed, Marshmallow for flexibility)
- Cache validation schemas when possible
- Avoid over-validation in performance-critical paths

### Security
- Validate all external inputs
- Use parameterized queries to prevent SQL injection
- Sanitize HTML/JavaScript to prevent XSS
- Validate file types and sizes
- Check authorization after validation
