#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DAYSBalloon 石垣島 自動ブログ記事生成スクリプト（SEO/AIO強化版）
- Anthropic API で SEO 記事を 1 本生成（本文 + 記事専用FAQ を同時生成）
- blog/<slug>.html を出力 / blog/index.json を更新 / sitemap.xml を再生成
- 記事ごとに BlogPosting + FAQPage + BreadcrumbList の構造化データを付与（AI検索対策）
- 関連記事・サービスへの内部リンクを自動挿入（回遊・評価の循環）
- テーマごとにカテゴリとターゲットキーワードを持ち、タイトル冒頭に「石垣島」を必ず置く
環境変数: ANTHROPIC_API_KEY が必須
"""
import os
import re
import json
import datetime
import urllib.request

SITE = "https://daysballoon-ishigaki.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG_DIR = os.path.join(ROOT, "blog")
INDEX_JSON = os.path.join(BLOG_DIR, "index.json")
SITEMAP = os.path.join(ROOT, "sitemap.xml")
MODEL = "claude-haiku-4-5-20251001"
LINE_URL = "https://lin.ee/QJ74oFl"
OG_IMAGE = SITE + "/photo_019.jpg"

# テーマ定義: title / category / keywords(狙う検索語) / spots(本文に必ず入れる固有名詞候補)
TOPICS = [
    {"title": "石垣島の主要リゾートホテルで叶えるサプライズバルーン演出",
     "category": "ホテルサプライズ", "keywords": ["石垣島 ホテル サプライズ", "石垣島 バルーン"],
     "spots": ["ANAインターコンチネンタル石垣リゾート", "フサキビーチリゾート ホテル＆ヴィラズ"]},
    {"title": "石垣島でのプロポーズをバルーンで演出する方法",
     "category": "プロポーズ", "keywords": ["石垣島 プロポーズ", "石垣島 プロポーズ 演出"],
     "spots": ["川平湾", "サンセットビーチ"]},
    {"title": "石垣島の結婚記念日サプライズ｜バルーン装飾アイデア集",
     "category": "記念日", "keywords": ["石垣島 結婚記念日", "石垣島 記念日 サプライズ"],
     "spots": ["フサキビーチリゾート ホテル＆ヴィラズ", "玉取崎展望台"]},
    {"title": "石垣島のホテル客室バースデーサプライズ｜事例とコツ",
     "category": "ホテルサプライズ", "keywords": ["石垣島 誕生日 サプライズ", "石垣島 ホテル バースデー"],
     "spots": ["ANAインターコンチネンタル石垣リゾート", "グランヴィリオリゾート石垣島"]},
    {"title": "石垣島の誕生日サプライズを成功させるバルーン装飾のポイント",
     "category": "誕生日", "keywords": ["石垣島 誕生日 サプライズ", "石垣島 バルーン装飾"],
     "spots": ["米原ビーチ", "石垣島離島ターミナル"]},
    {"title": "石垣島リゾートウェディングのバルーン装飾の選び方",
     "category": "ウェディング", "keywords": ["石垣島 リゾートウェディング", "石垣島 ウェディング装飾"],
     "spots": ["フサキビーチリゾート ホテル＆ヴィラズ", "ANAインターコンチネンタル石垣リゾート"]},
    {"title": "石垣島・川平湾を望むロケーションでのバルーンフォト演出アイデア",
     "category": "フォト演出", "keywords": ["川平湾 フォト", "石垣島 バルーン 写真"],
     "spots": ["川平湾", "川平公園"]},
    {"title": "石垣島のサンセットビーチで楽しむバルーンサプライズ",
     "category": "サプライズ事例", "keywords": ["石垣島 サンセット サプライズ", "石垣島 ビーチ バルーン"],
     "spots": ["石垣島サンセットビーチ", "米原ビーチ"]},
    {"title": "石垣島の女子旅で盛り上がるバルーンデコレーション活用術",
     "category": "女子旅", "keywords": ["石垣島 女子旅 サプライズ", "石垣島 バルーン"],
     "spots": ["ANAインターコンチネンタル石垣リゾート", "石垣島離島ターミナル"]},
    {"title": "石垣島の星空とバルーンで作るロマンチックな夜の演出",
     "category": "プロポーズ", "keywords": ["石垣島 星空 プロポーズ", "石垣島 夜 サプライズ"],
     "spots": ["玉取崎展望台", "フサキビーチリゾート ホテル＆ヴィラズ"]},
    {"title": "石垣島で子どもの誕生日を祝うバルーン装飾アイデア",
     "category": "誕生日", "keywords": ["石垣島 子ども 誕生日", "石垣島 バースデー 装飾"],
     "spots": ["グランヴィリオリゾート石垣島", "ANAインターコンチネンタル石垣リゾート"]},
    {"title": "石垣島旅行の記念日を彩るバルーンブーケの魅力",
     "category": "記念日", "keywords": ["石垣島 記念日", "石垣島 バルーンブーケ"],
     "spots": ["川平湾", "米原ビーチ"]},
    {"title": "石垣島・八重山の海をテーマにしたバルーンカラーコーディネート",
     "category": "装飾アイデア", "keywords": ["石垣島 バルーン装飾", "八重山 バルーン"],
     "spots": ["川平湾", "石垣島サンセットビーチ"]},
    {"title": "石垣島のレストラン・カフェでのサプライズバルーン持ち込み術",
     "category": "サプライズ事例", "keywords": ["石垣島 レストラン サプライズ", "石垣島 サプライズ"],
     "spots": ["石垣島離島ターミナル", "石垣市街地"]},
    {"title": "石垣島のプロポーズを成功させる絶景スポット×バルーン演出",
     "category": "プロポーズ", "keywords": ["石垣島 プロポーズ スポット", "石垣島 プロポーズ"],
     "spots": ["玉取崎展望台", "川平湾", "石垣島サンセットビーチ"]},
]

SERVICE_LINKS = [
    ("ホテルサプライズ装飾", SITE + "/#service"),
    ("プロポーズ演出", SITE + "/#service"),
    ("記念日・誕生日サプライズ", SITE + "/#service"),
    ("よくあるご質問", SITE + "/#faq"),
]


def load_posts():
    if os.path.exists(INDEX_JSON):
        try:
            with open(INDEX_JSON, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def pick_topic(posts):
    """既存記事数で循環しつつ、直近に生成したテーマは避ける"""
    recent = [p.get("title") for p in posts[:5]]
    idx = len(posts) % len(TOPICS)
    for i in range(len(TOPICS)):
        t = TOPICS[(idx + i) % len(TOPICS)]
        if t["title"] not in recent:
            return t
    return TOPICS[idx]


def slugify(title):
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "article"
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + base[:40]


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def call_anthropic(topic):
    key = os.environ["ANTHROPIC_API_KEY"]
    spots = "・".join(topic["spots"])
    kws = "』『".join(topic["keywords"])
    prompt = (
        "あなたは石垣島のバルーン装飾・サプライズ演出専門店『DAYSBalloon』のブログ編集者です。\n"
        "以下のテーマで、検索ユーザーの疑問に具体的に答えるSEO記事を日本語で書いてください。\n\n"
        "【テーマ】" + topic["title"] + "\n"
        "【必ず含める検索語】『" + kws + "』を見出しか本文に自然に含める\n"
        "【必ず触れる固有名詞】" + spots + "（石垣島の実在スポット・ホテル。少なくとも1つは本文に入れる）\n"
        "【禁止】宮古島・伊良部島・下地島など石垣島以外の地名は絶対に書かない\n\n"
        "出力は次のJSON形式のみ（前後に説明やコードブロック記号は不要）:\n"
        "{\n"
        '  "body": "記事本文のHTML。h2,h3,p,ul,liのみ使用。900〜1300字。最初の<p>は記事の要約（100字以内）にする。最後にLINE相談を促す一文を入れる",\n'
        '  "faq": [\n'
        '    {"q": "この記事のテーマに関する具体的な質問1（石垣島を含める）", "a": "80〜150字の回答"},\n'
        '    {"q": "質問2", "a": "回答2"},\n'
        '    {"q": "質問3", "a": "回答3"}\n'
        "  ]\n"
        "}\n"
    )
    body = {"model": MODEL, "max_tokens": 3000, "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(body).encode("utf-8"),
        headers={"content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8"))
    text = data["content"][0]["text"].strip()
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text).strip()
    try:
        obj = json.loads(text)
        content = obj.get("body", "").strip()
        faq = [f for f in obj.get("faq", []) if f.get("q") and f.get("a")][:3]
    except Exception:
        # JSONで返らなかった場合は本文のみとして扱う
        content = text
        faq = []
    # 安全弁: 宮古島系の語が混入していたら石垣島に置換
    for bad in ["宮古島", "伊良部島", "下地島", "宮古ブルー"]:
        content = content.replace(bad, "石垣島")
    return content, faq


def related_links(posts, current_slug, n=3):
    items = [p for p in posts if p.get("slug") != current_slug][:n]
    if not items:
        return ""
    li = "".join(
        '<li><a href="/blog/' + p["slug"] + '.html">' + p["title"] + "</a></li>" for p in items
    )
    return '<section class="related"><h2>関連記事</h2><ul>' + li + "</ul></section>\n"


def service_links_html():
    li = "".join('<li><a href="' + u + '">' + t + "</a></li>" for t, u in SERVICE_LINKS)
    return '<section class="services"><h2>DAYSBalloon 石垣島のサービス</h2><ul>' + li + "</ul></section>\n"


def faq_html(faq):
    if not faq:
        return ""
    items = "".join(
        "<details><summary>" + f["q"] + "</summary><p>" + f["a"] + "</p></details>" for f in faq
    )
    return '<section class="faq"><h2>この記事に関するよくある質問</h2>' + items + "</section>\n"


def cta_html():
    return (
        '<section class="cta">'
        "<p>石垣島でのバルーン装飾・サプライズ演出は、DAYSBalloonにお任せください。ご相談・お見積もりは無料です。</p>"
        '<a class="cta-btn" href="' + LINE_URL + '" target="_blank" rel="noopener">LINEで無料相談する</a>'
        "</section>\n"
    )


def render_article(topic, title, desc, slug, date, content, faq, posts):
    url = SITE + "/blog/" + slug + ".html"
    head = (
        '<!DOCTYPE html>\n<html lang="ja">\n<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        "<title>" + title + "｜DAYSBalloon 石垣島</title>\n"
        '<meta name="description" content="' + desc + '">\n'
        '<link rel="canonical" href="' + url + '">\n'
        '<meta name="robots" content="index, follow">\n'
        '<meta property="og:title" content="' + title + '">\n'
        '<meta property="og:description" content="' + desc + '">\n'
        '<meta property="og:type" content="article">\n'
        '<meta property="og:url" content="' + url + '">\n'
        '<meta property="og:image" content="' + OG_IMAGE + '">\n'
        '<meta property="og:site_name" content="DAYSBalloon 石垣島">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        '<link rel="icon" href="/favicon.ico" sizes="any">\n'
        '<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Noto+Sans+JP:wght@300;400;500;700&display=swap" rel="stylesheet">\n'
    )
    # 構造化データ: BlogPosting
    ld_post = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "description": desc,
        "datePublished": date,
        "dateModified": date,
        "image": OG_IMAGE,
        "inLanguage": "ja",
        "keywords": ", ".join(topic["keywords"]),
        "articleSection": topic["category"],
        "author": {"@type": "Organization", "name": "DAYSBalloon 石垣島", "url": SITE + "/"},
        "publisher": {"@type": "Organization", "name": "DAYSBalloon 石垣島", "url": SITE + "/"},
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
    }
    # 構造化データ: パンくず
    ld_bread = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "ホーム", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "ブログ", "item": SITE + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": title, "item": url},
        ],
    }
    ld = (
        '<script type="application/ld+json">' + json.dumps(ld_post, ensure_ascii=False) + "</script>\n"
        '<script type="application/ld+json">' + json.dumps(ld_bread, ensure_ascii=False) + "</script>\n"
    )
    # 構造化データ: FAQ（記事専用）
    if faq:
        ld_faq = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": f["q"],
                 "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
                for f in faq
            ],
        }
        ld += '<script type="application/ld+json">' + json.dumps(ld_faq, ensure_ascii=False) + "</script>\n"

    style = (
        "<style>\n"
        "*{margin:0;padding:0;box-sizing:border-box}\n"
        'body{font-family:"Noto Sans JP",sans-serif;background:#F5F0EA;color:#1A1A1A;line-height:1.9}\n'
        "a{color:#A88947}\n"
        ".wrap{max-width:760px;margin:0 auto;padding:0 24px}\n"
        ".site-header{padding:28px 0;border-bottom:1px solid rgba(168,137,71,.25)}\n"
        '.logo{font-family:"Cormorant Garamond",serif;font-size:1.6rem;text-decoration:none;color:#1A1A1A}\n'
        ".logo span{color:#A88947;font-style:italic}\n"
        ".crumb{font-size:.78rem;color:#888;padding:18px 0 0}\n"
        ".crumb a{color:#888;text-decoration:none}\n"
        "article{padding:32px 0 24px}\n"
        ".meta{font-size:.78rem;color:#A88947;letter-spacing:1px;margin-bottom:14px}\n"
        "article h1{font-size:1.7rem;font-weight:500;line-height:1.5;margin-bottom:28px}\n"
        "article h2,.faq h2,.related h2,.services h2{font-size:1.25rem;font-weight:500;margin:34px 0 14px;border-left:3px solid #A88947;padding-left:12px}\n"
        "article h3{font-size:1.05rem;margin:24px 0 10px}\n"
        "article p{margin-bottom:16px}\n"
        "article ul,.related ul,.services ul{margin:0 0 16px 1.4em}\n"
        ".faq details{background:#fff;border:1px solid rgba(168,137,71,.25);border-radius:8px;padding:14px 18px;margin-bottom:10px}\n"
        ".faq summary{cursor:pointer;font-weight:500}\n"
        ".faq details p{margin:10px 0 0;font-size:.92rem;color:#444}\n"
        ".cta{background:#fff;border:1px solid rgba(168,137,71,.35);border-radius:10px;padding:26px 22px;margin:36px 0;text-align:center}\n"
        ".cta p{margin-bottom:16px}\n"
        ".cta-btn{display:inline-block;background:#06C755;color:#fff;padding:14px 32px;border-radius:999px;text-decoration:none;font-weight:500}\n"
        ".back{padding:0 0 80px}\n"
        ".back a{display:inline-block;border:1px solid #A88947;color:#A88947;padding:12px 28px;border-radius:999px;text-decoration:none;font-size:.85rem}\n"
        ".site-footer{border-top:1px solid rgba(168,137,71,.25);padding:32px 0;text-align:center;font-size:.78rem;color:#888}\n"
        "</style>\n</head>\n<body>\n"
    )
    bodyhtml = (
        '<header class="site-header"><div class="wrap"><a href="/" class="logo">DAYS<span>Balloon</span></a></div></header>\n'
        '<main class="wrap">\n'
        '<nav class="crumb"><a href="/">ホーム</a> › <a href="/blog/">ブログ</a> › ' + topic["category"] + "</nav>\n"
        "<article>\n"
        '<div class="meta">' + topic["category"] + "｜" + date + "</div>\n"
        "<h1>" + title + "</h1>\n" + content + "\n</article>\n"
        + faq_html(faq)
        + cta_html()
        + related_links(posts, slug)
        + service_links_html()
        + '<div class="back"><a href="/blog/">← 記事一覧へ戻る</a></div>\n</main>\n'
        '<footer class="site-footer"><div class="wrap">© DAYSBalloon 石垣島 — Ishigaki Balloon Decoration &amp; Surprise</div></footer>\n'
        "</body>\n</html>\n"
    )
    return head + ld + style + bodyhtml


def build_sitemap(posts):
    today = datetime.date.today().strftime("%Y-%m-%d")
    urls = [
        "<url><loc>" + SITE + "/</loc><lastmod>" + today + "</lastmod><changefreq>weekly</changefreq><priority>1.0</priority></url>",
        "<url><loc>" + SITE + "/blog/</loc><lastmod>" + today + "</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>",
    ]
    for p in posts:
        urls.append("<url><loc>" + SITE + "/blog/" + p["slug"] + ".html</loc><lastmod>" + p["date"] + "</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n"
    with open(SITEMAP, "w", encoding="utf-8") as f:
        f.write(xml)


def main():
    os.makedirs(BLOG_DIR, exist_ok=True)
    posts = load_posts()
    topic = pick_topic(posts)
    title = topic["title"]
    content, faq = call_anthropic(topic)
    m = re.search(r"<p>(.*?)</p>", content, re.S)
    desc = re.sub(r"<[^>]+>", "", m.group(1)) if m else "石垣島のバルーン装飾・サプライズ演出の情報をお届けします。"
    desc = desc.strip().replace('"', "'")[:110]
    date = datetime.date.today().strftime("%Y-%m-%d")
    slug = slugify(title)
    html = render_article(topic, title, desc, slug, date, content, faq, posts)
    with open(os.path.join(BLOG_DIR, slug + ".html"), "w", encoding="utf-8") as f:
        f.write(html)
    posts = [p for p in posts if p.get("slug") != slug]
    posts.insert(0, {"date": date, "slug": slug, "category": topic["category"], "title": title, "description": desc})
    with open(INDEX_JSON, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    build_sitemap(posts)
    print("Generated:", slug, "| FAQ:", len(faq))


if __name__ == "__main__":
    main()
