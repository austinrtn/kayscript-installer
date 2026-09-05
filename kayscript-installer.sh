#!/bin/sh
installer_url="https://github.com/austinrtn/kayscript-installer/archive/refs/tags/1.0.tar.gz"
pkg_manager_cmd=""

main() {
    if ! command -v python3 >/dev/null 2>&1; then
        echo "Need to install python"
        exit 1
    fi
    if ! command -v curl >/dev/null 2>&1; then
        echo "Need to install curl"
        exit 1
    fi

    if command -v pacman >/dev/null 2>&1; then
        pkg_manager_cmd="sudo pacman -S --needed __pkg__"
    elif command -v apt-get >/dev/null 2>&1; then
        pkg_manager_cmd="sudo apt-get install -y __pkg__"
    else
        echo "No supported package manager found..."
        exit 1
    fi

    work_dir="$(mktemp -d)" || exit 1
    trap 'rm -rf -- "$work_dir"' EXIT

    cd "$work_dir" || exit 1
    echo "Downloading installer..."

    curl \
        --fail \
        --location \
        --silent \
        --show-error \
        --output installer.tar.gz \
        "$installer_url" || exit 1

    tar \
        -xzf installer.tar.gz \
        --strip-components=1 || exit 1

    python3 app.py --d "$pkg_manager_cmd"
}

main
