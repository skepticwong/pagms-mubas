import os

file_path = 'models.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# We want to find the first '        }' at the end of the file that has redundant copies
# Let's search from the bottom for the last two '        }' lines

indices = []
for i in range(len(lines)):
    if lines[i].strip() == '}':
        # Check if it has 8 spaces
        if lines[i].startswith('        }'):
            indices.append(i)

if len(indices) >= 2:
    # We suspect the last one is the rogue one
    last_rogue = indices[-1]
    # Check if there are only whitespace/newlines between indices[-2] and indices[-1]
    between = lines[indices[-2]+1 : indices[-1]]
    is_mostly_empty = all(not b.strip() for b in between)
    
    if is_mostly_empty:
        new_lines = lines[:indices[-1]]
        # Also remove the specific index[-1] line if we accidentally kept it
        # Actually [:indices[-1]] excludes the rogue line
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            f.writelines(new_lines)
        print(f"Removed rogue closure at line {indices[-1] + 1}")
    else:
        print("Could not find a safe rogue closure to remove.")
else:
    print(f"Found {len(indices)} closures, needed at least 2.")
