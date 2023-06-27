#!/bin/bash
screen -d -m -S sunblinds python3 sunblinds.py
screen -X caption always "%{rw} * | %H * $LOGNAME | %{bw}%c %D |%{-}%-Lw%{rw}%50>%{rW}%n%f* %t %{-}%+Lw%<" 