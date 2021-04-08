#!/bin/sh

# Dead simple static site generator

TITLE="orionc.dev"
POSTS=src/posts
URL='https://orionc.dev'
NAV=src/nav
dst=dst
index="$dst/index.html"

build()
{
    cp src/*.css $dst
    cp src/robots.txt $dst
    cp -r src/data/* $dst
    sed -e "s,TITLE,$TITLE,g" \
        -e "s,URL,$URL,g" templates/head.html > $index
    cat templates/header.html >> $index
    for dir in $(ls $POSTS); do
        echo "<h3>$dir</h3>" >> $index
        loop_over_posts $POSTS/$dir $dir true
    done

    cat templates/footer.html >> $index
    loop_over_posts $NAV nav false
}

# $1 path
# $2 directory name
# $3 (true/false) add post to index
loop_over_posts()
{
    touch sorted_posts
    for i in $(ls $1); do
        date=$(git log -n 1 --diff-filter=A --date="format:%x" --pretty=format:'%ad%n' -- $1/$i)
        echo "$date :: $i" >> sorted_posts
    done
    sort -ru sorted_posts > sorted

    echo '<ul>' >> $index
    while read post; do
        post_name="$(echo $post | cut -c 14- | rev | cut -c 4- | rev)"
        if $3; then
            post_date="$(echo $post | cut -c 1-14)"
            echo "<li> $post_date <a href="$post_name">$post_name</a>" >> $index
        fi
        generate_post $1 $post_name
    done < sorted
    echo '</ul>' >> $index
    rm sorted_posts
    rm sorted
}

# $1 path
# $2 file name
generate_post()
{
    echo "creating page: $2.html"

    output="$dst/$2.html"
    sed -e "s,TITLE,$TITLE :: $2,g" \
        -e "s,URL,$URL/$2,g" templates/head.html > $output
    cat templates/header.html >> $output
    markdown $1/$2.md >> $output
    cat templates/footer.html >> $output
}

mkdir -p $dst
build;