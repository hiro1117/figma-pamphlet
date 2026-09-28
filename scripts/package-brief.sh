#!/usr/bin/env bash
# skill-brief/ を配布用の .skill(zip)にまとめる。使い方: scripts/package-brief.sh [版ラベル]
set -euo pipefail
cd "$(dirname "$0")/.."
label="${1:-$(date +%Y-%m-%d)}"
out="dist/pamphlet-brief_${label}.skill"
mkdir -p dist
rm -rf /tmp/pamphlet-brief-pack && mkdir -p /tmp/pamphlet-brief-pack/pamphlet-brief
cp -R skill-brief/. /tmp/pamphlet-brief-pack/pamphlet-brief/
( cd /tmp/pamphlet-brief-pack && zip -q -r -X "$OLDPWD/$out" pamphlet-brief -x '*.DS_Store' )
cp "$out" dist/pamphlet-brief.skill
echo "packed: $out (and dist/pamphlet-brief.skill)"
unzip -l "$out"
