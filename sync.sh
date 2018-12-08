#!/bin/bash

rsync -uvr --exclude=".*" ./ orca:/

echo "git commit and push."
git add *
git commit -m `date +%Y/%m/%d`
git push origin master
