#!/usr/bin/env python3
"""Update DB_DSN in .env to use existing 'q2o' database."""

from pathlib import Path

ENV_PATH = Path(r'C:\Q2O_Combined\.env')
NEW_DSN = 'DB_DSN=postgresql+psycopg://q2o_user:Q2OPostgres2025(@localhost:5432/q2o'

print('=' * 60)
print('Updating DB_DSN to use existing q2o database')
print('=' * 60)
print()

if not ENV_PATH.exists():
    print(f'✗ .env file not found at {ENV_PATH}')
    exit(1)

# Read the file
content = ENV_PATH.read_text(encoding='utf-8')
lines = content.split('\n')

# Update DB_DSN line
updated = False
new_lines = []
for line in lines:
    if line.strip().startswith('DB_DSN='):
        if 'q2o' not in line:
            new_lines.append(NEW_DSN)
            updated = True
            print(f'✓ Updated: {line[:60]}...')
            print(f'  To:      {NEW_DSN[:60]}...')
        else:
            new_lines.append(line)
            print(f'✓ DB_DSN already points to q2o database')
    else:
        new_lines.append(line)

if updated:
    ENV_PATH.write_text('\n'.join(new_lines), encoding='utf-8')
    print()
    print('✓ .env file updated successfully')
else:
    print('✓ DB_DSN already configured correctly')

print()
print('Next steps:')
print('  1. Restart the backend API')
print('  2. Test the Admin Portal - all endpoints should work now')
print()

