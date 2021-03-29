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
    cp -r src/data $dst
    sed -e "s,TITLE,$TITLE,g" \
        -e "s,URL,$URL,g" templates/head.html > $index
    cat templates/header.html >> $index

    for i in $(ls $POSTS); do
        echo "<h3>$i</h3>" >> $index
        loop_over_posts $POSTS/$i $i true
    done

    cat templates/footer.html >> $index
    loop_over_posts $NAV nav false
}

# $1 path
# $2 directory name
# $3 add post to index
loop_over_posts()
{
    for j in $(ls $1); do
        post="$(echo $j | awk '{ print substr( $0, 1, length($0)-3)}')"
        if $3; then
            name=$(echo $post | sed "s,-, ,")
            echo "<a href="$post.html">$name</a>" >> $index
        fi
        generate_post $1 $post
    done
}

# $1 path
# $2 file name
generate_post()
{
    echo "creating page: $2"

    output="$dst/$2.html"
    sed -e "s,TITLE,$TITLE :: $2,g" \
        -e "s,URL,$URL/$2,g" templates/head.html > $output
    cat templates/header.html >> $output
    markdown $1/$2.md >> $output
    cat templates/footer.html >> $output
}

mkdir -p $dst
build;