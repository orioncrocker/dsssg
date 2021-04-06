# Static site refactor

Now that my degree is techinically done (more on that [here](/now)), I had the free time to catch up on my project backlog.

After the last site refactor utilizing PHP, I realized that I was in way too deep for the scope of this site.
This is supposed to be a small personal website to write notes to myself and others, not something that needs to be overly complicated.

Similar to the previous rework, I set up some goalposts for myself to work towards:

1. Easy to write and update blog posts
2. Written from scratch (mostly) 
3. "Just works"
4. Looks and feels modern
5. Keep page size and bloat to a minimum

Instead of using a language like PHP that dynamically renders a markdown page each time a new page is accessed on the site, I realized that it would be much more efficient to just serve a pre-rendered HTML file instead.
Then it hit me: Linux was more than capable of rendering markdown into HTML with its own native tools.

### Introducing dead simple static site generator

As the name suggests, my proposed solution to this problem is dead simple.
dsssg uses nothing but the Linux shell and Make to create html files using templates for the header and footer.
If you’d like to check out the script, feel free to do so on my [github page](https://github.com/orioncrocker/dsssg).

Current bugs / known issues:

- Blog posts are displayed alphabetically rather than by date submitted
- No proper 404 page ([fixed!](/some-page-that-doesnt-exist) 04/05/2021)