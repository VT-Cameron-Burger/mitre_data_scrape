#!/usr/bin/env python3
"""Extract unique MITRE ATT&CK mitigation URLs.

Scans all JSON files under the repository root for STIX objects and
collects `external_references` where `source_name == "mitre-attack"`
that reference mitigations. It looks for explicit `url` values that
contain `/mitigations/` and also constructs mitigation URLs when an
`external_id` like `Mxxxx` exists but no `url` is present.

Writes one URL per line to `mitre_mitigation_urls.txt` by default.
"""
import json
import sys
from pathlib import Path
from typing import Set


def extract_mitigation_urls(root: Path) -> Set[str]:
    urls = set()
    for path in root.rglob('*.json'):
        try:
            with path.open('r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            # skip files that aren't valid JSON or are unreadable
            continue

        objects = data.get('objects') if isinstance(data, dict) else None
        if not isinstance(objects, list):
            continue

        for obj in objects:
            if not isinstance(obj, dict):
                continue

            # Collect external_references from any object that references a mitigation
            for ref in obj.get('external_references', []) or []:
                if not isinstance(ref, dict):
                    continue
                if ref.get('source_name') != 'mitre-attack':
                    continue

                # Prefer explicit URL when present and it looks like a mitigation
                url = ref.get('url')
                ext_id = ref.get('external_id', '')

                if url and '/mitigations/' in url:
                    urls.add(url.rstrip('/'))
                    continue

                # If there's no url but an external_id like 'M1234', construct a canonical URL
                if ext_id and isinstance(ext_id, str) and ext_id.upper().startswith('M'):
                    urls.add(f'https://attack.mitre.org/mitigations/{ext_id.upper()}')

    return urls


def main():
    root = Path(__file__).resolve().parents[1]
    out = Path('mitre_mitigation_urls.txt')
    if len(sys.argv) > 1:
        root = Path(sys.argv[1])
    if len(sys.argv) > 2:
        out = Path(sys.argv[2])

    print(f"Scanning JSON files under: {root}")
    urls = extract_mitigation_urls(root)
    if not urls:
        print('No mitigation URLs found.')
        return

    # Sort by mitigation id for deterministic output
    def keyfn(u: str):
        return u.rstrip('/').split('/')[-1]

    sorted_urls = sorted(urls, key=keyfn)

    with out.open('w', encoding='utf-8') as f:
        for u in sorted_urls:
            f.write(u + '\n')

    print(f'Wrote {len(sorted_urls)} unique mitigation URLs to: {out}')


if __name__ == '__main__':
    main()
