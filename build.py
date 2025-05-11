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
    'content_dir': 'content',    # Directory containing markdown files
    'output_dir': 'site',        # Directory for generated HTML files
    'template_dir': 'templates', # Directory containing templates
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
    
    # Fall back to file modification time
    mod_time = os.path.getmtime(file_path)
    return datetime.fromtimestamp(mod_time)

def clean_output_directory():
    """Clean output directory"""
    if os.path.exists(CONFIG['output_dir']):
        shutil.rmtree(CONFIG['output_dir'])
    os.makedirs(CONFIG['output_dir'], exist_ok=True)
    os.makedirs(os.path.join(CONFIG['output_dir'], 'tags'), exist_ok=True)
    os.makedirs(os.path.join(CONFIG['output_dir'], 'posts'), exist_ok=True)

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
    
    env.filters['date'] = date_filter
    
    # Add current date to templates
    env.globals['now'] = datetime.now()
    
    # Clean output directory
    clean_output_directory()
    
    # Load tag metadata (if available)
    tags_metadata = load_tag_metadata()
    
    # Collect all posts and organize by tags
    posts = []
    tags_to_posts = defaultdict(list)
    all_tags = set()
    
    # Process all markdown files in content directory
    for root, _, files in os.walk(CONFIG['content_dir']):
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
                    'url': generate_post_url(slug)
                }
                
                posts.append(post)
                
                # Add post to each of its tags
                for tag in tags:
                    tags_to_posts[tag].append(post)
    
    # Sort posts by date (newest first)
    posts.sort(key=lambda x: x['date'], reverse=True)
    
    # Process tag objects for templates
    processed_tags = {}
    
    for tag_name in all_tags:
        tag_obj = process_tag(tag_name, tags_metadata)
        tag_obj['count'] = len(tags_to_posts[tag_name])
        processed_tags[tag_name] = tag_obj
    
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
    static_dir = os.path.join(CONFIG['template_dir'], 'static')
    if os.path.exists(static_dir):
        shutil.copytree(
            static_dir, 
            os.path.join(CONFIG['output_dir'], 'static'),
            dirs_exist_ok=True
        )
    
    print(f"Site built successfully with {len(posts)} posts and {len(processed_tags)} tags")

if __name__ == "__main__":
    build_site()
