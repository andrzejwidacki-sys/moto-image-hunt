#!/bin/bash
# próbuje pobrać napisy (ręczne i automatyczne) kilkoma klientami YouTube; bez pobierania wideo
mkdir -p subs-out; : > subs-out/log.txt
for id in $(cat yt/select_ids.txt); do
  ok=0
  for c in tv_embedded mweb tv web_safari android_vr ios web_embedded; do
    rm -f /tmp/s_*.vtt
    /tmp/yt/bin/yt-dlp --skip-download --write-subs --write-auto-subs --sub-langs "pl.*,en.*,en,pl" --sub-format vtt \
      --extractor-args "youtube:player_client=$c" -o "/tmp/s_%(id)s.%(ext)s" "https://www.youtube.com/watch?v=$id" > /tmp/s_out.txt 2>&1
    if ls /tmp/s_*.vtt >/dev/null 2>&1; then cp /tmp/s_*.vtt subs-out/; echo "$id OK client=$c $(ls /tmp/s_*.vtt | tr '\n' ' ')" >> subs-out/log.txt; ok=1; break; fi
  done
  [ $ok = 0 ] && echo "$id FAIL: $(grep -m1 -o 'ERROR.*' /tmp/s_out.txt | cut -c1-110)" >> subs-out/log.txt
done
cat subs-out/log.txt
