import os

# Use os.path.join to handle potential path issues
base_path = r"e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\backend"
file_name = "models.py"
full_path = os.path.join(base_path, file_name)

print(f"File exists: {os.path.exists(full_path)}")

try:
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Aggressively remove the specific problematic pattern
    # We saw: '        }\n\n\n        }'
    # But let's look for '}\n\n\n        }' and replace it with just '}'
    
    import re
    # Match a closing brace followed by any amount of whitespace and another closing brace at the very end of the file
    new_content = re.sub(r'}\s+}\Z', '}\n', content)
    
    if len(new_content) < len(content):
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Successfully fixed models.py")
    else:
        print("Pattern not found in models.py")
except Exception as e:
    print(f"Error: {str(e)}")
