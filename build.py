#!/usr/bin/env python3
"""
Simple Tag System Implementation for dsssg (Dead Simple Static Site Generator)

This script enhances dsssg with a flat tag-based system instead of directory-based organization.
Features:
- Uses YAML front matter in markdown files to assign tags
- Generates tag archive pages
- Updates URL structure to use tags instead of directories
- Provides tag-based navigation
"""

import os
import re
import yaml
import shutil
import markdown
from collections import defaultdict
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# Configuration
CONFIG = {
    'content_dir': 'content/posts',# Content files
    'nav_dir': 'content/nav',    # Nav files
    'static_dir': 'static',      # Static assets
    'output_dir': 'site',        # Generated HTML filepath
    'template_dir': 'templates', # HTML templates
    'tag_template': 'tag.html',  # Template for tag pages
    'post_template': 'post.html',# Template for post pages
    'index_template': 'index.html', # Template for index page
    'tags_template': 'tags.html',# Template for tags overview page
    'site_title': 'My Website',  # Title of the website
    'site_description': 'A tagged website built with dsssg',
    'site_url': 'https://example.com',
    'date_format': '%Y-%m-%d',   # Date format
    'tags_file': 'tags.yaml'     # File containing tag metadata (optional)
}

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
    """Read markdown file and extract front matter"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    front_matter, content_without_front_matter = extract_front_matter(content)
    
    # Convert remaining content to HTML
    html_content = markdown.markdown(
        content_without_front_matter,
        extensions=['fenced_code', 'tables', 'nl2br']
    )
    
    return front_matter, html_content

def get_post_date(front_matter, file_path):
    """Get post date from front matter or file modification time"""
    if 'date' in front_matter:
        return front_matter['date']
    return ""

def clean_output_directory():
    """Clean output directory"""
    if os.path.exists(CONFIG['output_dir']):
        shutil.rmtree(CONFIG['output_dir'])
    os.makedirs(CONFIG['output_dir'], exist_ok=True)
    os.makedirs(os.path.join(CONFIG['output_dir'], 'tags'), exist_ok=True)
    os.makedirs(os.path.join(CONFIG['output_dir'], 'posts'), exist_ok=True)

def generate_nav_url(slug):
    """Generate URL for a post - now independent of tags"""
    return f"/{slug}.html"

def generate_post_url(slug):
    """Generate URL for a post - now independent of tags"""
    return f"/posts/{slug}.html"

def generate_tag_url(tag):
    """Generate URL for a tag page"""
    tag_slug = tag.lower().replace(' ', '-')
    return f"/tags/{tag_slug}.html"

def load_tag_metadata():
    """Load tag metadata from tags.yaml file if it exists"""
    tags_metadata = {}
    
    tags_file_path = os.path.join(os.path.dirname(__file__), CONFIG['tags_file'])
    if os.path.exists(tags_file_path):
        try:
            with open(tags_file_path, 'r', encoding='utf-8') as f:
                tags_metadata = yaml.safe_load(f) or {}
            print(f"Loaded metadata for {len(tags_metadata)} tags from {CONFIG['tags_file']}")
        except Exception as e:
            print(f"Error loading tags metadata: {e}")
    else:
        print(f"Tags file {CONFIG['tags_file']} not found, proceeding without tag metadata")
    
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
        'featured': metadata.get('featured', False),
        'order': metadata.get('order', 999),
        'url': generate_tag_url(slug)
    }
    
    return tag

def build_site():
    """Build the site with tag support"""
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
        if isinstance(date_value, datetime):
            return date_value.strftime(format_string)
        return date_value
    
    def safe_html_truncate(html_content, length=700):
        """
        Safely truncate HTML content to approximately 'length' characters
        while preserving valid HTML structure and code blocks
        """
        from html.parser import HTMLParser
        import re
        
        # Pre-process to handle markdown code blocks that might not be in HTML yet
        # Protect code blocks with special markers
        protected_content = html_content
        
        # First, handle fenced code blocks ```code``` and preserve them
        code_block_pattern = r'```(?:[a-zA-Z0-9]+)?\n(.*?)\n```'
        code_blocks = []
        
        def save_code_block(match):
            code_blocks.append(match.group(0))
            return f"CODE_BLOCK_PLACEHOLDER_{len(code_blocks) - 1}"
        
        protected_content = re.sub(code_block_pattern, save_code_block, protected_content, flags=re.DOTALL)
        
        # Then, handle inline code `code` and preserve them
        inline_code_pattern = r'`([^`]+)`'
        inline_codes = []
        
        def save_inline_code(match):
            inline_codes.append(match.group(0))
            return f"INLINE_CODE_PLACEHOLDER_{len(inline_codes) - 1}"
        
        protected_content = re.sub(inline_code_pattern, save_inline_code, protected_content)
        
        class HTMLTruncator(HTMLParser):
            def __init__(self, max_length):
                super().__init__()
                self.reset()
                self.max_length = max_length
                self.char_count = 0
                self.output = []
                self.open_tags = []
                self.truncated = False
                self.in_pre = False
                self.in_code = False
                
            def handle_starttag(self, tag, attrs):
                if self.truncated:
                    return
                
                # Skip certain tags that might cause issues
                if tag in ('script', 'style', 'iframe'):
                    return
                
                # Track if we're in a code or pre element
                if tag == 'pre':
                    self.in_pre = True
                elif tag == 'code':
                    self.in_code = True
                
                self.open_tags.append(tag)
                attrs_str = " ".join(f'{name}="{value}"' for name, value in attrs)
                self.output.append(f"<{tag}{' ' + attrs_str if attrs_str else ''}>")
                
            def handle_endtag(self, tag):
                if self.truncated:
                    return
                
                # Skip certain tags
                if tag in ('script', 'style', 'iframe'):
                    return
                
                # Track if we're leaving a code or pre element
                if tag == 'pre':
                    self.in_pre = False
                elif tag == 'code':
                    self.in_code = False
                
                # Remove matching open tag
                if tag in self.open_tags:
                    self.open_tags.remove(tag)
                
                self.output.append(f"</{tag}>")
                
            def handle_data(self, data):
                if self.truncated:
                    return
                
                # Check if this is a code block placeholder
                code_block_match = re.match(r'CODE_BLOCK_PLACEHOLDER_(\d+)', data)
                if code_block_match:
                    # This is a code block placeholder, replace it with the actual code
                    index = int(code_block_match.group(1))
                    if index < len(code_blocks):
                        # For code blocks, we count them as a fixed number of characters
                        # to avoid them taking up the entire excerpt
                        code_chars = 50  # Count code blocks as 50 chars regardless of actual length
                        
                        if self.char_count + code_chars <= self.max_length:
                            # We can include a shortened version of this code block
                            code_preview = code_blocks[index]
                            # Limit the code block to a reasonable preview
                            if len(code_preview) > 100:
                                code_lines = code_preview.split('\n')
                                if len(code_lines) > 3:
                                    code_preview = '\n'.join(code_lines[:3]) + '\n...'
                            
                            self.output.append(code_preview)
                            self.char_count += code_chars
                        else:
                            # Not enough space for the code block
                            self.truncated = True
                    return
                
                # Check if this is an inline code placeholder
                inline_code_match = re.match(r'INLINE_CODE_PLACEHOLDER_(\d+)', data)
                if inline_code_match:
                    index = int(inline_code_match.group(1))
                    if index < len(inline_codes):
                        code = inline_codes[index]
                        # For inline code, count the actual length
                        if self.char_count + len(code) <= self.max_length:
                            self.output.append(code)
                            self.char_count += len(code)
                        else:
                            # Not enough space for the inline code
                            self.truncated = True
                    return
                
                # Count only visible characters
                data_length = len(data)
                remaining = self.max_length - self.char_count
                
                if remaining <= 0:
                    self.truncated = True
                    return
                    
                if data_length > remaining:
                    # If we're in a code block, don't split in the middle
                    if self.in_pre or self.in_code:
                        self.truncated = True
                        return
                    
                    # Cut at word boundary if possible
                    words = data[:remaining + 50].split()
                    partial_data = ' '.join(words[:-1]) if len(words) > 1 else words[0][:remaining]
                    
                    if partial_data:
                        self.output.append(partial_data + '...')
                    else:
                        self.output.append(data[:remaining] + '...')
                    
                    self.char_count += len(partial_data)
                    self.truncated = True
                else:
                    self.output.append(data)
                    self.char_count += data_length
            
            def get_truncated_html(self):
                output_str = ''.join(self.output)
                
                # Close any remaining open tags
                for tag in reversed(self.open_tags):
                    output_str += f'</{tag}>'
                    
                return output_str
        
        # Remove problematic elements before parsing
        cleaned_html = re.sub(r'<(script|style|iframe).*?</\1>|<head>.*?</head>', '', protected_content, flags=re.DOTALL)
        
        truncator = HTMLTruncator(length)
        truncator.feed(cleaned_html)
        truncated_html = truncator.get_truncated_html()
        
        # Post-process to restore any code placeholders that might still be in the truncated text
        for i, code in enumerate(code_blocks):
            placeholder = f"CODE_BLOCK_PLACEHOLDER_{i}"
            if placeholder in truncated_html:
                truncated_html = truncated_html.replace(placeholder, code)
        
        for i, code in enumerate(inline_codes):
            placeholder = f"INLINE_CODE_PLACEHOLDER_{i}"
            if placeholder in truncated_html:
                truncated_html = truncated_html.replace(placeholder, code)
        
        return truncated_html

    def process_markdown(directory, is_nav=False):
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
                    date = get_post_date(front_matter, file_path)

                    # Get tags (defaulting to empty list)
                    tags = front_matter.get('tags', [])

                    # If tags is a string, convert to list
                    if isinstance(tags, str):
                        tags = [tag.strip() for tag in tags.split(',')]

                    # Track all tags used
                    all_tags.update(tags)

                    # Create post object
                    post = {
                        'title': title,
                        'date': date,
                        'tags': tags,
                        'content': html_content,
                        'slug': slug,
                        'url': generate_nav_url(slug) if is_nav else generate_post_url(slug)
                    }

                    if is_nav is False:
                        posts.append(post)

                        # Add post to each of its tags
                        for tag in tags:
                            tags_to_posts[tag].append(post)
                    else:
                        nav_pages.append(post)

    env.filters['date'] = date_filter
    env.filters['safe_truncate'] = safe_html_truncate

    # Add current date to templates
    env.globals['now'] = datetime.now()
    
    # Clean output directory
    clean_output_directory()
    
    # Load tag metadata (if available)
    tags_metadata = load_tag_metadata()
    
    # Collect all posts and organize by tags
    posts = []
    nav_pages = []
    tags_to_posts = defaultdict(list)
    all_tags = set()

    process_markdown('content_dir')
    process_markdown('nav_dir', True)

    # Sort posts by date (newest first)
    posts.sort(key=lambda x: x['date'], reverse=True)
    
    # Process tag objects for templates
    processed_tags = {}
    
    for tag_name in all_tags:
        tag_obj = process_tag(tag_name, tags_metadata)
        tag_obj['count'] = len(tags_to_posts[tag_name])
        processed_tags[tag_name] = tag_obj

    # Generate nav pages
    post_template = env.get_template(CONFIG['post_template'])
    for post in nav_pages:
        # Generate output path
        output_path = os.path.join(CONFIG['output_dir'], post['url'].lstrip('/'))
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Render post template
        html = post_template.render(
            post=post,
            site=CONFIG,
            posts=posts,
            tags=list(processed_tags.values())
        )

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

    # Generate post pages
    post_template = env.get_template(CONFIG['post_template'])
    for post in posts:
        # Process tags for this post
        post_tags = []
        for tag_name in post['tags']:
            if tag_name in processed_tags:
                post_tags.append(processed_tags[tag_name])

        # Update post with processed tags
        post['processed_tags'] = post_tags

        # Generate output path
        output_path = os.path.join(CONFIG['output_dir'], post['url'].lstrip('/'))
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Render post template
        html = post_template.render(
            post=post,
            site=CONFIG,
            posts=posts,
            tags=list(processed_tags.values())
        )

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

    # Generate tag pages
    tag_template = env.get_template(CONFIG['tag_template'])
    for tag_name, tag_posts in tags_to_posts.items():
        # Sort posts in this tag by date
        tag_posts.sort(key=lambda x: x['date'], reverse=True)
        
        # Get processed tag object
        tag = processed_tags[tag_name]
        
        # Generate output path
        tag_slug = tag_name.lower().replace(' ', '-')
        output_path = os.path.join(CONFIG['output_dir'], f"tags/{tag_slug}.html")
        
        # Render tag template
        html = tag_template.render(
            tag=tag,
            posts=tag_posts,
            site=CONFIG,
            tags=list(processed_tags.values())
        )
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
    
    # Generate index page
    index_template = env.get_template(CONFIG['index_template'])
    index_html = index_template.render(
        posts=posts,
        site=CONFIG,
        tags=list(processed_tags.values())
    )
    
    # Write index to file
    with open(os.path.join(CONFIG['output_dir'], 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    # Generate tags overview page
    if os.path.exists(os.path.join(CONFIG['template_dir'], CONFIG['tags_template'])):
        tags_template = env.get_template(CONFIG['tags_template'])
        tags_html = tags_template.render(
            posts=posts,
            site=CONFIG,
            tags=list(processed_tags.values())
        )
        
        # Write tags page to file
        with open(os.path.join(CONFIG['output_dir'], 'tags.html'), 'w', encoding='utf-8') as f:
            f.write(tags_html)
        print("Tags overview page generated")
    
    # Copy static assets (CSS, JS, images, etc.)
    static_dir = os.path.join(CONFIG['static_dir'])
    if os.path.exists(static_dir):
        shutil.copytree(
            static_dir, 
            os.path.join(CONFIG['output_dir'], 'static'),
            dirs_exist_ok=True
        )
    
    print(f"Site built successfully with {len(posts)} posts and {len(processed_tags)} tags")

if __name__ == "__main__":
    build_site()
