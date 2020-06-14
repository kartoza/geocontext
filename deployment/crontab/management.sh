#!/usr/bin/env bash

if [[ $# -lt 1 ]]; then
  exit 1
fi

name="$(echo "$*" | cut -d' ' -f1)"
hsh="$(echo "$*" | md5sum | cut -d' ' -f1)"

logs_home="/var/log/"
lock_home="/home/ec2-user/locks"

base_output_dir="$logs_home/$(date "+%Y-%m/%d")"
output_dir="$base_output_dir/$name"

mkdir -p "$output_dir"

lock_file="$lock_home/$hsh.lock"
output_file="$output_dir/$(date "+%Y.%m.%d-%H.%M.%S")-$RANDOM.log"

if [[ -f $lock_file ]]; then
  echo "Attempted running '$*' but found '$lock_file', so execution cancelled" > "$output_file"
  echo "$(date "+%Y-%m-%d %H:%M:%S") : Cron execution ignored because of lock file '$lock_file' : $*" >> "$logs_home/warnings.log"
  exit
fi

docker_id="$(docker ps | grep geocontext_uwsgi:latest | cut -d' ' -f1 | head -n1)"

if [[ -n "$docker_id" ]]; then
  touch "$lock_file"
  echo "$(date "+%Y-%m-%d %H:%M:%S") : Cron started : $*" >> "$logs_home/execution.log"
  {
    echo "$(date "+%Y-%m-%d %H:%M:%S"): Running: $*"
    echo "Using Docker instance $docker_id"
    echo '--------------------------------------------------------------------------------'
    docker exec "$docker_id" /bin/bash -c "python manage.py $*" 2>&1
    echo '--------------------------------------------------------------------------------'
    echo "$(date "+%Y-%m-%d %H:%M:%S"): Finished: $*"
  } >> "$output_file"
  echo "$(date "+%Y-%m-%d %H:%M:%S") : Cron finished in $SECONDS : $*" >> "$logs_home/execution.log"
  rm "$lock_file"
fi
