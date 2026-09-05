import subprocess
from dataclasses import dataclass
from pathlib import Path

config_dir = Path(Path.home() / ".config/systemd/user/").resolve()
project_dir = Path("/var/lib/kayscript")

repo_url = "https://github.com/austinrtn/KayScript/archive/refs/tags/0.1.tar.gz"

#################################
###### FILE CLASS ###############
#################################
local_file_dir = Path.cwd().resolve()

@dataclass()
class File:
    name: str
    desc: str
    dest: Path
    mode: int
    root_owned: bool
    tmp_path: Path = local_file_dir

    @classmethod
    def download_repo(cls, destination: Path) -> bool:
        curl_cmd = ["curl", "--fail", "--silent", "--show-error", "--location", f"{repo_url}"] 
        tar_cmd = ["tar", "-xz", "--strip-components=1"]
        
        with subprocess.Popen(curl_cmd, stdout=subprocess.PIPE) as curl: 
            assert curl.stdout is not None
            
            tar_res = subprocess.run(
                tar_cmd,
                check=False,
                cwd=destination,
                stdin=curl.stdout,
            )
            
            curl.stdout.close()
            curl_status = curl.wait()

            if curl_status != 0:
                print(f"Download failed: curl exited with {curl_status}")
                return False
    
            if tar_res.returncode != 0:
                print(f"Extraction failed: tar exited with {tar_res.returncode}")
                return False

        return True
            
    def __post_init__(self) -> None:
        self.tmp_path = (local_file_dir / self.name).resolve()
        self.dest = self.dest.resolve()
        
    def validate_tmp_path(self) -> bool:
        return self.tmp_path.exists()

    def validate_dest_path(self) -> bool: 
        cmd = ["test", "-e", str(self.dest)]
        
        if self.root_owned: cmd.insert(0, "sudo")
        return subprocess.run(cmd, check=False).returncode == 0

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
udev_rule = File(
    name="udev_rule",
    desc="udev_rule",
    dest=Path("/etc/udev/rules.d/99-usb-connected.rules"),
    mode=0o644,
    root_owned=True,
)

sudoers_rule = File(
    name="sudoers_rule",
    desc="sudoers_rule",
    dest=Path("/etc/sudoers.d/kayscript-bypass"),
    mode=0o440,
    root_owned=True,
)

root_service = File(
    name="root_service",
    desc="root_service",
    dest=Path("/etc/systemd/system/kayscript-usb.service"),
    mode=0o644,
    root_owned=True,
)

user_service = File(
    name="user_service",
    desc="user_service",
    dest=Path.home() / ".config/systemd/user/kayscript.service",
    mode=0o644,
    root_owned=False,
)

# app_py = File(
#     name="app.py",
#     desc="Main",
#     dest=project_dir / "app.py",
#     mode=0o755,
#     root_owned=True,
#     tmp_path=Path("./")
# )

kayscript = File(
    name="kayscript",
    desc="Main Script",
    dest=project_dir / "KayScript",
    mode=0o755,
    root_owned=True,
    tmp_path=Path("./")
)
files = [udev_rule, root_service, kayscript, user_service, sudoers_rule]
