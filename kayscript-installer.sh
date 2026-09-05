#!/bin/sh
installer_url="https://github.com/austinrtn/kayscript-installer/archive/refs/tags/1.0.tar.gz"
pkg_manager_cmd=""

main() {
    if [[ -z $(command -v python) ]]; then 
        echo "Need to install python"
        exit 1
    fi
    if [[ -z $(command -v curl) ]]; then 
        echo "Need to install curl"
        exit 1
    fi
    
    if [[ -n $(command -v pacman) ]]; then 
        pkg_manager_cmd="sudo pacman -S --needed __pkg__"
    elif [[ -n $(command -v pacman) ]]; then 
        pkg_manager_cmd="sudo apt-get install -y __pkg__"
    else 
        echo "No supported package manager found..."
        exit 1
    fi

    work_dir="$(mktemp -d)"
    trap 'rm -rf "$work_dir"' EXIT
    
    cd "$work_dir"
    echo "Downloading installer..."
    curl --fail --location --silent "$installer_url" | tar -xz --strip-components=1

    python3 app.py --l "$pkg_manager_cmd"
}

main