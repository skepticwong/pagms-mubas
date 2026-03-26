import os

root_dir = r'e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\frontend\src'

for root, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith(('.svelte', '.js', '.ts')):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                new_content = content.replace('http://localhost:5000/api', '/api')
                # Also handle case where it's just 'http://localhost:5000' without /api (e.g. for uploads)
                new_content = new_content.replace('http://localhost:5000', '')
                
                if new_content != content:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Fixed: {path}")
            except Exception as e:
                print(f"Error fixing {path}: {e}")
