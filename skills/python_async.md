# Python Async Programming Skills

## Async/Await Fundamentals

### When to Use Async
- I/O-bound operations (network, disk, database)
- High concurrency requirements
- WebSocket or long-polling connections
- Multiple external API calls

### Core Concepts
- `async def`: Define coroutine functions
- `await`: Pause execution until awaitable completes
- `asyncio.run()`: Entry point for async programs
- `asyncio.gather()`: Run multiple coroutines concurrently
- `asyncio.wait_for()`: Add timeouts to operations

## Best Practices

### Error Handling
- Wrap awaited calls in try/except blocks
- Use context managers for resource cleanup
- Handle CancelledError gracefully
- Propagate exceptions appropriately

### Concurrency Patterns
- Use `asyncio.Semaphore` for limiting concurrent operations
- Implement connection pooling for databases/APIs
- Use queues for producer-consumer patterns
- Avoid blocking calls in async code

### Common Pitfalls
- Don't mix blocking and async code
- Avoid `asyncio.sleep(0)` unless yielding intentionally
- Be careful with mutable default arguments
- Watch for unawaited coroutines

## Code Examples

```python
import asyncio
import aiohttp
from contextlib import asynccontextmanager

# Basic async function
async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()

# Concurrent execution with gather
async def fetch_all(urls: list[str]) -> list[dict]:
    tasks = [fetch_data(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]

# Semaphore for limiting concurrency
async def fetch_with_limit(urls: list[str], max_concurrent: int = 5) -> list[dict]:
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def bounded_fetch(url: str) -> dict:
        async with semaphore:
            return await fetch_data(url)
    
    tasks = [bounded_fetch(url) for url in urls]
    return await asyncio.gather(*tasks)

# Timeout handling
async def fetch_with_timeout(url: str, timeout: float = 5.0) -> dict | None:
    try:
        return await asyncio.wait_for(fetch_data(url), timeout=timeout)
    except asyncio.TimeoutError:
        print(f"Request to {url} timed out")
        return None

# Async context manager
@asynccontextmanager
async def get_connection(pool):
    conn = await pool.acquire()
    try:
        yield conn
    finally:
        await pool.release(conn)

# Producer-consumer pattern
async def producer(queue: asyncio.Queue, items: list):
    for item in items:
        await queue.put(item)
    await queue.put(None)  # Sentinel value

async def consumer(queue: asyncio.Queue):
    while True:
        item = await queue.get()
        if item is None:
            break
        await process_item(item)
        queue.task_done()
```

## Testing Async Code

```python
import pytest
import asyncio

async def test_async_function():
    result = await fetch_data("https://api.example.com/data")
    assert "key" in result

@pytest.mark.asyncio
async def test_concurrent_operations():
    urls = ["http://example.com/1", "http://example.com/2"]
    results = await fetch_all(urls)
    assert len(results) == 2

async def test_timeout():
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(
            asyncio.sleep(10),
            timeout=1.0
        )
```
