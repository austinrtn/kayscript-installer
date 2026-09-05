import os
import pwd
import shlex
from shutil import which
from subprocess import CalledProcessError as ProcessError, run
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from files import File, config_dir, files, sudoers_rule, project_dir, root_service, udev_rule, user_service, kayscript

pkg_manager_cmd=""
root_dir: Path = Path.cwd()
local_path: Path = Path(Path.home() / "Documents/KayScript/kayscript-0.2.tar.gz").resolve()

def install_script(work_dir: Path, download_files: bool) -> None:
    _ = run(["sudo", "-v"], check=False)
   
    print("> Beginning Installation!")

    if download_files:
        print("> Downloading")
        if not File.download_repo(work_dir):
            return
    else:
        if not local_path.exists():
            print(f"Local Archive Path does not exist: {local_path}")
            raise RuntimeError
        res = run(
            ["tar", "-xzf", str(local_path), "--strip-components=1"],
            check=False,
            cwd=work_dir,
        )

        if res.returncode != 0:
            print(f"Failed to unarchive local tar file: {res.returncode}")
            raise RuntimeError

    if not compile(work_dir):
        return
                
    user = get_username()
    udev_rule.replace_text("__ROOT_SERVICE__", root_service.dest.name)
    root_service.replace_text("__USER__", user)
    root_service.replace_text("__SERVICE__", user_service.dest.name)
    sudoers_rule.replace_text("__USER__", user)
    sudoers_rule.replace_text("__SCRIPT__", str(kayscript.dest))
    user_service.replace_text("__SCRIPT__", str(kayscript.dest))

    print(">Installing Files...")
    _ = run(
        [
            "sudo",
            "mkdir",
            "-p",
            project_dir,
        ],
        check=False,
    )
    
    _ = run(["mkdir", "-p", config_dir], check=False)
    _ = run(["sudo", "mkdir", "-p", "/mnt/"], check=False)

    for file in files:
        file.install()

    print("Files Installed!")
    print()

    venv_dir = project_dir / ".venv"
    if not venv_dir.is_dir():
        print("> Installing Python Virtual Enviornment...")

        try:
            _ = run(
                ["sudo", "python3", "-m", "venv", str(project_dir / ".venv")], check=True
            )
        except ProcessError as error:
            print(
                f"Unable to install python virtual enviornment: {error.returncode}",
                file=sys.stdout,
            )

        print("Python Venv Installed!")

    print("> Updating Rules And Services")

    _ = run(["sudo", "udevadm", "control", "--reload"], check=False)
    _ = run(["sudo", "systemctl", "daemon-reload"], check=False)
    _ = run(["systemctl", "--user", "daemon-reload"], check=False)

    print("Rules Updated!")
    print()
    print("Installation Finished!")

def compile(work_dir: Path) -> bool:
    try: 
        ensure_pipx()
    except ProcessError as err:
        print(f"Could not install pipx: {err.returncode}")
        return False

    try:
        ensure_pyinstaller()
    except ProcessError as err:
        print(f"Could not install Pyinstaller: {err.returncode}")
        return False

    kayscript_app_path = work_dir / "app.py"
    if not kayscript_app_path.exists(): 
        print("Cannnot find the source compiler python program.")
        print(f"{kayscript_app_path}")
        return False

    print("> Compiling Python Applicaiton...")
    try: 
        _ = run(
            [
                "pyinstaller",
                "--clean",
                "--onefile",
                "--name", "kayscript",
                "--workpath", str(work_dir / ".pyinstaller-build"),
                "--distpath", str(root_dir),
                str(kayscript_app_path),
            ],
            check=True,
            cwd=work_dir,
        )
        
    except ProcessError as err:
        print(f"Could not compile executable: {err.returncode}")
        return False

    print("Application Compiled!")
    print()
    return True
        
def ensure_pipx() -> None:
    if which("pipx") is None: 
        print("> Installing Pipx...")
    else: 
        return

    install_cmd = shlex.split(pkg_manager_cmd.replace("__pkg__", "python-pipx"))
    _ = run(
        install_cmd,
        check=True,
    )

    if which("pipx") is None:
              raise RuntimeError("pipx was installed but is not available in PATH")
    else: 
        print("Pipx Installed!")
        print()
    
def ensure_pyinstaller() -> None: 
    if which("pyinstaller") is None: 
        print("> Installing Pyinstaller...")
    else: 
        return
        
    _ = run(
        [
            "pipx",
            "install",
            "pyinstaller",
        ],
        check=True,
    )

    if which("pyinstaller") is None:
                raise RuntimeError("pyinstaller was installed but is not available in PATH")
    else: 
        print("Pyinstaller Installed!")
        print()
        
def uninstall() -> None:
    confirm = input("Are you sure you want to uninstall KayScript? [Y/n]\t")
    confirm = confirm.lower()

    if confirm == "y":
        print(">Uninstalling...")
        for file in files:
            file.uninstall()

        _ = run(["sudo", "rm", "-rf", str(project_dir)], check=False)
        print("Uninstalled!")

def get_username() -> str:
    if os.geteuid() == 0 and "SUDO_UID" in os.environ:
        uid = int(os.environ["SUDO_UID"])
    else: 
        uid = os.getuid()
        
    return pwd.getpwuid(uid).pw_name

def check(): 
    _ = run(["sudo", "-v"], check=False)

    print("\033[2J\033[H", end="", flush=True)
    for file in files:
        header: str = f"### {file.desc} ###"
        print(f"{header}")
        print("_" * len(header))
        print()
        print(f"Local Path: {file.tmp_path}")
        print(f"Dest Path: {file.dest}")

        exists = file.validate_dest_path()
        match = False if not exists else files_match(file)
        
         
        print(f"Exists: {exists}")
        print(f"Files Match: {match if exists else 'N.A'}")
        print()

        cat = input("Press 'p' to print or any other key to continue\n").lower() == "p"
        if cat: 
            print("\033[2J\033[H", end="", flush=True)
            print(file.dest.read_text())
            print()
            _ = input("Press any key to continue")
            
        print("\033[2J\033[H", end="", flush=True)

def files_match(file: File) -> bool:
    cmp = ["cmp", "--silent", "--", str(file.tmp_path), str(file.dest)]

    if file.root_owned:
        cmp.insert(0, "sudo")

    result = run(cmp, check=False)

    if result.returncode == 0:
        return True
    elif result.returncode == 1: 
        return False

    raise RuntimeError(f"Could not compare {file.tmp_path} and {file.dest}")
    
def main() -> None:
    option = "--d"
    global pkg_manager_cmd
    pkg_manager_cmd = "sudo pacman -S --needed __pkg__"
    
    if len(sys.argv) > 1:
        option = sys.argv[1]
    if len(sys.argv) > 2: 
        pkg_manager_cmd = sys.argv[2]

    if option in {"--d", "--l"}:
        download_files = option == "--d"
        with TemporaryDirectory() as work_dir:
            install_script(Path(work_dir), download_files)
            
    elif option == "--r":
        uninstall()

    elif option == "--c":
        check()


if __name__ == "__main__":
    try: 
        main()
    except KeyboardInterrupt: 
        pass
