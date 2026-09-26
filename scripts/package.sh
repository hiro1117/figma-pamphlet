#!/usr/bin/env bash
# skill/ を配布用の .skill(zip)にまとめる。使い方: scripts/package.sh [版ラベル]
set -euo pipefail
cd "$(dirname "$0")/.."
label="${1:-$(date +%Y-%m-%d)}"
out="dist/figma-pamphlet_${label}.skill"
rm -rf /tmp/figma-pamphlet-pack && mkdir -p /tmp/figma-pamphlet-pack/figma-pamphlet
cp -R skill/. /tmp/figma-pamphlet-pack/figma-pamphlet/
( cd /tmp/figma-pamphlet-pack && zip -q -r -X "$OLDPWD/$out" figma-pamphlet -x '*.DS_Store' )
cp "$out" dist/figma-pamphlet.skill
echo "packed: $out (and dist/figma-pamphlet.skill)"
unzip -l "$out"
