#!/usr/bin/env python3
"""
Generate Homebrew formula with correct PyPI URLs and SHA256 hashes.

Usage:
    python scripts/generate_formula.py > homebrew-tap/Formula/crowelogic.rb
"""

import json
import sys
import urllib.request
from typing import Optional


DEPENDENCIES = [
    # (pypi_name, version)
    ("typer", "0.21.1"),
    ("rich", "14.2.0"),
    ("click", "8.3.1"),
    ("shellingham", "1.5.4"),
    ("markdown-it-py", "4.0.0"),
    ("mdurl", "0.1.2"),
    ("pygments", "2.19.2"),
    ("httpx", "0.28.1"),
    ("httpx-sse", "0.4.3"),
    ("httpcore", "1.0.9"),
    ("h11", "0.16.0"),
    ("anyio", "4.12.1"),
    ("certifi", "2026.1.4"),
    ("idna", "3.11"),
    ("azure-identity", "1.25.1"),
    ("azure-keyvault-secrets", "4.10.0"),
    ("azure-core", "1.38.0"),
    ("msal", "1.34.0"),
    ("msal-extensions", "1.3.1"),
    ("cryptography", "46.0.3"),
    ("cffi", "2.0.0"),
    ("pycparser", "2.23"),
    ("pyjwt", "2.10.1"),
    ("requests", "2.32.5"),
    ("urllib3", "2.6.3"),
    ("charset-normalizer", "3.4.4"),
    ("isodate", "0.7.2"),
    ("typing-extensions", "4.15.0"),
]


def get_pypi_info(package: str, version: str) -> Optional[dict]:
    """Fetch package info from PyPI."""
    url = f"https://pypi.org/pypi/{package}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"  # Warning: Could not fetch {package}: {e}", file=sys.stderr)
        return None


def get_sdist_info(pypi_data: dict) -> Optional[tuple]:
    """Extract sdist URL and SHA256 from PyPI response."""
    for file_info in pypi_data.get("urls", []):
        if file_info.get("packagetype") == "sdist":
            return file_info["url"], file_info["digests"]["sha256"]
    return None


def generate_resource_block(name: str, url: str, sha256: str) -> str:
    """Generate a Homebrew resource block."""
    return f'''  resource "{name}" do
    url "{url}"
    sha256 "{sha256}"
  end
'''


def main():
    print("# Fetching PyPI package information...", file=sys.stderr)
    print("# This may take a moment...\n", file=sys.stderr)

    resources = []
    for package, version in DEPENDENCIES:
        info = get_pypi_info(package, version)
        if info:
            sdist = get_sdist_info(info)
            if sdist:
                url, sha256 = sdist
                resources.append(generate_resource_block(package, url, sha256))
                print(f"  # Found: {package} {version}", file=sys.stderr)
            else:
                resources.append(f'  # MANUAL: {package} {version} - no sdist found\n')
        else:
            resources.append(f'  # MANUAL: {package} {version} - fetch failed\n')

    # Print the formula
    print('''# typed: false
# frozen_string_literal: true

class Crowelogic < Formula
  include Language::Python::Virtualenv

  desc "Quantum-Enhanced Scientific Reasoning CLI"
  homepage "https://github.com/michaelcrowe/crowe-logic-cli"
  url "https://github.com/michaelcrowe/crowe-logic-cli/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "REPLACE_WITH_RELEASE_SHA256"
  license "MIT"
  head "https://github.com/michaelcrowe/crowe-logic-cli.git", branch: "main"

  depends_on "python@3.11"

''')

    for resource in resources:
        print(resource)

    print('''
  def install
    virtualenv_install_with_resources

    # Install agent files
    pkgshare.install "agents" if File.directory?("agents")
  end

  def caveats
    <<~EOS
      To get started, run:
        crowelogic config

      Agent files are installed to:
        #{pkgshare}/agents

      Configuration file location:
        ~/.crowelogic.toml
    EOS
  end

  test do
    assert_match "crowe-logic-cli", shell_output("#{bin}/crowelogic version")
    assert_match "Commands", shell_output("#{bin}/crowelogic --help")
  end
end
''')


if __name__ == "__main__":
    main()