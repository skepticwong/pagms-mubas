import os

# Use absolute path to avoid shell issues with parentheses
file_path = r'e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\backend\models.py'
fixed_path = r'e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\backend\models_fixed_final.py'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Truncate at line 1454 (index 1453)
    if len(lines) >= 1454:
        new_lines = lines[:1454]
        with open(fixed_path, 'w', encoding='utf-8', newline='') as f:
            f.writelines(new_lines)
        print(f"Successfully wrote {len(new_lines)} lines to {fixed_path}")
    else:
        print(f"File only has {len(lines)} lines, can't truncate at 1454")
except Exception as e:
    print(f"Error: {str(e)}")
