# It's alive!

Finally, it's complete! Mostly.
There are still a few bugs around, but it's about time I stopped being a perfectionist and actually completed a project rather than endlessly obsess over the small imperfections that only I would notice.

So, here it is.
At long last, a functional website built from "scratch."
Before going into why I think this iteration is an improvement over the original site, I'll let you take a peek at my first attempt instead.
[I've saved it for posterity here](/old_site/index.html).

While the original site looks aesthetically identical to this site, it was written 100% in HTML and CSS.
That means that every time I wanted to update the navbar, header, footer, or anything else consistent throughout all of the pages, I had to manually udpate each one.
**By hand.**
As you can probably imagine, it was tedious and absolutely terrible.
Additionally, it made the already time consuming effort required to write a blog post an uncessesarily complicated task.

## Requirements for site rework:

1. Easy to write and update blog posts
2. Written from scratch (mostly) 
3. "Just works"
4. Looks and feels modern (or at least not something from 1999)
5. Keep page size and bloat to a minimum

That was pretty much it. Simple right?

Because I didn't know much about web development at this point, I decided to investigate some of the tools regularly used for development.
While Javascript is the "industry standard" that everyone seems to be using nowadays, it is [notorious for bloat](https://brainleaf.com/blog/bug-reports/javascript-is-slowing-down-the-internet/).

Instead, I turned to another web language.
One that is almost universally hated across every programming board I've ever surfed.

The *dreaded* **PHP**.

![php is trash apparently](/images/php.jpg)

The decision to use PHP came from stumbling across [this github page](https://github.com/Cristy94/markdown-blog) while trying to search for a preexisting [FOSS](https://en.wikipedia.org/wiki/Free_and_open-source_software) framework to use instead of starting from absolutely nothing.
During my limited experience as noob programmer, I've learned that it's always better to use someone else's project, no matter how abandoned, as a diving board instead of building one yourself.

I think it was this line from the repository's `README` that sold me on it: "To create a post just write a new .md file. Everything else just works."
*Perfect,* that's exactly what I was looking for.

Turns out the repo had been written for use with Apache web hosting software, not Nginx.
Because I already had a few [other sites](https://thebonegeneration.com) hosted via Nginx on my web server, I figured that reconfiguring Nginx to act like Apache would be worth it.
Was it worth it? Yes.
Was it painful? Also yes.

In my few years at Portland State I've noticed that topics like regular expressions are something most new programmers shy away from (for good reason).
I was fortunate enough to have a decent understanding of regular expressions at the start of this project instead of having to learn as I went along.
That being said, it's always nice to have a tool online do the heavy lifting for you.
I would highly recommend [regexr.com](https://regexr.com/) if you're thinking of dabbling with regular expressions for yourself.

The real magic of the repository is a script called `Parsedown`.
In a nutshell it renders `.md` pages into HTML, all you have to do is point it at a directory with `.md` files in it and you're good to go.
In case you're unfamiliar, Markdown is very common around the internet (Github uses Markdown documents) and incredibly easy to write decent looking pages in.

- [x] 1. Easy to write and update blog posts

## Ok, so far so good.

Now came the third requirement, something that "just works."
Out of the box, [Cristy94's](https://github.com/Cristy94) repo only read blog pages out of one directory.
While this arguably "just worked," I wanted to be able to list different categories of posts separately rather than have one large list of of all .md files I vomited onto the site.

In order to achieve this, some fundamental restructuring had to take place.
That means transforming this:

```
<?php
require_once 'postRenderer.php';
$path = './posts';
$files = array_slice(scandir($path), 2);

foreach ($files as $file) {
    $md = file_get_contents($path . '/' . $file);
    // Get only summary (first lines of post)
    $md = getFirstLines($md, 3);
    $md = addTitleHref($md, $file);
    ?>
    <div class="blog-post">
        <?php echo renderMarkdown($md); ?>
        <a href="<?php echo explode('.', $file)[0] ?>">Read post</a>
    </div>
<?php } ?>
```

Into this:

```
<?php
require_once 'postRenderer.php';
$path = './blog/';
$dirs = array_slice(scandir($path), 2);

foreach ($dirs as $dir) {

    $dirpath = $path . $dir;
    if(is_dir($dirpath)) {

        $files = array_slice(scandir($dirpath), 2);
        if (count($files) > 0) {
            ?>
            <h1><?php echo $dir ?></h1>
            <?php

            foreach($files as $file) {
                $filepath = $dirpath . '/' . $file;

                if(is_file($filepath) && pathinfo($file,
                    PATHINFO_EXTENSION) == 'md') {

                    $md = file_get_contents($filepath);
                    $pageTitle = getPostTitle($md, $filepath);
                    $pageDate = getPostDate($filepath);
                    ?>
                    <li>
                        <?php
                        if ($pageDate)
                            echo $pageDate;
                        else
                            echo "date not found!";
                        echo " :: ";
                        ?>
                        <a href = <?php echo getPostSlug($filepath) ?>>
                        <?php echo $pageTitle ?></a>
                    </li>
                    <?php
                }
            }
        }
    }
} ?>
```

Essentially, the foreach loop which traversed through the single directory now was a two foreach loops which traversed through all available directories -> then the files within that directory.
Additionally I added the functionality to read when the file was last updated, making it easy to see when each post was added to the site.

With this added functionality, all I needed to do to create another category or post was simply drop it into the `blog` directory.

- [x] 2. Written from scratch (mostly)   
- [x] 3. "Just works"

Before moving away from PHP, I do have ot say that I don't hate using it.
Sure, it's a bit goofy to use at times, but if you've scripted using `bash` before it's a piece of cake.
Not sure where all the hate is coming from.

## Moving on

Requirement 4 is mostly subjective, but it's an important one.
If you encounter a site in 2020 that looks like something straight from the glory days of the internet, there are one of three possibilities at play.

1. The site hasn't been updated since 1999
2. The site was built by someone who doesn't know what CSS is
3. The site was built by a college professor

I just think it's important for a website to look aesthetically appealing on a basic level with emphasis on functionality and overall user experience.
The original site looked good (by my standards at least) and I thought that the top navbar was easy to understand and get around with.
All it took to integrate the old look into the new site was copying a .css file.
Easy.

- [x] 4. Looks and feels modern (or at least not something from 1999)

## Only one requirement left: Keep the page size and bloat to a minimum.

For this next part, I used [smallseotools.com](https://smallseotools.com/website-page-size-checker/) to determine the size of multiple pages.

Here's something I found genuinely surprising. Turns out, even though my [about](/about) page is calling about 5 other pages in order to be displayed properly, it's about 1.33 KB less in size than my previous [about](/old_site/index.html) page.

![speed test 1](/images/speed0.png)

Okay, so we're heading in the right direction.
But how does this compare to other sites regularly used on the internet?

![speed test 2](/images/speed1.png)

Maybe Google's homepage was an unfair target to compare myself against.
However, when looking at the comparison between my site and [pdx.edu](https://pdx.edu) and [amazon.com](https://amazon.com), it becomes clear how small my each page really is from a bandwidth perspective.

- [x] 5. Keep page size and bloat to a minimum

## Anyways...

Now that this site is done I have no more excuses to put off blog posts.
It was logical that the first real post be about the site itself, as it was an endeavor in and of itself.
Expect future posts to be anywhere between sysadmin notes, album reviews, and code snippets, and other random things.

I would like to try to take the time out of my week to write at least 1 post a week, but I know that probably won't happen so I won't commit.

As always, thanks for stopping by.

In the mean time, here's a list of other things I'd like to implement in the future, but probably not anytime soon.

0. Bugfix - sort posts in each category by date   
   (This will only matter when there is content to sort through)
1. RSS Feed
2. Title icon
3. Search function
4. Tag function?