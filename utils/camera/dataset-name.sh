name=$1
if [ -z "$name" ]; then
  echo "usage: $0 <name>"
  exit 1
fi
mv -v out-video.avi out-video-${name}.avi
mv -v out-key.csv out-key-${name}.csv
