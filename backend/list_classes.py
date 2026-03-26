import os
import ast

backend_path = r'e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\backend'

for root, dirs, files in os.walk(backend_path):
    for file in files:
        if file.endswith('.py'):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    node = ast.parse(f.read())
                
                classes = [n.name for n in node.body if isinstance(n, ast.ClassDef)]
                if classes:
                    print(f"File: {file_path}")
                    for cls in classes:
                        print(f"  Class: {cls}")
            except Exception as e:
                # print(f"Error reading {file_path}: {e}")
                pass
