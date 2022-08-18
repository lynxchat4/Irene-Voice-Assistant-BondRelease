#!/usr/bin/env bash

cd "$(dirname $0)/.."

python -m coverage run --source=irene --omit=**/test*/** -m unittest discover . && python -m coverage html
