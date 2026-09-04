# Python Modernization Cheat Sheet
## From Basic to Professional Python

### 1. File Operations

```python
# ❌ OLD WAY
import os
f = open('file.json', 'r')
data = json.load(f)
f.close()

# ✅ MODERN WAY
from pathlib import Path
with open('file.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# ✅ EVEN BETTER (pathlib)
path = Path('file.json')
with path.open('r', encoding='utf-8') as f:
    data = json.load(f)
```

### 2. Dictionary Operations

```python
# ❌ OLD WAY
data = {}
i = 0
for detail in df['detail']:
    data[i] = {
        'title': df['detail'][i]['title'],
        'length': df['detail'][i]['length'],
    }
    i += 1

# ✅ MODERN WAY (list comprehension)
data = [
    {
        'title': detail['title'],
        'length': detail['length'],
    }
    for detail in df['detail']
]

# ✅ EVEN BETTER (enumerate)
data = {
    i: {
        'title': detail['title'],
        'length': detail['length'],
    }
    for i, detail in enumerate(df['detail'])
}
```

### 3. Conditional Initialization

```python
# ❌ OLD WAY
if title not in movies:
    movies[title] = {'showings': {}}
movies[title]['showings'][date] = times

# ✅ MODERN WAY (defaultdict)
from collections import defaultdict
movies = defaultdict(lambda: {'showings': {}})
movies[title]['showings'][date] = times

# ✅ ALTERNATIVE (setdefault)
movies.setdefault(title, {'showings': {}})
movies[title]['showings'][date] = times
```

### 4. Safe Dictionary Access

```python
# ❌ OLD WAY
if 'Actores:' in movie['details']:
    actors = movie['details']['Actores:']
else:
    actors = None

# ✅ MODERN WAY
actors = movie.get('details', {}).get('Actores:')

# ✅ WITH DEFAULT
actors = movie.get('details', {}).get('Actores:', [])
```

### 5. String Formatting

```python
# ❌ OLD WAY
print("Found " + str(len(movies)) + " movies in " + theater)

# ❌ SLIGHTLY BETTER
print("Found %d movies in %s" % (len(movies), theater))

# ✅ MODERN WAY (f-strings)
print(f"Found {len(movies)} movies in {theater}")

# ✅ MULTI-LINE
message = (
    f"Cinema: {theater}\n"
    f"Movies: {len(movies)}\n"
    f"Date: {date}"
)
```

### 6. List Building

```python
# ❌ OLD WAY
titles = []
for movie in movies:
    titles.append(movie['title'])

# ✅ MODERN WAY (list comprehension)
titles = [movie['title'] for movie in movies]

# ✅ WITH FILTER
titles = [m['title'] for m in movies if m['age'] == '12']

# ✅ GENERATOR (memory efficient for large data)
titles = (movie['title'] for movie in movies)
```

### 7. Dictionary Building

```python
# ❌ OLD WAY
result = {}
for key, value in data.items():
    result[key] = transform(value)

# ✅ MODERN WAY (dict comprehension)
result = {key: transform(value) for key, value in data.items()}

# ✅ WITH FILTER
result = {k: v for k, v in data.items() if v > 0}
```

### 8. Error Handling

```python
# ❌ OLD WAY
try:
    process_file(filename)
except:  # Don't do this!
    print("Error")

# ✅ MODERN WAY
try:
    process_file(filename)
except FileNotFoundError:
    print(f"File not found: {filename}")
except json.JSONDecodeError as e:
    print(f"Invalid JSON: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
    import traceback
    traceback.print_exc()
```

### 9. Function Arguments

```python
# ❌ OLD WAY
def normalize(input_file, output_file):
    # No type hints, hard to understand

# ✅ MODERN WAY
def normalize(input_file: str, output_file: str) -> List[Dict[str, Any]]:
    """
    Normalize cinema data
    
    Args:
        input_file: Path to raw JSON
        output_file: Path to save normalized data
        
    Returns:
        List of normalized movie dictionaries
    """
    pass

# ✅ WITH DEFAULTS
def normalize(
    input_file: str,
    output_file: str,
    indent: int = 2,
    ensure_ascii: bool = False
) -> List[Dict[str, Any]]:
    pass
```

### 10. Class Design

```python
# ❌ OLD WAY (procedural)
def load_yelmo(filename):
    pass

def normalize_yelmo(data):
    pass

def save_yelmo(data, filename):
    pass

# ✅ MODERN WAY (OOP)
class YelmoNormalizer:
    def __init__(self, input_path: str, output_path: str):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
    
    def load_data(self) -> List[Dict]:
        """Load raw data"""
        pass
    
    def normalize(self) -> List[Dict]:
        """Transform data"""
        pass
    
    def save_data(self, data: List[Dict]) -> None:
        """Save normalized data"""
        pass
```

### 11. Data Classes

```python
# ❌ OLD WAY
def make_movie(title, length, age):
    return {
        'title': title,
        'length': length,
        'age': age,
    }

movie = make_movie("Inception", "148 min", "PG-13")
print(movie['title'])  # No autocomplete

# ✅ MODERN WAY (dataclass)
from dataclasses import dataclass

@dataclass
class Movie:
    title: str
    length: str
    age: str
    
    def to_dict(self) -> dict:
        return {
            'title': self.title,
            'length': self.length,
            'age': self.age,
        }

movie = Movie("Inception", "148 min", "PG-13")
print(movie.title)  # Autocomplete works!
```

### 12. JSON Handling

```python
# ❌ OLD WAY
json.dump(data, f)  # Escaped unicode, no formatting

# ✅ MODERN WAY
json.dump(
    data,
    f,
    ensure_ascii=False,  # Proper UTF-8
    indent=2,            # Pretty print
    sort_keys=False      # Preserve order
)
```

### 13. Path Operations

```python
# ❌ OLD WAY
import os
filename = 'data_raw/yelmo_raw.json'
directory = os.path.dirname(filename)
if not os.path.exists(directory):
    os.makedirs(directory)

# ✅ MODERN WAY
from pathlib import Path
path = Path('data_raw/yelmo_raw.json')
path.parent.mkdir(parents=True, exist_ok=True)

# ✅ USEFUL PATH OPERATIONS
path.exists()        # Check if exists
path.stem            # Filename without extension
path.suffix          # Extension (.json)
path.name            # Full filename
path.parent          # Parent directory
list(path.glob('*.json'))  # Find all JSON files
```

### 14. Iteration

```python
# ❌ OLD WAY
i = 0
for item in items:
    print(f"{i}: {item}")
    i += 1

# ✅ MODERN WAY (enumerate)
for i, item in enumerate(items):
    print(f"{i}: {item}")

# ✅ START FROM 1
for i, item in enumerate(items, start=1):
    print(f"{i}: {item}")
```

### 15. Zipping Iterables

```python
# ❌ OLD WAY
for i in range(len(titles)):
    print(titles[i], lengths[i])

# ✅ MODERN WAY (zip)
for title, length in zip(titles, lengths):
    print(title, length)

# ✅ CREATE DICT FROM TWO LISTS
movie_data = dict(zip(titles, lengths))
```

### 16. Sorting

```python
# ❌ OLD WAY
movies.sort()  # Modifies in place

# ✅ MODERN WAY (returns new list)
sorted_movies = sorted(movies)

# ✅ CUSTOM SORT KEY
sorted_movies = sorted(movies, key=lambda m: m['title'])

# ✅ USING OPERATOR
from operator import itemgetter
sorted_movies = sorted(movies, key=itemgetter('title'))

# ✅ MULTIPLE KEYS
sorted_movies = sorted(movies, key=lambda m: (m['date'], m['time']))
```

### 17. Grouping Data

```python
# ❌ OLD WAY
groups = {}
for item in items:
    key = item['category']
    if key not in groups:
        groups[key] = []
    groups[key].append(item)

# ✅ MODERN WAY (defaultdict)
from collections import defaultdict
groups = defaultdict(list)
for item in items:
    groups[item['category']].append(item)

# ✅ USING itertools.groupby (for sorted data)
from itertools import groupby
items.sort(key=lambda x: x['category'])
for category, group in groupby(items, key=lambda x: x['category']):
    print(category, list(group))
```

### 18. Set Operations

```python
# Get unique values
unique_titles = set(movie['title'] for movie in movies)

# Set operations
theater_a = {'Movie1', 'Movie2', 'Movie3'}
theater_b = {'Movie2', 'Movie3', 'Movie4'}

theater_a & theater_b  # Intersection: {'Movie2', 'Movie3'}
theater_a | theater_b  # Union: {'Movie1', 'Movie2', 'Movie3', 'Movie4'}
theater_a - theater_b  # Difference: {'Movie1'}
```

### 19. Any/All

```python
# ❌ OLD WAY
has_showing = False
for movie in movies:
    if movie['showings']:
        has_showing = True
        break

# ✅ MODERN WAY
has_showing = any(movie['showings'] for movie in movies)

# Check if all movies have synopsis
all_have_synopsis = all(movie.get('synopsis') for movie in movies)
```

### 20. Main Guard

```python
# ❌ OLD WAY
normalize_all()  # Runs when imported!

# ✅ MODERN WAY
def main():
    normalize_all()

if __name__ == '__main__':
    main()  # Only runs when executed directly
```

## Quick Reference

### When to use what:

| Task | Tool |
|------|------|
| Build a list | List comprehension |
| Build a dict | Dict comprehension |
| Group items | `defaultdict` or `groupby` |
| Deduplicate | `set()` |
| Safe dict access | `.get()` |
| Format strings | f-strings |
| File operations | `pathlib.Path` |
| Iteration with index | `enumerate()` |
| Parallel iteration | `zip()` |
| Sorting | `sorted()` with `key=` |
| Memory-efficient iteration | Generator expression `()` |

### Common Imports

```python
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from itertools import groupby
from operator import itemgetter, attrgetter
import json
from datetime import datetime
```