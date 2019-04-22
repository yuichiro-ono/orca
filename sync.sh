#!/bin/bash

rsync -uvr --exclude=".*" ./ pacs:/

echo "git commit and push."
git add *
git commit -m `date +%Y/%m/%d`
git push origin master
