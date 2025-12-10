#!/usr/bin/env python3
"""Extract unique MITRE ATT&CK technique and sub-technique URLs.

Scans all JSON files under the repository root for objects of
`type` == "attack-pattern" and collects `external_references`
where `source_name` == "mitre-attack" and a `url` is present.

Writes one URL per line to `mitre_technique_urls.txt` by default.
"""
import json
import sys
from pathlib import Path


def extract_urls(root: Path):
    urls = set()
    for path in root.rglob('*.json'):
        try:
            with path.open('r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            # skip files that aren't valid JSON or are unreadable
            continue

        # STIX bundles usually have an 'objects' list
        objects = data.get('objects') if isinstance(data, dict) else None
        if not isinstance(objects, list):
            continue

        for obj in objects:
            if not isinstance(obj, dict):
                continue
            if obj.get('type') != 'attack-pattern':
                continue
            for ref in obj.get('external_references', []) or []:
                if not isinstance(ref, dict):
                    continue
                if ref.get('source_name') == 'mitre-attack' and 'url' in ref:
                    urls.add(ref['url'])

    return urls


def main():
    root = Path(__file__).resolve().parents[1]
    out = Path('mitre_technique_urls.txt')
    if len(sys.argv) > 1:
        root = Path(sys.argv[1])
    if len(sys.argv) > 2:
        out = Path(sys.argv[2])

    print(f"Scanning JSON files under: {root}")
    urls = extract_urls(root)
    if not urls:
        print('No mitre-attack URLs found.')
        return

    # Sort URLs for deterministic output (by the last path segment which contains the technique id)
    def keyfn(u: str):
        return u.rstrip('/').split('/')[-1]

    sorted_urls = sorted(urls, key=keyfn)

    with out.open('w', encoding='utf-8') as f:
        for u in sorted_urls:
            f.write(u.rstrip('/') + '\n')

    print(f'Wrote {len(sorted_urls)} unique URLs to: {out}')


if __name__ == '__main__':
    main()
