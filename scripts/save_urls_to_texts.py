#!/usr/bin/env python3
"""Save text content from a CSS selector for each URL to .txt files using Playwright.

This script reads one-or-more input files with one URL per line (defaults to
`mitre_technique_urls.txt` and `mitre_mitigation_urls.txt` if present), navigates
to each page using Playwright, extracts the visible text from elements matching
the CSS selector (default: `#v-tabContent > .row`) and writes that plain text to
filesystem-safe `.txt` files in an output directory.

NOTE: This script is NOT executed here. Install Playwright and browsers before
running locally:
    pip install playwright
    playwright install

Usage:
    python scripts/save_urls_to_texts.py --inputs mitre_technique_urls.txt --output texts --workers 4
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import re
from pathlib import Path
from typing import List


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Save selector text from URLs to .txt files')
    p.add_argument('--inputs', '-i', nargs='*', help='Input text files with one URL per line')
    p.add_argument('--output', '-o', default='text_outputs', help='Output directory for text files')
    p.add_argument('--workers', '-w', type=int, default=3, help='Number of concurrent pages')
    p.add_argument('--timeout', type=int, default=30000, help='Navigation timeout in ms (default 30000)')
    p.add_argument('--no-headless', action='store_true', help='Run browser with UI (not recommended)')
    p.add_argument('--wait', type=float, default=0.5, help='Extra wait seconds after network idle before extracting')
    p.add_argument('--selector', default='#v-attckmatrix > .row', help='CSS selector to extract text from')
    return p.parse_args()


def read_urls_from_files(files: List[Path]) -> List[str]:
    urls = []
    for f in files:
        if not f.exists():
            logging.warning('Input file not found: %s', f)
            continue
        for line in f.read_text(encoding='utf-8').splitlines():
            u = line.strip()
            if not u:
                continue
            urls.append(u)
    return urls


def sanitize_filename_from_url(url: str) -> str:
    m = re.sub(r'^https?://', '', url, flags=re.I)
    m = m.split('?', 1)[0].split('#', 1)[0]
    name = m.replace('/', '_')
    name = re.sub(r'[^A-Za-z0-9._\-]', '_', name)
    if len(name) > 180:
        name = name[-180:]
    if not name.lower().endswith('.txt'):
        name = name + '.txt'
    return name


async def fetch_and_save_text(sem: asyncio.Semaphore, browser, url: str, outpath: Path, selector: str, timeout: int, wait: float):
    async with sem:
        try:
            page = await browser.new_page()
            await page.set_viewport_size({'width': 1280, 'height': 1024})
            await page.goto(url, wait_until='networkidle', timeout=timeout)
            if wait and wait > 0:
                await asyncio.sleep(wait)

            elems = await page.query_selector_all(selector)
            if not elems:
                text_content = ''
            else:
                parts = []
                for el in elems:
                    try:
                        t = await el.inner_text()
                    except Exception:
                        try:
                            t = await el.text_content() or ''
                        except Exception:
                            t = ''
                    parts.append(t.strip())
                # join with double newline to separate blocks
                text_content = '\n\n'.join(p for p in parts if p)

            # ensure output directory
            outpath.parent.mkdir(parents=True, exist_ok=True)
            outpath.write_text(text_content, encoding='utf-8')
            await page.close()
            logging.info('Saved text: %s (len=%d)', outpath, len(text_content))
        except Exception as e:
            logging.exception('Failed to fetch/save %s: %s', url, e)


async def run_all(urls: List[str], output_dir: Path, workers: int, timeout: int, headless: bool, wait: float, selector: str):
    from playwright.async_api import async_playwright

    sem = asyncio.Semaphore(workers)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        tasks = []
        for url in urls:
            fname = sanitize_filename_from_url(url)
            outpath = output_dir / fname
            tasks.append(fetch_and_save_text(sem, browser, url, outpath, selector, timeout, wait))

        await asyncio.gather(*tasks)
        await browser.close()


def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

    repo_root = Path(__file__).resolve().parents[1]
    input_files = []
    if args.inputs:
        input_files = [Path(p) for p in args.inputs]
    else:
        candidates = [repo_root / 'mitre_technique_urls.txt', repo_root / 'mitre_mitigation_urls.txt']
        input_files = [c for c in candidates if c.exists()]

    if not input_files:
        logging.error('No input URL files provided and no default files found.')
        return

    urls = read_urls_from_files(input_files)
    if not urls:
        logging.error('No URLs found in input files.')
        return

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    logging.info('Preparing to save %d URLs to text files in %s', len(urls), output_dir)
    logging.info('Selector: %s', args.selector)
    logging.info('NOTE: This script requires Playwright (pip install playwright && playwright install)')

    asyncio.run(run_all(urls=urls, output_dir=output_dir, workers=args.workers, timeout=args.timeout, headless=not args.no_headless, wait=args.wait, selector=args.selector))


if __name__ == '__main__':
    main()
