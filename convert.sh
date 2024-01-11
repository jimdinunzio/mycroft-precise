SOURCE_DIR=tobeconverted
DEST_DIR=converted

for i in $SOURCE_DIR/*.wav; do echo "Converting $i..."; fn=${i##*/}; ffmpeg.exe -i "$i" -acodec pcm_s16le -ar 16000 -ac 1 -f wav "$DEST_DIR/${fn%.*}.wav"; done

