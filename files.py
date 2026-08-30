import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


#################################
###### FILE CLASS ###############
#################################
local_file_dir = Path(Path.home() / "Documents/kayscript-installer").resolve()

@dataclass()
class File:
    name: str
    desc: str
    url: str
    dest: Path
    mode: int
    root_owned: bool
    tmp_path: Path = local_file_dir

    def __post_init__(self) -> None:
        self.tmp_path = (local_file_dir / self.name).resolve()
        self.dest = self.dest.resolve()

    def validate_tmp_path(self) -> bool:
        return self.tmp_path.exists()

    def validate_dest_path(self) -> bool: 
        cmd = ["test", "-e", str(self.dest)]
        
        if self.root_owned: cmd.insert(0, "sudo")
        return subprocess.run(cmd, check=False).returncode == 0

    def download(self) -> bool:
        result = subprocess.run(
            [
                "curl",
                "--fail",
                "--silent",
                "--show-error",
                "--location",
                "--max-time",
                "15",
                "--output",
                self.name,
                self.url,
            ],
            check=False,
        )

        match result.returncode:
            case 0:
                return True
            case 6:
                print(f"Could not resolve the host for {self.name}", file=sys.stderr)
            case 22:
                print(
                    f"The server returned an HTTP error for {self.name}",
                    file=sys.stderr,
                )
                print(f"{self.url}")
            case 28:
                print(f"The download timed out for {self.name}", file=sys.stderr)
            case error_code:
                print(
                    f"Failed to download {self.name}: "
                    + f"curl exited with code {error_code}",
                    file=sys.stderr,
                )

        return False

    def replace_text(self, old: str, new: str) -> None:
        _ = self.tmp_path.write_text(self.tmp_path.read_text().replace(old, new))

    def install(self) -> None:
        if self.root_owned:
            _ = subprocess.run(
                [
                    "sudo",
                    "install",
                    "-o",
                    "root",
                    "-g",
                    "root",
                    "-m",
                    f"{self.mode:o}",
                    f"{self.tmp_path}",
                    f"{self.dest}",
                ],
                check=False,
            )
        else:
            _ = subprocess.run(
                [
                    "install",
                    "-m",
                    f"{self.mode:o}",
                    f"{self.tmp_path}",
                    f"{self.dest}",
                ],
                check=False,
            )

    def uninstall(self) -> None:
        _ = subprocess.run(["sudo", "rm", "-f", str(self.dest)], check=False)

#################################
###### FILE PATHS ##############
#################################
kayscript_app_path = Path(Path.home() / "Documents/KayScript/app.py").resolve()
config_dir = Path(Path.home() / ".config/systemd/user/").resolve()
project_dir = Path("/var/lib/kayscript")

gh_url = "https://raw.githubusercontent.com/austinrtn/KayScript/refs/heads/master/"
kayscript_url= "https://github.com/austinrtn/KayScript/blob/c21bc06e163389a6f6afb82f8ceed6b9b7604df3/dist/kayscript"

udev_rule = File(
    name="udev_rule",
    desc="udev_rule",
    url=f"{gh_url}udev_rule",
    dest=Path("/etc/udev/rules.d/99-usb-connected.rules"),
    mode=0o644,
    root_owned=True,
)

sudoers_rule = File(
    name="sudoers_rule",
    desc="sudoers_rule",
    url=f"{gh_url}sudoers_rule",
    dest=Path("/etc/sudoers.d/kayscript-bypass"),
    mode=0o440,
    root_owned=True,
)

root_service = File(
    name="root_service",
    desc="root_service",
    url=f"{gh_url}root_service",
    dest=Path("/etc/systemd/system/kayscript-usb.service"),
    mode=0o644,
    root_owned=True,
)

user_service = File(
    name="user_service",
    desc="user_service",
    url=f"{gh_url}user_service",
    dest=Path.home() / ".config/systemd/user/kayscript.service",
    mode=0o644,
    root_owned=False,
)

kayscript = File(
    name="kayscript",
    desc="Main Script",
    url=f"{gh_url}dist/kayscript",
    dest=project_dir / "KayScript",
    mode=0o755,
    root_owned=True,
    tmp_path=Path("./dist/")
)
files = [udev_rule, root_service, kayscript, user_service, sudoers_rule]
