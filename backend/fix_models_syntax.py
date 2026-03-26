import os

file_path = 'models.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the last to_dict method end for ReviewerNote
# We know from view_file it's around 1454
# But let's be safe and search for the second to last '        }'

count = 0
last_good_line = -1
for i in range(len(lines) - 1, -1, -1):
    if lines[i].strip() == '}':
        count += 1
        if count == 2: # The second one from bottom should be the good one
            last_good_line = i
            break

if last_good_line != -1:
    new_lines = lines[:last_good_line + 1]
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"Successfully truncated {file_path} at line {last_good_line + 1}")
else:
    print("Could not find the truncation point safely.")
