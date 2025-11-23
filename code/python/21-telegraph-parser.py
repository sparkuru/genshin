# -*- coding: utf-8 -*-
# pip install beautifulsoup4 requests

"""
telegraph-parser.py

Usage:
  python telegraph-parser.py "https://telegra.ph/xxx"

Features:
  1) Fetch a telegra.ph page
  2) Parse title as directory name
  3) Extract all <img> src and download them in document order

Notice:
  - For lawful use only. Ensure you have the right to access and use the target page.
"""

import argparse
import html
import os
import re
import sys
import time
from pathlib import Path
from typing import List, Tuple, Dict
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup  # type: ignore

if sys.platform == "win32":
    from colorama import init as colorama_init
    colorama_init(autoreset=True)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def sanitize_filename(name: str, replacement: str = "_") -> str:
    """Sanitize a title string so it can be safely used as a directory name."""
    # Unescape HTML entities
    name = html.unescape(name).strip()
    # Replace illegal path characters
    name = re.sub(r"[\\/:*?\"<>|]", replacement, name)
    # Collapse invisible whitespaces
    name = re.sub(r"\s+", " ", name).strip()
    # Limit length to avoid excessively long paths
    return name[:180] if len(name) > 180 else name


def fetch_page(url: str, timeout: float, headers: dict[str, str]) -> str:
    resp = requests.get(url, timeout=timeout, headers=headers)
    resp.raise_for_status()
    return resp.text


def _extract_time_text(soup: "BeautifulSoup") -> str:
    """Best-effort time extraction from telegraph-like pages."""
    meta = soup.select_one('meta[property="article:published_time"]') or soup.select_one('meta[name="article:published_time"]')
    if meta and meta.get("content"):
        return meta.get("content").strip()
    time_tag = soup.select_one(".tl_article_header time") or soup.find("time")
    if time_tag:
        if time_tag.get("datetime"):
            return time_tag.get("datetime").strip()
        if time_tag.text:
            return time_tag.text.strip()
    return ""


def parse_title_and_images(html_text: str, base_url: str) -> Tuple[str, List[str], str]:
    soup = BeautifulSoup(html_text, "html.parser")

    title_text = ""
    title_tag = soup.find("title")
    if title_tag and title_tag.text:
        title_text = title_tag.text
    else:
        header_h1 = soup.select_one(".tl_article_header h1")
        title_text = header_h1.text if header_h1 else "telegraph"

    article = soup.select_one("#_tl_editor") or soup.select_one(".tl_article_content")
    if not article:
        article = soup

    parsed_base = urlparse(base_url)
    base_scheme_netloc = f"{parsed_base.scheme}://{parsed_base.netloc}"

    image_urls: List[str] = []
    for img in article.find_all("img"):
        src = (img.get("src") or "").strip()
        if not src:
            continue
        if src.startswith("//"):
            src = "https:" + src
        elif src.startswith("/"):
            src = urljoin(base_scheme_netloc, src)
        elif not src.startswith(("http://", "https://")):
            src = urljoin(base_url, src)
        image_urls.append(src)

    time_text = _extract_time_text(soup)
    return title_text, image_urls, time_text


def ensure_directory(base_dir: Path, title: str) -> Path:
    safe = sanitize_filename(title)
    # Remove trailing brand suffix like " – Telegraph" if present
    safe = re.sub(r"\s*[–-]\s*Telegraph\s*$", "", safe, flags=re.IGNORECASE)
    target = base_dir / safe
    target.mkdir(parents=True, exist_ok=True)
    return target


def download_with_retry(url: str, dest_path: Path, timeout: float, headers: dict[str, str], retries: int, backoff: float) -> Path:
    for attempt in range(1, retries + 1):
        try:
            with requests.get(url, stream=True, timeout=timeout, headers=headers) as r:
                r.raise_for_status()
                content_type = r.headers.get("Content-Type", "")
                ext = guess_extension_from_content_type(content_type)
                if ext and dest_path.suffix.lower() != ext:
                    dest_path = dest_path.with_suffix(ext)
                tmp_path = dest_path.with_suffix(dest_path.suffix + ".part")
                with open(tmp_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                os.replace(tmp_path, dest_path)
                return dest_path
        except Exception:  # noqa: BLE001 - Centralized retry error handling
            if attempt < retries:
                time.sleep(backoff * attempt)
            else:
                raise


def guess_extension_from_content_type(content_type: str) -> str:
    ct = content_type.split(";")[0].strip().lower()
    mapping = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "image/bmp": ".bmp",
        "application/octet-stream": "",  # unknown
    }
    return mapping.get(ct, "")


def build_headers(user_agent: str | None) -> dict[str, str]:
    headers = {
        "User-Agent": user_agent or DEFAULT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }
    return headers


def rewrite_html_with_local_images(html_text: str, url_to_local_name: Dict[str, str], base_url: str) -> str:
    """Replace <img src> with local filenames if present in mapping."""
    soup = BeautifulSoup(html_text, "html.parser")
    article = soup.select_one("#_tl_editor") or soup.select_one(".tl_article_content") or soup
    
    parsed_base = urlparse(base_url)
    base_scheme_netloc = f"{parsed_base.scheme}://{parsed_base.netloc}"
    
    for img in article.find_all("img"):
        src = (img.get("src") or "").strip()
        if not src:
            continue
        if src.startswith("//"):
            src = "https:" + src
        elif src.startswith("/"):
            src = urljoin(base_scheme_netloc, src)
        elif not src.startswith(("http://", "https://")):
            src = urljoin(base_url, src)
        local = url_to_local_name.get(src)
        if local:
            img["src"] = local
    return str(soup)


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse telegra.ph page and download images in order.")
    parser.add_argument("url", help="telegra.ph page URL")
    parser.add_argument("--out", dest="out_dir", default=".", help="Output root directory (default: current)")
    parser.add_argument("--timeout", type=float, default=20.0, help="Request timeout in seconds (default: 20)")
    parser.add_argument("--retries", type=int, default=3, help="Retry times on download failure (default: 3)")
    parser.add_argument("--backoff", type=float, default=1.5, help="Exponential backoff factor (default: 1.5)")
    parser.add_argument("--ua", dest="ua", default=None, help="Custom User-Agent")

    args = parser.parse_args()

    headers = build_headers(args.ua)

    try:
        html_text = fetch_page(args.url, timeout=args.timeout, headers=headers)
    except Exception as e:
        print(f"[Error] Failed to fetch page: {e}", file=sys.stderr)
        sys.exit(2)

    title_text, image_urls, time_text = parse_title_and_images(html_text, args.url)
    if not image_urls:
        print("[Warning] No images found on the page.", file=sys.stderr)

    base_dir = Path(args.out_dir)
    target_dir = ensure_directory(base_dir, title_text)

    # Persist in order: 0001.jpg, 0002.jpg, ...
    width = max(4, len(str(len(image_urls))))
    url_to_local: Dict[str, str] = {}
    for index, img_url in enumerate(image_urls, start=1):
        stem = str(index).zfill(width)
        # Try to guess extension from URL first
        url_ext_match = re.search(r"\.(jpg|jpeg|png|webp|gif|bmp)(?:\?|#|$)", img_url, re.IGNORECASE)
        ext = f".{url_ext_match.group(1).lower()}" if url_ext_match else ".jpg"
        dest = target_dir / f"{stem}{ext}"
        try:
            print(f"[Download] {index}/{len(image_urls)} -> {dest.name}")
            final_path = download_with_retry(img_url, dest, timeout=args.timeout, headers=headers, retries=args.retries, backoff=args.backoff)
            url_to_local[img_url] = final_path.name
        except Exception as e:
            print(f"[Failed] {img_url} -> {e}", file=sys.stderr)

    # Write readme.txt with url/title/time
    try:
        readme_path = target_dir / "readme.txt"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(f"url: {args.url}\n")
            f.write(f"title: {title_text}\n")
            f.write(f"time: {time_text}\n")
    except Exception as e:
        print(f"[Failed] write readme.txt -> {e}", file=sys.stderr)

    # Save rewritten HTML with local image paths
    try:
        rewritten = rewrite_html_with_local_images(html_text, url_to_local, args.url)
        with open(target_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(rewritten)
    except Exception as e:
        print(f"[Failed] write index.html -> {e}", file=sys.stderr)

    print(f"Done. Found {len(image_urls)} images, output to: {target_dir}")


if __name__ == "__main__":
    main()


