#!/usr/bin/env python3
"""Update password in .env file from Q2OPostgres2025! to Q2OPostgres2025("""

from pathlib import Path

ENV_PATH = Path(r'C:\Q2O_Combined\.env')

if not ENV_PATH.exists():
    print(f'✗ .env file not found at {ENV_PATH}')
    exit(1)

content = ENV_PATH.read_text(encoding='utf-8')
lines = content.split('\n')
new_lines = []
updated = False

for line in lines:
    if 'Q2OPostgres2025!' in line:
        new_line = line.replace('Q2OPostgres2025!', 'Q2OPostgres2025(')
        new_lines.append(new_line)
        updated = True
        print(f'Updated: {line.strip()[:70]}...')
    else:
        new_lines.append(line)

if updated:
    ENV_PATH.write_text('\n'.join(new_lines), encoding='utf-8')
    print('✓ .env file updated with new password')
else:
    print('✓ .env file already has correct password or no password found')

