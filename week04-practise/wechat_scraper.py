#!/usr/bin/env python3
import argparse
import os
import re
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup


DEFAULT_URLS = [
    "https://mp.weixin.qq.com/s/WyIA5-6P7Y3n3qhvk0aPvQ",
    "https://mp.weixin.qq.com/s/m5OJY2K5E9itFKaU4DjZXA",
]


def _sanitize_filename(name: str) -> str:
    name = re.sub(r"[^\w\-\.]+", "_", name.strip())
    return name or "article"


def _extract_title(soup: BeautifulSoup) -> str:
    title = soup.find("h1", id="activity-name")
    if title and title.get_text(strip=True):
        return title.get_text(strip=True)
    meta = soup.find("meta", property="og:title")
    if meta and meta.get("content"):
        return meta["content"].strip()
    if soup.title and soup.title.get_text(strip=True):
        return soup.title.get_text(strip=True)
    return "wechat_article"


def _extract_content_root(soup: BeautifulSoup) -> Optional[BeautifulSoup]:
    root = soup.find("div", id="js_content")
    if root:
        return root
    # Fallback for occasionally different container ids
    for candidate_id in ["js_article", "article_content", "content"]:
        root = soup.find("div", id=candidate_id)
        if root:
            return root
    return None


def _iter_blocks(content_root: BeautifulSoup) -> Iterable[Tuple[str, BeautifulSoup]]:
    block_tags = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "section", "blockquote", "pre", "ul", "ol", "img"]
    for tag in content_root.find_all(block_tags, recursive=True):
        yield tag.name, tag


def _extract_image_url(tag: BeautifulSoup) -> Optional[str]:
    for key in ["data-src", "data-original", "src", "data-ori-src"]:
        url = tag.get(key)
        if url:
            return url
    return None


def _download_image(session: requests.Session, url: str, out_dir: Path, index: int) -> Optional[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = ".jpg"
    if "." in url.split("?")[0]:
        ext = "." + url.split("?")[0].split(".")[-1]
        if len(ext) > 5:
            ext = ".jpg"
    filename = f"image_{index:03d}{ext}"
    path = out_dir / filename
    try:
        resp = session.get(url, timeout=20)
        resp.raise_for_status()
        path.write_bytes(resp.content)
        return path
    except Exception:
        return None


def _html_to_markdown(content_root: BeautifulSoup, session: requests.Session, image_dir: Path) -> Tuple[str, int]:
    lines: List[str] = []
    image_count = 0

    for tag_name, tag in _iter_blocks(content_root):
        if tag_name == "img":
            img_url = _extract_image_url(tag)
            if not img_url:
                continue
            image_count += 1
            saved = _download_image(session, img_url, image_dir, image_count)
            alt_text = tag.get("alt", "").strip()
            if saved:
                rel_path = saved.as_posix()
                alt = alt_text if alt_text else f"image_{image_count:03d}"
                lines.append(f"![{alt}]({rel_path})")
            else:
                lines.append(f"[image_{image_count:03d}] {img_url}")
            continue

        if tag_name in ["ul", "ol"]:
            items = [li.get_text(" ", strip=True) for li in tag.find_all("li", recursive=True)]
            for item in items:
                if item:
                    prefix = "-" if tag_name == "ul" else "1."
                    lines.append(f"{prefix} {item}")
            continue

        text = tag.get_text(" ", strip=True)
        if not text:
            continue
        if tag_name.startswith("h"):
            level = int(tag_name[1])
            lines.append("#" * min(level + 1, 6) + f" {text}")
        else:
            lines.append(text)

    # Remove consecutive duplicate lines
    cleaned: List[str] = []
    prev = None
    for line in lines:
        if line != prev:
            cleaned.append(line)
        prev = line

    return "\n\n".join(cleaned).strip(), image_count


def fetch_article(url: str, output_dir: Path) -> Tuple[Path, int]:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://mp.weixin.qq.com/",
        }
    )

    resp = session.get(url, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    title = _extract_title(soup)
    content_root = _extract_content_root(soup)
    if content_root is None:
        raise RuntimeError("未找到文章内容区域（js_content）")

    slug = _sanitize_filename(title)
    article_dir = output_dir / slug
    image_dir = article_dir / "images"
    article_dir.mkdir(parents=True, exist_ok=True)

    body_md, image_count = _html_to_markdown(content_root, session, image_dir)
    md_path = article_dir / "article.md"

    header = [
        f"# {title}",
        "",
        f"- Source: {url}",
        f"- Images: {image_count}",
        "",
    ]
    md_path.write_text("\n".join(header) + body_md + "\n", encoding="utf-8")
    return md_path, image_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="爬取微信公众号文章并转为Markdown文本（含图片）")
    parser.add_argument("urls", nargs="*", default=DEFAULT_URLS, help="要爬取的文章链接")
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent / "wechat_outputs"),
        help="输出目录",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    for url in args.urls:
        try:
            md_path, image_count = fetch_article(url, output_dir)
            print(f"[OK] {url} -> {md_path} (images: {image_count})")
        except Exception as exc:
            print(f"[ERROR] {url}: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
