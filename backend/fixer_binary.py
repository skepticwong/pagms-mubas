import os

file_path = 'models.py'
if not os.path.exists(file_path):
    print(f"Error: {file_path} not found")
    exit(1)

with open(file_path, 'rb') as f:
    content = f.read()

# Try different line endings for '        }\n\n\n        }'
rogue_variants = [
    b'        }\r\n\r\n\r\n        }',
    b'        }\n\n\n        }',
    b'        }\r\n\r\n        }',
    b'        }\n\n        }',
]

fixed = False
for variant in rogue_variants:
    if variant in content:
        # We want to keep ONLY the first '        }'
        new_content = content.replace(variant, variant.split(b'}')[0] + b'}')
        with open(file_path, 'wb') as f:
            f.write(new_content)
        print(f"Fixed variant: {repr(variant)}")
        fixed = True
        break

if not fixed:
    # Aggressive fallback: search for the last occurrence of '        }' and check if it's redundant
    last_idx = content.rfind(b'        }')
    prev_idx = content.rfind(b'        }', 0, last_idx)
    
    if prev_idx != -1:
        # Check if there's only whitespace between them
        between = content[prev_idx+10 : last_idx].strip()
        if not between:
             new_content = content[:last_idx]
             with open(file_path, 'wb') as f:
                 f.write(new_content)
             print("Fixed via aggressive fallback")
             fixed = True

if not fixed:
    print("Could not find rogue closure")
