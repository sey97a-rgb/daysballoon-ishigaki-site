#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DAYSBalloon 宮古島 自動ブログ記事生成スクリプト
- Anthropic API で SEO 記事を 1 本生成
- blog/<slug>.html を出力 / blog/index.json を更新 / sitemap.xml を再生成
環境変数: ANTHROPIC_API_KEY が必須
"""
import os
import re
import json
import datetime
import urllib.request

SITE = "https://daysballoon-miyakojima.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG_DIR = os.path.join(ROOT, "blog")
INDEX_JSON = os.path.join(BLOG_DIR, "index.json")
SITEMAP = os.path.join(ROOT, "sitemap.xml")
MODEL = "claude-haiku-4-5-20251001"
TOPICS = [
    "宮古島のホテル客室バースデーサプライズ｜バルーン装飾の事例とコツ",
    "宮古島でのプロポーズをバルーンで演出する方法",
    "宮古島の結婚記念日サプライズ｜バルーン装飾アイデア集",
    "宮古島リゾートウェディングのバルーン装飾の選び方",
    "宮古島の主要ホテルで叶えるサプライズバルーン演出",
    "宮古島の誕生日サプライズを成功させるバルーン装飾のポイント",
]


def count_posts():
    if os.path.exists(INDEX_JSON):
        try:
            with open(INDEX_JSON, encoding="utf-8") as f:
                return len(json.load(f))
        except Exception:
            return 0
    return 0


def pick_topic():
    return TOPICS[count_posts() % len(TOPICS)]


def slugify(title):
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "article"
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + base[:40]

def call_anthropic(topic):
    key = os.environ["ANTHROPIC_API_KEY"]
    prompt = (
        "あなたは宮古島のバルーン装飾・サプライズ演出専門店『DAYSBalloon』のブログ編集者です。"
        "以下のテーマで、SEOを意識した日本語ブログ記事をHTML本文だけ"
        "（h2,h3,p,ul,liのみ使用、htmlやbodyタグは不要）で800〜1200字程度で書いてください。"
        "『バルーン 宮古島』『サプライズ 宮古島』などの語句を自然に含め、"
        "最後にLINE相談を促す一文を入れてください。テーマ: " + topic
    )
    body = {"model": MODEL, "max_tokens": 2000, "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(body).encode("utf-8"),
        headers={"content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8"))
    text = data["content"][0]["text"].strip()
    text = re.sub(r'^```[a-zA-Z]*\n?', '', text)
    text = re.sub(r'\n?```$', '', text)
    return text.strip()

def render_article(title, desc, slug, date, category, content):
    head = (
        '<!DOCTYPE html>\n<html lang="ja">\n<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<title>' + title + '｜DAYSBalloon 宮古島</title>\n'
        '<meta name="description" content="' + desc + '">\n'
        '<link rel="canonical" href="' + SITE + '/blog/' + slug + '.html">\n'
        '<meta name="robots" content="index, follow">\n'
        '<meta property="og:title" content="' + title + '">\n'
        '<meta property="og:type" content="article">\n'
        '<meta property="og:url" content="' + SITE + '/blog/' + slug + '.html">\n'
        '<meta property="og:image" content="' + SITE + '/photo_019.jpg">\n'
        '<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Noto+Sans+JP:wght@300;400;500;700&display=swap" rel="stylesheet">\n'
    )
    ld = (
        '<script type="application/ld+json">'
        '{"@context":"https://schema.org","@type":"BlogPosting","headline":"' + title + '",'
        '"datePublished":"' + date + '","image":"' + SITE + '/photo_019.jpg",'
        '"author":{"@type":"Organization","name":"DAYSBalloon 宮古島"},'
        '"publisher":{"@type":"Organization","name":"DAYSBalloon 宮古島"},'
        '"mainEntityOfPage":"' + SITE + '/blog/' + slug + '.html"}'
        '</script>\n'
    )
    style = (
        '<style>\n'
        '*{margin:0;padding:0;box-sizing:border-box}\n'
        'body{font-family:"Noto Sans JP",sans-serif;background:#F5F0EA;color:#1A1A1A;line-height:1.9}\n'
        'a{color:#A88947}\n'
        '.wrap{max-width:760px;margin:0 auto;padding:0 24px}\n'
        '.site-header{padding:28px 0;border-bottom:1px solid rgba(168,137,71,.25)}\n'
        '.logo{font-family:"Cormorant Garamond",serif;font-size:1.6rem;text-decoration:none;color:#1A1A1A}\n'
        '.logo span{color:#A88947;font-style:italic}\n'
        'article{padding:56px 0 40px}\n'
        '.meta{font-size:.78rem;color:#A88947;letter-spacing:1px;margin-bottom:14px}\n'
        'article h1{font-size:1.7rem;font-weight:500;line-height:1.5;margin-bottom:28px}\n'
        'article h2{font-size:1.25rem;font-weight:500;margin:34px 0 14px;border-left:3px solid #A88947;padding-left:12px}\n'
        'article h3{font-size:1.05rem;margin:24px 0 10px}\n'
        'article p{margin-bottom:16px}\n'
        'article ul{margin:0 0 16px 1.4em}\n'
        '.back{padding:0 0 80px}\n'
        '.back a{display:inline-block;border:1px solid #A88947;color:#A88947;padding:12px 28px;border-radius:999px;text-decoration:none;font-size:.85rem}\n'
        '.site-footer{border-top:1px solid rgba(168,137,71,.25);padding:32px 0;text-align:center;font-size:.78rem;color:#888}\n'
        '</style>\n</head>\n<body>\n'
    )
    bodyhtml = (
        '<header class="site-header"><div class="wrap"><a href="/" class="logo">DAYS<span>Balloon</span></a></div></header>\n'
        '<main class="wrap">\n<article>\n'
        '<div class="meta">' + category + '｜' + date + '</div>\n'
        '<h1>' + title + '</h1>\n' + content + '\n</article>\n'
        '<div class="back"><a href="/blog/">← 記事一覧へ戻る</a></div>\n</main>\n'
        '<footer class="site-footer"><div class="wrap">© DAYSBalloon 宮古島</div></footer>\n'
        '</body>\n</html>\n'
    )
    return head + ld + style + bodyhtml


def build_sitemap(posts):
    today = datetime.date.today().strftime("%Y-%m-%d")
    urls = [
        '<url><loc>' + SITE + '/</loc><lastmod>' + today + '</lastmod><changefreq>weekly</changefreq><priority>1.0</priority></url>',
        '<url><loc>' + SITE + '/blog/</loc><lastmod>' + today + '</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>',
    ]
    for p in posts:
        urls.append('<url><loc>' + SITE + '/blog/' + p["slug"] + '.html</loc><lastmod>' + p["date"] + '</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>')
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n"
    with open(SITEMAP, "w", encoding="utf-8") as f:
        f.write(xml)


def main():
    os.makedirs(BLOG_DIR, exist_ok=True)
    title = pick_topic()
    content = call_anthropic(title)
    m = re.search(r"<p>(.*?)</p>", content, re.S)
    desc = re.sub(r"<[^>]+>", "", m.group(1)) if m else "宮古島のバルーン装飾・サプライズ演出の情報をお届けします。"
    desc = desc.strip().replace('"', "'")[:110]
    date = datetime.date.today().strftime("%Y-%m-%d")
    slug = slugify(title)
    category = "サプライズ事例"
    html = render_article(title, desc, slug, date, category, content)
    with open(os.path.join(BLOG_DIR, slug + ".html"), "w", encoding="utf-8") as f:
        f.write(html)
    posts = []
    if os.path.exists(INDEX_JSON):
        try:
            with open(INDEX_JSON, encoding="utf-8") as f:
                posts = json.load(f)
        except Exception:
            posts = []
    posts = [p for p in posts if p.get("slug") != slug]
    posts.insert(0, {"date": date, "slug": slug, "category": category, "title": title, "description": desc})
    with open(INDEX_JSON, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    build_sitemap(posts)
    print("Generated:", slug)


if __name__ == "__main__":
    main()
