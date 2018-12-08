#!/bin/bash

rsync -uvr --exclude=".*" ./ orca:/
