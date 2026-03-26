import os

file_path = 'models.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find all lines that consist only of an optional whitespace and a closing brace
indices = [i for i, line in enumerate(lines) if line.strip() == '}']

if len(indices) >= 2:
    # Truncate after the second-to-last closing brace
    # Wait, the very last one is definitely the rogue one if it's after the good one.
    # We want to remove line 1457 (index 1456)
    # The last known good one is 1454 (index 1453)
    
    rogue_index = indices[-1]
    good_index = indices[-2]
    
    print(f"Indices of braces: {indices}")
    
    if rogue_index > good_index + 1:
        # Check if there's only whitespace between them
        between = "".join(lines[good_index+1:rogue_index]).strip()
        if not between:
             new_lines = lines[:rogue_index]
             with open(file_path, 'w', encoding='utf-8') as f:
                 f.writelines(new_lines)
             print(f"Successfully truncated file at line {rogue_index}")
        else:
             print(f"Found content between braces: {repr(between)}")
    else:
        # They are adjacent?
        new_lines = lines[:rogue_index]
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"Removed adjacent rogue brace at line {rogue_index + 1}")
else:
    print(f"Only found {len(indices)} braces, can't safely truncate.")
