## Dead Simple Static Site Generator

dsssg is exactly what it claims to be: a static website generator that is dead simple.

This project represents a reaction to ubiquitous and bloated web frameworks that should be considered overkill when creating simple websites.

Drop in a few Markdown files, configure `config.yaml`, and run `make build`. That's it.

---

## Requirements

- [uv](https://docs.astral.sh/uv/) — Python dependency management (PyYAML, Markdown, Jinja2 are declared inline via PEP 723 and installed automatically)

---

## Standalone Usage

Clone the repo and build:

```sh
git clone <repo-url> dsssg
cd dsssg
make build
```

The generated site lands in `site/`. To deploy locally or to a remote server:

```sh
make local     # rsync to /var/www/html (requires sudo)
make deploy    # rsync to remote (requires .env)
```

For remote deploy, copy `.env.example` to `.env` and fill in your credentials:

```sh
DEPLOY_USER=user
DEPLOY_HOST=example.com
DEPLOY_PATH=/var/www/html
```

---

## Submodule Usage

To use dsssg as a submodule in a separate site repository:

```sh
mkdir mysite && cd mysite
git init
git submodule add <repo-url> dssg
```

Create a `config.yaml` in the site root pointing to your content directories:

```yaml
site_title: "My Site"
site_description: "A website about things."
site_url: "https://example.com"
author: "Your Name"

content_dir: "posts"
nav_dir: "nav"
template_dir: "dssg/templates"
static_dir: "static"
output_dir: "site"
tags_file: "tags.yaml"
```

Copy the Makefile from dsssg to the site root:

```sh
cp dssg/Makefile .
```

Then add your content:

```
mysite/
├── dssg/           # dsssg submodule
├── config.yaml
├── Makefile
├── tags.yaml
├── posts/          # Blog posts
├── nav/            # Navbar pages (about, contact, etc.)
├── root/           # Root-level pages excluded from navbar (e.g. 404)
├── static/         # Site-specific static assets (overrides dssg/static/)
└── images/         # Images copied to site/images/
```

Changes to the generator itself (templates, build.py, CSS) should be committed inside the `dssg/` submodule separately.

---

## Configuration

All configuration lives in `config.yaml` (read from the current working directory at build time).

| Key | Default | Description |
|-----|---------|-------------|
| `site_title` | `"My Website"` | Site name, used in `<title>` and footer |
| `site_description` | `"A tagged website..."` | Meta description for the homepage |
| `site_url` | `"https://example.com"` | Base URL used for absolute links and OG tags |
| `author` | `""` | Author name used in footer and post metadata |
| `date_format` | `"%Y-%m-%d"` | strftime format for displayed post dates |
| `content_dir` | `"content/posts"` | Directory of blog post Markdown files |
| `nav_dir` | `"content/nav"` | Directory of navbar page Markdown files |
| `template_dir` | `"templates"` | Jinja2 templates directory |
| `static_dir` | `"static"` | Static assets copied to `site/static/` |
| `output_dir` | `"site"` | Build output directory |
| `tags_file` | `"tags.yaml"` | Tag metadata definitions |
| `images_dir` | `"images"` | *(optional)* Images directory, copied to `site/images/` |
| `root_dir` | `"root"` | *(optional)* Pages built with site template, output to site root, excluded from navbar |
| `footer_text` | `null` | *(optional)* First footer line (site-specific text) |
| `footer_credit` | `null` | *(optional)* Second footer line (e.g. attribution) |

---

## Content Format

### Posts (`content_dir`)

```markdown
---
title: My Post Title
tags: [tag-one, tag-two]
---

Markdown content here.
```

Post dates are derived from the **initial git commit** of each file. Uncommitted posts will not have a date.

### Nav Pages (`nav_dir`)

Same format as posts. These are rendered with the site template and linked in the navbar.

```markdown
---
title: About
hide_title: true
nav_order: 1
---

Content here. The page title won't be rendered as an h1.
```

Use `hide_title: true` to suppress the template-rendered `<h1>` (useful when your content already opens with a heading or you want full control over the layout).

Use `nav_order` to control the position of the page in the navbar. Pages are sorted numerically, lowest first. Pages without `nav_order` set will appear last.

### Root Pages (`root_dir`)

Same format as nav pages. Built with the site template and output to the site root (e.g. `404.html`), but **not** added to the navbar. Useful for error pages and other special pages.

---

## Tags

Tags must be defined in `tags.yaml`:

```yaml
my-tag:
  display_name: "My Tag"
  description: "Posts about this topic."
  color: "#58ACFA"     # optional
  icon: "🏷️"          # optional
  featured: true       # optional
  order: 1             # optional, lower = first
```

Tag archive pages are generated at `/tags/{tag-slug}.html`.

---

## Templates

Jinja2 templates live in `template_dir`. Available templates:

| File | Purpose |
|------|---------|
| `base.html` | Master layout (head, header, nav, footer) |
| `post.html` | Individual posts and nav pages |
| `index.html` | Homepage with post list and excerpts |
| `tag.html` | Tag archive page |
| `tags.html` | All-tags overview page |
| `post-meta.html` | Reusable date + tag badge component |

### Template Variables

All templates receive `site` (all config values) and `tags` (all tag objects). Additional variables per template:

- **post.html**: `post` (single post), `posts` (all posts, for related posts)
- **index.html**: `posts` (all posts, newest first)
- **tag.html**: `tag` (single tag object), `posts` (posts in this tag)
- **tags.html**: `tags`, `posts`

---

## Output Structure

```
site/
├── index.html
├── tags.html
├── 404.html           # from root_dir
├── about.html         # from nav_dir
├── posts/
│   └── my-post.html
├── tags/
│   └── my-tag.html
├── static/
│   └── css/
│       └── style.css
└── images/
```
