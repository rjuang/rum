#/bin/bash
for f in `ls *_test.py`; do
    echo "================== BEGIN: $f ============================"
    python3 $f
    echo "================== END:   $f ============================"
done
