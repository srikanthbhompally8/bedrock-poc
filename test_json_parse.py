import json

response = '''```json
{
    "job_title": "Senior Python Developer",
    "company": "Not specified",
    "years_required": 5,
    "core_skills": [
        {"name": "Python", "proficiency": "expert", "importance": 9},
        {"name": "PostgreSQL", "proficiency": "intermediate", "importance": 8},
        {"name": "Django", "proficiency": "intermediate", "importance": 8}
    ],
    "nice_to_have": ["Kubernetes", "AWS"],
    "education": "BS Computer Science",
    "salary_min": 120000,
    "salary_max": 160000
}
```'''

# Extract JSON
json_start = response.find('{')
brace_count = 0
json_end = -1

for i in range(json_start, len(response)):
    if response[i] == '{':
        brace_count += 1
    elif response[i] == '}':
        brace_count -= 1
        if brace_count == 0:
            json_end = i + 1
            break

json_str = response[json_start:json_end]

print("Extracted JSON:")
print(repr(json_str[:100]))
print()

try:
    data = json.loads(json_str)
    print("SUCCESS! Parsed data:")
    print(data)
except json.JSONDecodeError as e:
    print(f"ERROR: {e}")
    print(f"Problematic area around position {e.pos}:")
    start = max(0, e.pos - 50)
    end = min(len(json_str), e.pos + 50)
    print(repr(json_str[start:end]))
