#!/usr/bin/env bash
# Print the path of a Python interpreter that can `import regina`.
#
# The apt package ships its extension module for the distro's *system* Python
# (e.g. cpython-312 on Ubuntu 24.04). If `python3` points elsewhere (pyenv,
# update-alternatives, a venv), `import regina` fails, so we probe candidates.
set -euo pipefail
for p in "${REGINA_PYTHON:-}" python3 /usr/bin/python3 \
         $(ls /usr/bin/python3.[0-9]* 2>/dev/null | grep -E 'python3\.[0-9]+$' | sort -Vr); do
  [[ -n "$p" ]] || continue
  command -v "$p" >/dev/null 2>&1 || continue
  if "$p" -c 'import regina' >/dev/null 2>&1; then
    command -v "$p"
    exit 0
  fi
done
echo "No Python interpreter can import regina; run scripts/install-regina-ubuntu.sh" >&2
exit 1
