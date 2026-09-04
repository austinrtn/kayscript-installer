#!/bin/sh
installer_url="https://github.com/austinrtn/kayscript-installer/archive/refs/tags/0.1.tar.gz"
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
        pkg_manager_cmd="pacman -S --needed {pkg}"
    elif [[ -n $(command -v pacman) ]]; then 
        pkg_manager_cmd="apt-get install -y {pkg}"
    else 
        echo "No package manager found..."
        exit 1
    fi

    work_dir=mktemp()
    trap 'rm -rf "$work_dir"' EXIT
    
    cd "$work_dir"
    curl --fail --location --output repo.tar.gz "$installer_url" |
        tar -xz --strip-components-1

    python "app.py"
}

main