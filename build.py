#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#   "PyYAML",
#   "Markdown",
#   "Jinja2",
#   "Pillow",
# ]
# ///
"""
dsssg — Dead Simple Static Site Generator

Processes Markdown content with YAML front matter into a static site.
Supports tags, nav pages, root pages, image optimization, and Jinja2 templates.
"""

import os
import re
import sys
import yaml
import shutil
import markdown
from collections import defaultdict
from datetime import datetime
from html.parser import HTMLParser
from jinja2 import Environment, FileSystemLoader


def load_config():
    """Load configuration from config.yaml in cwd, merged over defaults."""
    defaults = {
        'content_dir': 'content/posts',
        'nav_dir': 'content/nav',
        'static_dir': 'static',
        'output_dir': 'site',
        'template_dir': 'templates',
        'tag_template': 'tag.html',
        'post_template': 'post.html',
        'index_template': 'index.html',
        'tags_template': 'tags.html',
        'site_title': 'My Website',
        'site_description': 'A tagged website built with dsssg',
        'site_url': 'https://example.com',
        'author': None,
        'date_format': '%Y-%m-%d',
        'tags_file': 'tags.yaml',
        'images_dir': 'images',
        'files_dir': None,
        'root_dir': 'root',
        'meta_delimiter': '',
        'footer_text': None,
        'footer_credit': None,
        'image_optimize': False,
        'image_max_width': 1200,
        'image_quality': 85,
    }
    config_path = sys.argv[1] if len(sys.argv) > 1 else 'config.yaml'
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = yaml.safe_load(f) or {}
        defaults.update(user_config)
    return defaults


CONFIG = load_config()

def extract_front_matter(content):
    """Extract YAML front matter from markdown content"""
    front_matter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if front_matter_match:
        front_matter_text = front_matter_match.group(1)
        content_without_front_matter = content[front_matter_match.end():]
        try:
            front_matter = yaml.safe_load(front_matter_text)
            return front_matter, content_without_front_matter
        except yaml.YAMLError as e:
            print(f"Error parsing YAML front matter: {e}")
            return {}, content
    return {}, content

def read_markdown_file(file_path):
    """Read markdown file, extract front matter, and process content"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    front_matter, content_without_front_matter = extract_front_matter(content)
    
    # Convert markdown to HTML
    html_content = markdown.markdown(
        content_without_front_matter,
        extensions=['fenced_code', 'tables']
    )
    
    # Process image captions
    html_content = process_image_captions(html_content)
    
    return front_matter, html_content

def get_post_date(front_matter):
    """Get post date from front matter, or empty string if not set"""
    return front_matter.get('date', "")

def clean_output_directory():
    """Clean output directory"""
    if os.path.exists(CONFIG['output_dir']):
        shutil.rmtree(CONFIG['output_dir'])
    os.makedirs(CONFIG['output_dir'], exist_ok=True)
    os.makedirs(os.path.join(CONFIG['output_dir'], 'tags'), exist_ok=True)
    os.makedirs(os.path.join(CONFIG['output_dir'], 'posts'), exist_ok=True)

def generate_nav_url(slug):
    """Generate URL for a nav or root page"""
    return f"/{slug}.html"

def generate_post_url(slug):
    """Generate URL for a post"""
    return f"/posts/{slug}.html"

def generate_tag_url(slug):
    """Generate URL for a tag page"""
    return f"/tags/{slug}.html"

def load_tag_metadata():
    """Load tag metadata from tags.yaml file if it exists"""
    tags_metadata = {}
    
    tags_file_path = CONFIG['tags_file']
    if os.path.exists(tags_file_path):
        try:
            with open(tags_file_path, 'r', encoding='utf-8') as f:
                tags_metadata = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading tags metadata: {e}")
    
    return tags_metadata

def process_tag(tag_name, tags_metadata):
    """Process a tag with its metadata"""
    # Get metadata for this tag (or empty dict if not found)
    metadata = tags_metadata.get(tag_name, {})
    
    # Default slug is the tag name in lowercase with spaces replaced by hyphens
    slug = tag_name.lower().replace(' ', '-')
    
    # Create a tag object with default values
    tag = {
        'name': tag_name,
        'slug': slug,
        'display_name': metadata.get('display_name', tag_name),
        'description': metadata.get('description', ''),
        'color': metadata.get('color', None),
        'icon': metadata.get('icon', None),
        'url': generate_tag_url(slug)
    }
    
    return tag

def get_related_posts(post, all_posts, n=3):
    """Return up to n posts most related to the given post by shared tag count."""
    current_tags = set(post.get('tags', []))
    if not current_tags:
        return []
    scored = []
    for other in all_posts:
        if other['slug'] == post['slug']:
            continue
        shared = current_tags & set(other.get('tags', []))
        if shared:
            scored.append((len(shared), other))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:n]]


def process_image_captions(html_content):
    """
    Process HTML content to add captions to images based on their alt text.
    Converts:
    <img src="path/to/image" alt="This is a caption">
    To:
    <figure>
        <img src="path/to/image" alt="This is a caption">
        <figcaption>This is a caption</figcaption>
    </figure>
    """
    # Pattern to match img tags with alt attributes
    img_pattern = r'<img([^>]*?)alt="([^"]*)"([^>]*?)>'
    
    def add_caption(match):
        # Get the parts of the img tag
        before_alt = match.group(1)
        alt_text = match.group(2)
        after_alt = match.group(3)
        
        # If alt text is empty, just return the original img tag
        if not alt_text.strip():
            return f'<img{before_alt}alt="{alt_text}"{after_alt}>'
        
        # Create a figure with caption
        return f'<figure>\n  <img{before_alt}alt="{alt_text}"{after_alt}>\n  <figcaption>{alt_text}</figcaption>\n</figure>'
    
    # Replace img tags with figure+figcaption
    html_with_captions = re.sub(img_pattern, add_caption, html_content)
    
    return html_with_captions

def build_site():
    """Build the site with tag support"""
    start_time = datetime.now()
    # Set up Jinja2 template environment
    env = Environment(loader=FileSystemLoader(CONFIG['template_dir']))

    # Add custom filters
    def date_filter(date_value, format_string="%Y-%m-%d"):
        """Format a date using strftime"""
        if isinstance(date_value, str):
            try:
                date_value = datetime.strptime(date_value, "%Y-%m-%d")
            except ValueError:
                return date_value
        if hasattr(date_value, 'strftime'):
            return date_value.strftime(format_string)
        return date_value

    def regex_replace(value, pattern, replacement):
        """Replace a pattern in a string"""
        if value is None:
            return ''
        return re.sub(pattern, replacement, value)

    def striptags_excerpt(value):
        """Strip all HTML tags except <pre> blocks and hyperlinks. Removes figures entirely."""
        if value is None:
            return ''
        pre_blocks = []
        def save_pre(match):
            pre_blocks.append(match.group(0))
            return f'\x00PRE{len(pre_blocks) - 1}\x00'
        result = re.sub(r'<pre>.*?</pre>', save_pre, value, flags=re.DOTALL)
        result = re.sub(r'<figure>.*?</figure>', '', result, flags=re.DOTALL)
        # Strip all tags except <a ...> and </a>
        result = re.sub(r'<(?!/?a[\s>])[^>]+>', '', result)
        for i, block in enumerate(pre_blocks):
            result = result.replace(f'\x00PRE{i}\x00', block)
        return result
    
    def safe_html_truncate(html_content, length=700):
        """
        Safely truncate HTML content to approximately 'length' characters
        while preserving valid HTML structure. Pre/code blocks are always
        included whole and count as 50 chars toward the budget.
        """
        # Extract <pre> blocks before parsing so they are never split
        pre_blocks = []
        def save_pre(match):
            pre_blocks.append(match.group(0))
            return f'\x00PRE{len(pre_blocks) - 1}\x00'
        html_without_pre = re.sub(r'<pre>.*?</pre>', save_pre, html_content, flags=re.DOTALL)

        class HTMLTruncator(HTMLParser):
            def __init__(self, max_length):
                super().__init__()
                self.reset()
                self.max_length = max_length
                self.char_count = 0
                self.output = []
                self.open_tags = []
                self.truncated = False

            def handle_starttag(self, tag, attrs):
                if self.truncated:
                    return
                if tag in ('script', 'style', 'iframe'):
                    return
                self.open_tags.append(tag)
                attrs_str = " ".join(f'{name}="{value}"' for name, value in attrs)
                self.output.append(f"<{tag}{' ' + attrs_str if attrs_str else ''}>")

            def handle_endtag(self, tag):
                if self.truncated:
                    return
                if tag in ('script', 'style', 'iframe'):
                    return
                if tag in self.open_tags:
                    self.open_tags.remove(tag)
                self.output.append(f"</{tag}>")

            def handle_data(self, data):
                if self.truncated:
                    return
                # Split on pre markers — they may be embedded mid-text-node
                parts = re.split(r'(\x00PRE\d+\x00)', data)
                for part in parts:
                    if self.truncated:
                        break
                    marker_match = re.fullmatch(r'\x00PRE(\d+)\x00', part)
                    if marker_match:
                        self.output.append(pre_blocks[int(marker_match.group(1))])
                        self.char_count += 50
                        if self.char_count >= self.max_length:
                            self.truncated = True
                    else:
                        part_length = len(part)
                        remaining = self.max_length - self.char_count
                        if remaining <= 0:
                            self.truncated = True
                        elif part_length > remaining:
                            words = part[:remaining + 50].split()
                            partial = ' '.join(words[:-1]) if len(words) > 1 else part[:remaining]
                            self.output.append((partial or part[:remaining]) + '...')
                            self.char_count += remaining
                            self.truncated = True
                        else:
                            self.output.append(part)
                            self.char_count += part_length

            def get_truncated_html(self):
                output_str = ''.join(self.output)
                for tag in reversed(self.open_tags):
                    output_str += f'</{tag}>'
                return output_str

        cleaned_html = re.sub(r'<(script|style|iframe).*?</\1>|<head>.*?</head>', '', html_without_pre, flags=re.DOTALL)
        truncator = HTMLTruncator(length)
        truncator.feed(cleaned_html)
        return truncator.get_truncated_html()

    def process_markdown(directory, is_nav=False, target=None):
        # Process all markdown files in content directory
        for root, _, files in os.walk(CONFIG[directory]):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)

                    # Generate slug from file name (without extension)
                    slug = os.path.splitext(os.path.basename(file_path))[0]

                    # Read markdown file
                    front_matter, html_content = read_markdown_file(file_path)

                    # Get post title
                    title = front_matter.get('title', slug)

                    # Get post date
                    date = get_post_date(front_matter)

                    # Get tags (defaulting to empty list)
                    tags = front_matter.get('tags', [])

                    # If tags is a string, convert to list
                    if isinstance(tags, str):
                        tags = [tag.strip() for tag in tags.split(',')]

                    # Track all tags used
                    all_tags.update(tags)

                    # Extract first image from content for use as thumbnail
                    thumbnail_match = re.search(r'<img[^>]+src="([^"]+)"', html_content)
                    thumbnail = thumbnail_match.group(1) if thumbnail_match else None

                    # Create post object
                    post = {
                        'title': title,
                        'hide_title': front_matter.get('hide_title', False),
                        'nav_order': front_matter.get('nav_order', None),
                        'date': date,
                        'tags': tags,
                        'content': html_content,
                        'slug': slug,
                        'url': generate_nav_url(slug) if is_nav else generate_post_url(slug),
                        'thumbnail': thumbnail,
                    }

                    if is_nav is False:
                        posts.append(post)

                        # Add post to each of its tags
                        for tag in tags:
                            tags_to_posts[tag].append(post)
                    else:
                        (target if target is not None else nav_pages).append(post)

    env.filters['date'] = date_filter
    env.filters['safe_truncate'] = safe_html_truncate
    env.filters['regex_replace'] = regex_replace
    env.filters['striptags_excerpt'] = striptags_excerpt

    # Add current date to templates
    env.globals['now'] = datetime.now()
    
    # Clean output directory
    clean_output_directory()
    
    # Load tag metadata (if available)
    tags_metadata = load_tag_metadata()
    
    # Collect all posts and organize by tags
    posts = []
    nav_pages = []
    root_pages = []
    tags_to_posts = defaultdict(list)
    all_tags = set()

    process_markdown('content_dir')
    process_markdown('nav_dir', True)
    if os.path.exists(CONFIG['root_dir']):
        process_markdown('root_dir', is_nav=True, target=root_pages)

    env.globals['nav_pages'] = nav_pages

    # Sort posts by date (newest first)
    posts.sort(key=lambda x: date_filter(x['date']), reverse=True)
    nav_pages.sort(key=lambda x: (x['nav_order'] is None, x['nav_order']))
    
    # Process tag objects for templates
    processed_tags = {}
    
    for tag_name in all_tags:
        tag_obj = process_tag(tag_name, tags_metadata)
        tag_obj['count'] = len(tags_to_posts[tag_name])
        processed_tags[tag_name] = tag_obj

    all_tags_list = list(processed_tags.values())

    def write_page(url, html):
        output_path = os.path.join(CONFIG['output_dir'], url.lstrip('/'))
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

    post_template = env.get_template(CONFIG['post_template'])

    # Generate nav and root pages
    for post in nav_pages + root_pages:
        write_page(post['url'], post_template.render(post=post, site=CONFIG, tags=all_tags_list))

    # Generate post pages
    for post in posts:
        post['processed_tags'] = [processed_tags[t] for t in post['tags'] if t in processed_tags]
        related = get_related_posts(post, posts)
        write_page(post['url'], post_template.render(post=post, site=CONFIG, posts=posts, tags=all_tags_list, related_posts=related))

    # Generate tag pages
    tag_template = env.get_template(CONFIG['tag_template'])
    for tag_name, tag_posts in tags_to_posts.items():
        tag_posts.sort(key=lambda x: date_filter(x['date']), reverse=True)
        tag = processed_tags[tag_name]
        write_page(tag['url'], tag_template.render(tag=tag, posts=tag_posts, site=CONFIG, tags=all_tags_list))

    # Generate index and tags overview pages
    index_template = env.get_template(CONFIG['index_template'])
    write_page('index.html', index_template.render(posts=posts, site=CONFIG, tags=all_tags_list))

    if os.path.exists(os.path.join(CONFIG['template_dir'], CONFIG['tags_template'])):
        tags_template = env.get_template(CONFIG['tags_template'])
        write_page('tags.html', tags_template.render(posts=posts, site=CONFIG, tags=all_tags_list))

    # Generate sitemap.xml
    site_url = CONFIG['site_url'].rstrip('/')
    sitemap_entries = [
        {'loc': f"{site_url}/", 'priority': '1.0'},
        {'loc': f"{site_url}/tags.html", 'priority': '0.5'},
    ]
    for post in posts:
        entry = {'loc': f"{site_url}{post['url']}", 'priority': '0.8'}
        date = post['date']
        if hasattr(date, 'strftime'):
            entry['lastmod'] = date.strftime('%Y-%m-%d')
        elif isinstance(date, str) and date:
            entry['lastmod'] = date[:10]
        sitemap_entries.append(entry)
    for page in nav_pages:
        sitemap_entries.append({'loc': f"{site_url}{page['url']}", 'priority': '0.6'})
    for tag in processed_tags.values():
        sitemap_entries.append({'loc': f"{site_url}{tag['url']}", 'priority': '0.5'})

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for entry in sitemap_entries:
        lines.append('  <url>')
        lines.append(f"    <loc>{entry['loc']}</loc>")
        if 'lastmod' in entry:
            lines.append(f"    <lastmod>{entry['lastmod']}</lastmod>")
        lines.append(f"    <priority>{entry['priority']}</priority>")
        lines.append('  </url>')
    lines.append('</urlset>')
    write_page('sitemap.xml', '\n'.join(lines))

    # Generate robots.txt
    write_page('robots.txt', f"User-agent: *\nAllow: /\n\nSitemap: {site_url}/sitemap.xml\n")

    # Generate RSS feed
    def to_rfc2822(date):
        if hasattr(date, 'strftime'):
            return date.strftime('%a, %d %b %Y 00:00:00 +0000')
        if isinstance(date, str) and date:
            try:
                return datetime.strptime(date[:10], '%Y-%m-%d').strftime('%a, %d %b %Y 00:00:00 +0000')
            except ValueError:
                pass
        return ''

    rss_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        '  <channel>',
        f'    <title>{CONFIG["site_title"]}</title>',
        f'    <link>{site_url}/</link>',
        f'    <description>{CONFIG["site_description"]}</description>',
        '    <language>en</language>',
        f'    <lastBuildDate>{to_rfc2822(datetime.now())}</lastBuildDate>',
        f'    <atom:link href="{site_url}/feed.xml" rel="self" type="application/rss+xml"/>',
    ]
    for post in posts:
        pub_date = to_rfc2822(post['date'])
        post_url = f"{site_url}{post['url']}"
        rss_lines += [
            '    <item>',
            f'      <title>{post["title"]}</title>',
            f'      <link>{post_url}</link>',
            f'      <guid>{post_url}</guid>',
        ]
        if pub_date:
            rss_lines.append(f'      <pubDate>{pub_date}</pubDate>')
        rss_lines.append(f'      <description><![CDATA[{post["content"]}]]></description>')
        rss_lines.append('    </item>')
    rss_lines += ['  </channel>', '</rss>']
    write_page('feed.xml', '\n'.join(rss_lines))

    # Copy dsssg bundled static assets first (parent site can override)
    dsssg_static = os.path.join(os.path.dirname(__file__), 'static')
    if os.path.exists(dsssg_static):
        shutil.copytree(dsssg_static, os.path.join(CONFIG['output_dir'], 'static'), dirs_exist_ok=True)

    # Copy site static assets (overrides dsssg defaults)
    static_dir = CONFIG['static_dir']
    if os.path.exists(static_dir):
        shutil.copytree(
            static_dir,
            os.path.join(CONFIG['output_dir'], 'static'),
            dirs_exist_ok=True
        )

    # Copy files directory
    files_dir = CONFIG['files_dir']
    if files_dir and os.path.exists(files_dir):
        shutil.copytree(
            files_dir,
            os.path.join(CONFIG['output_dir'], 'files'),
            dirs_exist_ok=True
        )

    # Copy and optimize site images
    images_optimized = 0
    images_dir = CONFIG['images_dir']
    if os.path.exists(images_dir):
        output_images_dir = os.path.join(CONFIG['output_dir'], images_dir)
        if CONFIG['image_optimize']:
            from PIL import Image
            max_width = CONFIG['image_max_width']
            jpeg_quality = CONFIG['image_quality']
            for root, _, files in os.walk(images_dir):
                for file in files:
                    src_path = os.path.join(root, file)
                    rel_path = os.path.relpath(src_path, images_dir)
                    dst_path = os.path.join(output_images_dir, rel_path)
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    ext = os.path.splitext(file)[1].lower()
                    if ext == '.gif':
                        shutil.copy2(src_path, dst_path)
                        continue
                    try:
                        with Image.open(src_path) as img:
                            if img.width > max_width:
                                ratio = max_width / img.width
                                img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
                            if ext in ('.jpg', '.jpeg'):
                                img.save(dst_path, 'JPEG', quality=jpeg_quality, optimize=True)
                            elif ext == '.png':
                                img.save(dst_path, 'PNG', optimize=True)
                            else:
                                img.save(dst_path)
                            images_optimized += 1
                    except Exception:
                        shutil.copy2(src_path, dst_path)
        else:
            shutil.copytree(images_dir, output_images_dir, dirs_exist_ok=True)

    elapsed = (datetime.now() - start_time).total_seconds()
    images_str = f", and optimized {images_optimized} images" if images_optimized else ""
    print(f"{CONFIG['site_title']} built successfully! Made {len(posts)} posts, {len(processed_tags)} tags{images_str} in {elapsed:.2f}s")

if __name__ == "__main__":
    build_site()
