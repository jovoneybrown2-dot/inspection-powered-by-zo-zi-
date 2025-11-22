"""
Zo-Zi Inspection System - Code Integrity Verification
Detects if application code has been modified after deployment
"""

import hashlib
import os
import json
from datetime import datetime

# Critical files to monitor for changes
CRITICAL_FILES = [
    'app.py',
    'database.py',
    'database_postgres.py',
    'db_config.py',
    'form_management_system.py',
]

def calculate_file_hash(filepath):
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Error hashing {filepath}: {e}")
        return None

def generate_integrity_manifest(version='1.0.0'):
    """Generate manifest of all file hashes - Run this when building release"""
    manifest = {
        'version': version,
        'generated_at': datetime.utcnow().isoformat(),
        'files': {}
    }

    print(f"🔐 Generating integrity manifest for version {version}...")

    for filepath in CRITICAL_FILES:
        if os.path.exists(filepath):
            file_hash = calculate_file_hash(filepath)
            if file_hash:
                manifest['files'][filepath] = file_hash
                print(f"  ✓ {filepath}: {file_hash[:16]}...")
        else:
            print(f"  ⚠ {filepath}: NOT FOUND")

    # Sign the manifest with secret key
    manifest['signature'] = sign_manifest(manifest)

    return manifest

def sign_manifest(manifest):
    """Create signature to prevent tampering with manifest itself"""
    # Use environment variable or default for dev
    secret = os.environ.get('ZOZI_SIGNING_SECRET', 'zozi-dev-secret-change-in-production')
    data = json.dumps(manifest['files'], sort_keys=True)
    signature = hashlib.sha256(f"{data}{secret}".encode()).hexdigest()
    return signature

def verify_integrity():
    """Check if code has been modified since deployment"""
    try:
        # Check if manifest exists
        if not os.path.exists('integrity_manifest.json'):
            return {
                'valid': None,
                'reason': 'No integrity manifest found (development mode)',
                'modified_files': [],
                'version': 'dev'
            }

        # Load original manifest
        with open('integrity_manifest.json', 'r') as f:
            original_manifest = json.load(f)

        # Verify manifest signature first
        expected_sig = sign_manifest(original_manifest)
        actual_sig = original_manifest.get('signature', '')

        if expected_sig != actual_sig:
            return {
                'valid': False,
                'reason': 'Manifest signature invalid - integrity file was tampered with',
                'modified_files': [],
                'version': original_manifest.get('version', 'unknown')
            }

        # Check each file
        modified_files = []
        missing_files = []

        for filepath, original_hash in original_manifest['files'].items():
            if not os.path.exists(filepath):
                missing_files.append(filepath)
                continue

            current_hash = calculate_file_hash(filepath)

            if current_hash != original_hash:
                modified_files.append(filepath)

        # Determine result
        all_issues = modified_files + missing_files

        if all_issues:
            reason = []
            if modified_files:
                reason.append(f"Modified: {', '.join(modified_files)}")
            if missing_files:
                reason.append(f"Missing: {', '.join(missing_files)}")

            return {
                'valid': False,
                'reason': ' | '.join(reason),
                'modified_files': modified_files,
                'missing_files': missing_files,
                'version': original_manifest.get('version')
            }

        return {
            'valid': True,
            'reason': 'All files verified',
            'modified_files': [],
            'version': original_manifest.get('version'),
            'checked_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {
            'valid': False,
            'reason': f'Integrity check failed: {str(e)}',
            'modified_files': [],
            'version': 'unknown'
        }

def get_installation_id():
    """Get or create unique installation ID"""
    id_file = 'installation_id.txt'

    if os.path.exists(id_file):
        with open(id_file, 'r') as f:
            return f.read().strip()

    # Generate new ID
    import uuid
    new_id = str(uuid.uuid4())

    with open(id_file, 'w') as f:
        f.write(new_id)

    print(f"🆔 Generated new installation ID: {new_id}")
    return new_id

if __name__ == '__main__':
    # If run directly, generate manifest
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'generate':
        version = sys.argv[2] if len(sys.argv) > 2 else '1.0.0'
        manifest = generate_integrity_manifest(version)

        with open('integrity_manifest.json', 'w') as f:
            json.dump(manifest, f, indent=2)

        print(f"\n✅ Integrity manifest saved to integrity_manifest.json")
        print(f"   Version: {manifest['version']}")
        print(f"   Files: {len(manifest['files'])}")
        print(f"   Signature: {manifest['signature'][:32]}...")
    else:
        # Test integrity
        result = verify_integrity()
        print(f"\n🔍 Integrity Check Result:")
        print(f"   Valid: {result['valid']}")
        print(f"   Version: {result.get('version')}")
        print(f"   Reason: {result.get('reason')}")
        if result.get('modified_files'):
            print(f"   Modified: {result['modified_files']}")
