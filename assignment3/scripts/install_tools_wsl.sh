#!/usr/bin/env bash
set -euo pipefail

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This installer is intended for Ubuntu/Debian in WSL."
  exit 1
fi

APT_SOURCES_DIR="$(pwd)/.apt"
APT_SOURCES_LIST="${APT_SOURCES_DIR}/ubuntu-jammy-yandex.list"
mkdir -p "${APT_SOURCES_DIR}" /tmp/empty-apt-sources
cat > "${APT_SOURCES_LIST}" <<'EOF'
deb https://mirror.yandex.ru/ubuntu jammy main restricted universe multiverse
deb https://mirror.yandex.ru/ubuntu jammy-updates main restricted universe multiverse
deb https://mirror.yandex.ru/ubuntu jammy-backports main restricted universe multiverse
deb https://mirror.yandex.ru/ubuntu jammy-security main restricted universe multiverse
EOF

APT_IPV4=(
  -o Acquire::ForceIPv4=true
  -o Dir::Etc::sourcelist="${APT_SOURCES_LIST}"
  -o Dir::Etc::sourceparts="/tmp/empty-apt-sources"
  -o APT::Get::List-Cleanup=0
)

sudo apt-get "${APT_IPV4[@]}" update
sudo apt-get "${APT_IPV4[@]}" install -y \
  build-essential \
  fastqc \
  freebayes \
  graphviz \
  minimap2 \
  python3 \
  python3-venv \
  python3-pip \
  samtools \
  sra-toolkit \
  wget

if [[ "${INSTALL_MAGE:-1}" == "1" ]]; then
  python3 -m venv .venv
  . .venv/bin/activate
  python -m pip install --upgrade pip
  python -m pip install mage-ai
fi

echo "Installed command-line tools."
if [[ "${INSTALL_MAGE:-1}" == "1" ]]; then
  echo "Mage is installed into assignment3/.venv."
  echo "Start Mage with: bash scripts/start_mage.sh"
else
  echo "Mage installation was skipped (INSTALL_MAGE=0)."
fi
