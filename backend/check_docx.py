import sys
try:
    import docx
    status = "Installed"
except ImportError:
    status = "Not installed"

with open('docx_status.txt', 'w') as f:
    f.write(f"python-docx status: {status}\n")
    f.write(f"Python version: {sys.version}\n")
