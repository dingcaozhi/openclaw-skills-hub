#!/usr/bin/env python3
"""
OpenClaw Skills News 自动更新脚本
每3小时抓取一次最新资讯
"""

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

SITE_DIR = Path("/Users/dingcaozhi/.openclaw/workspace/openclaw-skills-news")
NEWS_SOURCES = [
    {"name": "GitHub OpenClaw", "url": "https://github.com/openclaw/openclaw/commits/main", "category": "skill"},
    {"name": "ClawHub", "url": "https://clawhub.com/skills", "category": "skill"},
    {"name": "OpenClaw Docs", "url": "https://docs.openclaw.ai", "category": "tutorial"},
]

def fetch_with_jina(url):
    """使用 Jina Reader 抓取网页"""
    try:
        result = subprocess.run(
            ["curl", "-s", f"https://r.jina.ai/{url}", "-m", "30"],
            capture_output=True,
            text=True,
            timeout=35
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout
        return None
    except Exception as e:
        print(f"⚠️ 抓取失败 {url}: {e}")
        return None

def extract_news(content, source_name, category):
    """从内容中提取新闻"""
    news_items = []
    if not content:
        return news_items
    
    lines = content.split('\n')
    today = datetime.now().strftime("%Y-%m-%d")
    
    keywords = ['openclaw', 'skill', 'agent', 'mcp', 'tool', 'plugin', 'update', 'release', '新增', '发布']
    emojis = {'skill': '📊', 'tool': '🔧', 'tutorial': '📚', 'community': '💬'}
    
    for line in lines[:100]:
        line = line.strip()
        if len(line) > 10 and len(line) < 120:
            if any(kw in line.lower() for kw in keywords):
                title = re.sub(r'\[.*?\]|\(.*?\)', '', line).strip()
                if title and title not in [n['title'] for n in news_items]:
                    news_items.append({
                        "title": title[:100] + "..." if len(title) > 100 else title,
                        "summary": f"来自 {source_name} 的最新动态...",
                        "source": source_name,
                        "category": category,
                        "date": today,
                        "emoji": emojis.get(category, '📰')
                    })
                    if len(news_items) >= 2:
                        break
    
    return news_items

def fetch_news():
    """抓取新闻"""
    all_news = []
    print("📡 使用 Agent Reach 抓取 OpenClaw Skills 资讯...\n")
    
    for source in NEWS_SOURCES:
        print(f"🔍 {source['name']}...")
        content = fetch_with_jina(source['url'])
        if content:
            items = extract_news(content, source['name'], source['category'])
            all_news.extend(items)
            print(f"   ✅ {len(items)} 条")
        else:
            print(f"   ⚠️ 失败")
    
    print(f"\n📰 共 {len(all_news)} 条新闻")
    return all_news

def update_website(news_list):
    """更新网站"""
    index_file = SITE_DIR / "index.html"
    if not index_file.exists():
        print("❌ index.html 不存在")
        return False
    
    content = index_file.read_text(encoding='utf-8')
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 更新时间戳
    content = re.sub(
        r'<span id="updateTime">.*?</span>',
        f'<span id="updateTime">{today}</span>',
        content
    )
    
    # 更新统计
    total = len(news_list) if news_list else 8
    content = re.sub(
        r'<div class="stat-number" id="totalNews">\d+</div>',
        f'<div class="stat-number" id="totalNews">{total}</div>',
        content
    )
    
    index_file.write_text(content, encoding='utf-8')
    print(f"✅ 网站更新: {now}")
    return True

def deploy():
    """部署到 Netlify"""
    try:
        # 先创建站点
        result = subprocess.run(
            ["netlify", "api", "createSite", "--data", '{"name":"openclaw-skills-hub"}'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # 提取 site ID
        site_id = None
        if result.returncode == 0:
            match = re.search(r'"id":"([a-f0-9-]+)"', result.stdout)
            if match:
                site_id = match.group(1)
                # 保存 site ID
                config_file = SITE_DIR / ".site_id"
                config_file.write_text(site_id)
        
        # 读取保存的 site ID
        config_file = SITE_DIR / ".site_id"
        if config_file.exists():
            site_id = config_file.read_text().strip()
        
        if not site_id:
            print("❌ 无法获取 site ID")
            return False
        
        # 部署
        result = subprocess.run(
            ["netlify", "deploy", f"--site={site_id}", "--prod", "--dir=."],
            cwd=SITE_DIR,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("✅ 部署成功")
            # 提取 URL
            url_match = re.search(r'https://[a-z0-9-]+\.netlify\.app', result.stdout)
            if url_match:
                print(f"🌐 {url_match.group()}")
            return True
        else:
            print(f"❌ 部署失败: {result.stderr[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

def main():
    print(f"\n🦞 OpenClaw Skills Hub Updater")
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏰ 每3小时自动更新\n")
    
    news = fetch_news()
    
    print("\n📝 更新网站...")
    if update_website(news):
        print("\n🚀 部署...")
        deploy()
    
    print("\n✨ 完成!\n")

if __name__ == "__main__":
    main()
