#!/bin/sh
set -e

echo "Waiting for $1 to be healthy..."

until curl -s $1 > /dev/null; do
  sleep 2
done

echo "$1 is available!"
