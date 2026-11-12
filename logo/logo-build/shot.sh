#!/bin/bash
# usage: shot.sh file.svg bg width height out.png
WP=$(cygpath -w "$(pwd)")
cat > _r.html <<H
<!doctype html><html><body style="margin:0;background:$2"><img src="$1" style="display:block;width:${3}px;height:${4}px"></body></html>
H
"/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --headless=new --disable-gpu --hide-scrollbars --window-size=$3,$4 --screenshot="$(pwd -W)/$5" "file:///$(pwd -W)/_r.html" 2>&1 | tail -1
