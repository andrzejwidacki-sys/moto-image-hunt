#!/bin/bash
# Próba pobrania filmu (<=480p) różnymi klientami YouTube, potem przez Piped/Invidious. Użycie: dl.sh <id> <outdir>
ID=$1; OUT=$2; mkdir -p $OUT; LOG=$OUT/dl.log; : > $LOG
URL="https://www.youtube.com/watch?v=$ID"
for C in android_vr tv tv_embedded mweb web_safari ios web_embedded web_creator tv_simply android; do
  echo "== yt-dlp client $C" | tee -a $LOG
  /tmp/yt/bin/yt-dlp -q --no-warnings --extractor-args "youtube:player_client=$C" -f "bv*[height<=480]+ba/b[height<=480]/b" --merge-output-format mp4 --write-info-json -o "$OUT/video.%(ext)s" "$URL" >> $LOG 2>&1
  if ls $OUT/video.mp4 >/dev/null 2>&1 && [ $(stat -c%s $OUT/video.mp4) -gt 1000000 ]; then echo "OK client $C" | tee -a $LOG; echo $C > $OUT/client.txt; exit 0; fi
  rm -f $OUT/video.*
done
for H in pipedapi.kavin.rocks pipedapi.adminforge.de api.piped.private.coffee pipedapi.reallyaweso.me; do
  echo "== piped $H" | tee -a $LOG
  curl -sS -m 30 "https://$H/streams/$ID" -o $OUT/piped_$H.json >> $LOG 2>&1; head -c 300 $OUT/piped_$H.json >> $LOG; echo >> $LOG
done
curl -sS -m 30 "https://api.invidious.io/instances.json?sort_type=health" -o $OUT/inv_instances.json >> $LOG 2>&1; head -c 300 $OUT/inv_instances.json >> $LOG
exit 1
