# typed: false
# frozen_string_literal: true

class Crowelogic < Formula
  include Language::Python::Virtualenv

  desc "Quantum-Enhanced Scientific Reasoning CLI"
  homepage "https://github.com/michaelcrowe/crowe-logic-cli"
  url "https://github.com/michaelcrowe/crowe-logic-cli/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "PLACEHOLDER_SHA256_REPLACE_AFTER_RELEASE"
  license "MIT"
  head "https://github.com/michaelcrowe/crowe-logic-cli.git", branch: "main"

  depends_on "python@3.11"

  # Core CLI dependencies
  resource "typer" do
    url "https://files.pythonhosted.org/packages/ty/per/typer-0.21.1.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/ri/ch/rich-14.2.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "click" do
    url "https://files.pythonhosted.org/packages/cli/ck/click-8.3.1.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "shellingham" do
    url "https://files.pythonhosted.org/packages/sh/el/shellingham-1.5.4.tar.gz"
    sha256 "PLACEHOLDER"
  end

  # Rich dependencies
  resource "markdown-it-py" do
    url "https://files.pythonhosted.org/packages/ma/rk/markdown_it_py-4.0.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "mdurl" do
    url "https://files.pythonhosted.org/packages/md/ur/mdurl-0.1.2.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "pygments" do
    url "https://files.pythonhosted.org/packages/py/gm/pygments-2.19.2.tar.gz"
    sha256 "PLACEHOLDER"
  end

  # HTTP client dependencies
  resource "httpx" do
    url "https://files.pythonhosted.org/packages/ht/tp/httpx-0.28.1.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "httpx-sse" do
    url "https://files.pythonhosted.org/packages/ht/tp/httpx_sse-0.4.3.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "httpcore" do
    url "https://files.pythonhosted.org/packages/ht/tp/httpcore-1.0.9.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "h11" do
    url "https://files.pythonhosted.org/packages/h1/1/h11-0.16.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "anyio" do
    url "https://files.pythonhosted.org/packages/an/yi/anyio-4.12.1.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "certifi" do
    url "https://files.pythonhosted.org/packages/ce/rt/certifi-2026.1.4.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "idna" do
    url "https://files.pythonhosted.org/packages/id/na/idna-3.11.tar.gz"
    sha256 "PLACEHOLDER"
  end

  # Azure dependencies
  resource "azure-identity" do
    url "https://files.pythonhosted.org/packages/az/ur/azure_identity-1.25.1.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "azure-keyvault-secrets" do
    url "https://files.pythonhosted.org/packages/az/ur/azure_keyvault_secrets-4.10.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "azure-core" do
    url "https://files.pythonhosted.org/packages/az/ur/azure_core-1.38.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "msal" do
    url "https://files.pythonhosted.org/packages/ms/al/msal-1.34.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "msal-extensions" do
    url "https://files.pythonhosted.org/packages/ms/al/msal_extensions-1.3.1.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "cryptography" do
    url "https://files.pythonhosted.org/packages/cr/yp/cryptography-46.0.3.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "cffi" do
    url "https://files.pythonhosted.org/packages/cf/fi/cffi-2.0.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "pycparser" do
    url "https://files.pythonhosted.org/packages/py/cp/pycparser-2.23.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "pyjwt" do
    url "https://files.pythonhosted.org/packages/py/jw/pyjwt-2.10.1.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "requests" do
    url "https://files.pythonhosted.org/packages/re/qu/requests-2.32.5.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "urllib3" do
    url "https://files.pythonhosted.org/packages/ur/ll/urllib3-2.6.3.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "charset-normalizer" do
    url "https://files.pythonhosted.org/packages/ch/ar/charset_normalizer-3.4.4.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "isodate" do
    url "https://files.pythonhosted.org/packages/is/od/isodate-0.7.2.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "typing-extensions" do
    url "https://files.pythonhosted.org/packages/ty/pi/typing_extensions-4.15.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

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
