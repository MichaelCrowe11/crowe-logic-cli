#!/usr/bin/env python3
"""
Build standalone executable for Crowe Logic CLI.

Usage:
    python build_exe.py [--onefile | --onedir] [--clean] [--debug]

Options:
    --onefile   Create a single executable file (default)
    --onedir    Create a directory with executable and dependencies
    --clean     Clean build artifacts before building
    --debug     Include debug info in the build
"""

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def clean_build():
    """Remove previous build artifacts."""
    dirs_to_clean = ["build", "dist", "__pycache__"]
    files_to_clean = ["*.spec"]

    for dir_name in dirs_to_clean:
        path = Path(dir_name)
        if path.exists():
            print(f"Removing {path}...")
            shutil.rmtree(path)

    for pattern in files_to_clean:
        for path in Path(".").glob(pattern):
            print(f"Removing {path}...")
            path.unlink()


def get_platform_name() -> str:
    """Get platform identifier for the executable name."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if machine in ("x86_64", "amd64"):
        machine = "x64"
    elif machine in ("arm64", "aarch64"):
        machine = "arm64"

    return f"{system}-{machine}"


def build(onefile: bool = True, debug: bool = False):
    """Build the executable."""
    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller>=6.0.0"],
            check=True,
        )

    # Base command
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        "crowelogic",
        "--noconfirm",
    ]

    # Build mode
    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    # Debug mode
    if debug:
        cmd.append("--debug=all")
    else:
        cmd.append("--strip")

    # Hidden imports for Azure SDK and other modules
    hidden_imports = [
        "azure.identity",
        "azure.keyvault.secrets",
        "azure.core",
        "msal",
        "msal_extensions",
        "httpx",
        "httpx_sse",
        "rich",
        "typer",
        "click",
    ]
    for module in hidden_imports:
        cmd.extend(["--hidden-import", module])

    # Add data files
    agents_path = Path("agents")
    if agents_path.exists():
        sep = ";" if platform.system() == "Windows" else ":"
        cmd.extend(["--add-data", f"agents{sep}agents"])

    # Entry point
    cmd.append("src/crowe_logic_cli/main.py")

    print("Building with command:")
    print(" ".join(cmd))
    print()

    subprocess.run(cmd, check=True)

    # Report results
    if onefile:
        exe_name = "crowelogic.exe" if platform.system() == "Windows" else "crowelogic"
        exe_path = Path("dist") / exe_name
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\nExecutable created: {exe_path}")
            print(f"Size: {size_mb:.1f} MB")
            print(f"Platform: {get_platform_name()}")
            print("\nTo install globally:")
            print(f"  sudo cp {exe_path} /usr/local/bin/crowelogic")
    else:
        print("\nDirectory build created: dist/crowelogic/")
        print("Run with: ./dist/crowelogic/crowelogic")


def main():
    parser = argparse.ArgumentParser(description="Build Crowe Logic CLI executable")
    parser.add_argument(
        "--onefile",
        action="store_true",
        default=True,
        help="Create single executable (default)",
    )
    parser.add_argument(
        "--onedir",
        action="store_true",
        help="Create directory with dependencies",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts first",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Include debug information",
    )

    args = parser.parse_args()

    if args.clean:
        clean_build()

    build(onefile=not args.onedir, debug=args.debug)


if __name__ == "__main__":
    main()
