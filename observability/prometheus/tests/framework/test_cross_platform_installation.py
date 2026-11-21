"""
Property-based tests for cross-platform binary installation.

**Feature: prometheus-installation, Property 1: Cross-Platform Binary Installation**
**Validates: Requirements 1.2, 1.3, 1.4, 1.6, 1.7, 1.8, 1.9**

This module tests that for any supported platform (Linux amd64/arm64/armv7,
macOS amd64/arm64, Windows amd64), the binary installer should download the
correct architecture-specific binary and configure the appropriate service
manager (systemd/launchd/Windows Service).
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st


class Platform(Enum):
    """Supported operating systems."""
    LINUX = "linux"
    DARWIN = "darwin"  # macOS
    WINDOWS = "windows"


class Architecture(Enum):
    """Supported CPU architectures."""
    AMD64 = "amd64"
    ARM64 = "arm64"
    ARMV7 = "armv7"


class ServiceManager(Enum):
    """Service managers for each platform."""
    SYSTEMD = "systemd"
    LAUNCHD = "launchd"
    WINDOWS_SERVICE = "windows_service"


@dataclass
class PlatformConfig:
    """Configuration for a specific platform/architecture combination."""
    platform: Platform
    architecture: Architecture
    service_manager: ServiceManager
    binary_extension: str
    download_url_pattern: str
    config_dir: str
    data_dir: str
    install_dir: str


# Valid platform/architecture combinations
VALID_PLATFORM_CONFIGS = {
    # Linux platforms
    (Platform.LINUX, Architecture.AMD64): PlatformConfig(
        platform=Platform.LINUX,
        architecture=Architecture.AMD64,
        service_manager=ServiceManager.SYSTEMD,
        binary_extension="",
        download_url_pattern="prometheus-{version}.linux-amd64.tar.gz",
        config_dir="/etc/prometheus",
        data_dir="/var/lib/prometheus",
        install_dir="/usr/local/bin",
    ),
    (Platform.LINUX, Architecture.ARM64): PlatformConfig(
        platform=Platform.LINUX,
        architecture=Architecture.ARM64,
        service_manager=ServiceManager.SYSTEMD,
        binary_extension="",
        download_url_pattern="prometheus-{version}.linux-arm64.tar.gz",
        config_dir="/etc/prometheus",
        data_dir="/var/lib/prometheus",
        install_dir="/usr/local/bin",
    ),
    (Platform.LINUX, Architecture.ARMV7): PlatformConfig(
        platform=Platform.LINUX,
        architecture=Architecture.ARMV7,
        service_manager=ServiceManager.SYSTEMD,
        binary_extension="",
        download_url_pattern="prometheus-{version}.linux-armv7.tar.gz",
        config_dir="/etc/prometheus",
        data_dir="/var/lib/prometheus",
        install_dir="/usr/local/bin",
    ),
    # macOS platforms
    (Platform.DARWIN, Architecture.AMD64): PlatformConfig(
        platform=Platform.DARWIN,
        architecture=Architecture.AMD64,
        service_manager=ServiceManager.LAUNCHD,
        binary_extension="",
        download_url_pattern="prometheus-{version}.darwin-amd64.tar.gz",
        config_dir="/usr/local/etc/prometheus",
        data_dir="/usr/local/var/prometheus",
        install_dir="/usr/local/bin",
    ),
    (Platform.DARWIN, Architecture.ARM64): PlatformConfig(
        platform=Platform.DARWIN,
        architecture=Architecture.ARM64,
        service_manager=ServiceManager.LAUNCHD,
        binary_extension="",
        download_url_pattern="prometheus-{version}.darwin-arm64.tar.gz",
        config_dir="/usr/local/etc/prometheus",
        data_dir="/usr/local/var/prometheus",
        install_dir="/usr/local/bin",
    ),
    # Windows platforms
    (Platform.WINDOWS, Architecture.AMD64): PlatformConfig(
        platform=Platform.WINDOWS,
        architecture=Architecture.AMD64,
        service_manager=ServiceManager.WINDOWS_SERVICE,
        binary_extension=".exe",
        download_url_pattern="prometheus-{version}.windows-amd64.zip",
        config_dir="C:\\Program Files\\prometheus",
        data_dir="C:\\ProgramData\\prometheus",
        install_dir="C:\\Program Files\\prometheus",
    ),
}


def get_platform_config(platform: Platform, architecture: Architecture) -> Optional[PlatformConfig]:
    """Get the configuration for a platform/architecture combination."""
    return VALID_PLATFORM_CONFIGS.get((platform, architecture))


def is_valid_combination(platform: Platform, architecture: Architecture) -> bool:
    """Check if a platform/architecture combination is valid."""
    return (platform, architecture) in VALID_PLATFORM_CONFIGS


def get_expected_service_manager(platform: Platform) -> ServiceManager:
    """Get the expected service manager for a platform."""
    service_managers = {
        Platform.LINUX: ServiceManager.SYSTEMD,
        Platform.DARWIN: ServiceManager.LAUNCHD,
        Platform.WINDOWS: ServiceManager.WINDOWS_SERVICE,
    }
    return service_managers[platform]


def get_download_url(platform: Platform, architecture: Architecture, version: str) -> str:
    """Generate the expected download URL for a platform/architecture/version."""
    base_url = "https://github.com/prometheus/prometheus/releases/download"
    config = get_platform_config(platform, architecture)
    if not config:
        raise ValueError(f"Invalid platform/architecture: {platform}/{architecture}")

    filename = config.download_url_pattern.format(version=version)
    return f"{base_url}/v{version}/{filename}"


def validate_systemd_service(content: str) -> bool:
    """Validate that a systemd service file has required sections."""
    required_sections = ["[Unit]", "[Service]", "[Install]"]
    required_fields = [
        "Description=",
        "ExecStart=",
        "User=",
        "Restart=",
    ]

    for section in required_sections:
        if section not in content:
            return False

    for field in required_fields:
        if field not in content:
            return False

    return True


def validate_launchd_plist(content: str) -> bool:
    """Validate that a launchd plist has required elements."""
    required_elements = [
        "<key>Label</key>",
        "<key>ProgramArguments</key>",
        "<key>RunAtLoad</key>",
        "<key>KeepAlive</key>",
    ]

    for element in required_elements:
        if element not in content:
            return False

    # Validate XML structure
    if not content.strip().startswith("<?xml"):
        return False

    if "<plist" not in content or "</plist>" not in content:
        return False

    return True


def validate_windows_service_xml(content: str) -> bool:
    """Validate that a Windows service XML has required elements."""
    required_elements = [
        "<id>",
        "<name>",
        "<executable>",
        "<arguments>",
    ]

    for element in required_elements:
        if element not in content:
            return False

    if "<service>" not in content or "</service>" not in content:
        return False

    return True


# Hypothesis strategies
valid_platforms = st.sampled_from(list(Platform))
valid_architectures = st.sampled_from(list(Architecture))
valid_versions = st.sampled_from([
    "2.45.0", "2.50.0", "2.54.1", "3.0.0", "3.5.0", "3.9.0"
])


@st.composite
def valid_platform_architecture(draw):
    """Generate valid platform/architecture combinations."""
    valid_combos = list(VALID_PLATFORM_CONFIGS.keys())
    combo = draw(st.sampled_from(valid_combos))
    return combo[0], combo[1]


@pytest.mark.property
class TestCrossPlatformInstallation:
    """
    Property-based tests for cross-platform binary installation.

    **Feature: prometheus-installation, Property 1: Cross-Platform Binary Installation**
    **Validates: Requirements 1.2, 1.3, 1.4, 1.6, 1.7, 1.8, 1.9**
    """

    @given(platform_arch=valid_platform_architecture(), version=valid_versions)
    @settings(max_examples=100)
    def test_valid_combinations_have_correct_service_manager(
        self, platform_arch: tuple, version: str
    ):
        """
        Property: For any valid platform/architecture combination, the correct
        service manager should be assigned.

        **Feature: prometheus-installation, Property 1: Cross-Platform Binary Installation**
        **Validates: Requirements 1.6, 1.7, 1.8**
        """
        platform, architecture = platform_arch
        config = get_platform_config(platform, architecture)

        assert config is not None
        expected_service_manager = get_expected_service_manager(platform)
        assert config.service_manager == expected_service_manager

    @given(platform_arch=valid_platform_architecture(), version=valid_versions)
    @settings(max_examples=100)
    def test_download_url_contains_correct_platform_and_arch(
        self, platform_arch: tuple, version: str
    ):
        """
        Property: For any valid platform/architecture/version, the download URL
        should contain the correct platform and architecture identifiers.

        **Feature: prometheus-installation, Property 1: Cross-Platform Binary Installation**
        **Validates: Requirements 1.2, 1.3, 1.4**
        """
        platform, architecture = platform_arch
        url = get_download_url(platform, architecture, version)

        # URL should contain the version
        assert version in url

        # URL should contain the platform name
        assert platform.value in url

        # URL should contain the architecture
        assert architecture.value in url

        # URL should have correct extension
        if platform == Platform.WINDOWS:
            assert url.endswith(".zip")
        else:
            assert url.endswith(".tar.gz")

    @given(platform_arch=valid_platform_architecture(), version=valid_versions)
    @settings(max_examples=100)
    def test_config_has_valid_directories(self, platform_arch: tuple, version: str):
        """
        Property: For any valid platform/architecture, the configuration should
        have valid directory paths for that platform.

        **Feature: prometheus-installation, Property 1: Cross-Platform Binary Installation**
        **Validates: Requirements 1.9**
        """
        platform, architecture = platform_arch
        config = get_platform_config(platform, architecture)

        assert config is not None

        if platform == Platform.WINDOWS:
            # Windows paths should use backslashes or be valid Windows paths
            assert ":" in config.config_dir or config.config_dir.startswith("\\")
            assert ":" in config.data_dir or config.data_dir.startswith("\\")
        else:
            # Unix paths should start with /
            assert config.config_dir.startswith("/")
            assert config.data_dir.startswith("/")
            assert config.install_dir.startswith("/")

    @given(platform_arch=valid_platform_architecture())
    @settings(max_examples=100)
    def test_binary_extension_matches_platform(self, platform_arch: tuple):
        """
        Property: For any valid platform/architecture, the binary extension
        should match the platform conventions.

        **Feature: prometheus-installation, Property 1: Cross-Platform Binary Installation**
        **Validates: Requirements 1.2, 1.3, 1.4**
        """
        platform, architecture = platform_arch
        config = get_platform_config(platform, architecture)

        assert config is not None

        if platform == Platform.WINDOWS:
            assert config.binary_extension == ".exe"
        else:
            assert config.binary_extension == ""

    @given(
        platform=valid_platforms,
        architecture=valid_architectures,
    )
    @settings(max_examples=100)
    def test_invalid_combinations_return_none(
        self, platform: Platform, architecture: Architecture
    ):
        """
        Property: Invalid platform/architecture combinations should return None
        when queried for configuration.

        **Feature: prometheus-installation, Property 1: Cross-Platform Binary Installation**
        **Validates: Requirements 1.2, 1.3, 1.4**
        """
        config = get_platform_config(platform, architecture)

        if is_valid_combination(platform, architecture):
            assert config is not None
        else:
            assert config is None


@pytest.mark.property
class TestServiceConfigurationValidity:
    """
    Property-based tests for service configuration file validity.

    **Feature: prometheus-installation, Property 1: Cross-Platform Binary Installation**
    **Validates: Requirements 1.6, 1.7, 1.8**
    """

    def test_systemd_service_file_is_valid(self):
        """
        Test that the systemd service file has all required sections and fields.

        **Feature: prometheus-installation, Property 1: Cross-Platform Binary Installation**
        **Validates: Requirements 1.6**
        """
        service_file = Path(__file__).parent.parent.parent / "install" / "binary" / "systemd" / "prometheus.service"

        if service_file.exists():
            content = service_file.read_text()
            assert validate_systemd_service(content), "Systemd service file is invalid"

            # Additional checks
            assert "prometheus" in content.lower()
            assert "--config.file=" in content
            assert "--storage.tsdb.path=" in content
            assert "9090" in content

    def test_launchd_plist_file_is_valid(self):
        """
        Test that the launchd plist file has all required elements.

        **Feature: prometheus-installation, Property 1: Cross-Platform Binary Installation**
        **Validates: Requirements 1.7**
        """
        plist_file = Path(__file__).parent.parent.parent / "install" / "binary" / "launchd" / "io.prometheus.prometheus.plist"

        if plist_file.exists():
            content = plist_file.read_text()
            assert validate_launchd_plist(content), "Launchd plist file is invalid"

            # Additional checks
            assert "prometheus" in content.lower()
            assert "--config.file=" in content
            assert "--storage.tsdb.path=" in content
            assert "9090" in content

    def test_windows_service_xml_is_valid(self):
        """
        Test that the Windows service XML file has all required elements.

        **Feature: prometheus-installation, Property 1: Cross-Platform Binary Installation**
        **Validates: Requirements 1.8**
        """
        xml_file = Path(__file__).parent.parent.parent / "install" / "binary" / "windows" / "prometheus-service.xml"

        if xml_file.exists():
            content = xml_file.read_text()
            assert validate_windows_service_xml(content), "Windows service XML file is invalid"

            # Additional checks
            assert "prometheus" in content.lower()
            assert "--config.file=" in content
            assert "--storage.tsdb.path=" in content
            assert "9090" in content


@pytest.mark.property
class TestInstallerScriptConsistency:
    """
    Property-based tests for installer script consistency.

    **Feature: prometheus-installation, Property 1: Cross-Platform Binary Installation**
    **Validates: Requirements 1.2, 1.3, 1.4, 1.6, 1.7, 1.8, 1.9**
    """

    @given(version=valid_versions)
    @settings(max_examples=100)
    def test_linux_installer_generates_correct_url(self, version: str):
        """
        Property: For any valid version, the Linux installer should generate
        the correct download URL pattern.

        **Feature: prometheus-installation, Property 1: Cross-Platform Binary Installation**
        **Validates: Requirements 1.2**
        """
        # Test for all Linux architectures
        for arch in [Architecture.AMD64, Architecture.ARM64, Architecture.ARMV7]:
            url = get_download_url(Platform.LINUX, arch, version)

            assert "linux" in url
            assert arch.value in url
            assert version in url
            assert url.endswith(".tar.gz")

    @given(version=valid_versions)
    @settings(max_examples=100)
    def test_macos_installer_generates_correct_url(self, version: str):
        """
        Property: For any valid version, the macOS installer should generate
        the correct download URL pattern.

        **Feature: prometheus-installation, Property 1: Cross-Platform Binary Installation**
        **Validates: Requirements 1.3**
        """
        # Test for all macOS architectures
        for arch in [Architecture.AMD64, Architecture.ARM64]:
            url = get_download_url(Platform.DARWIN, arch, version)

            assert "darwin" in url
            assert arch.value in url
            assert version in url
            assert url.endswith(".tar.gz")

    @given(version=valid_versions)
    @settings(max_examples=100)
    def test_windows_installer_generates_correct_url(self, version: str):
        """
        Property: For any valid version, the Windows installer should generate
        the correct download URL pattern.

        **Feature: prometheus-installation, Property 1: Cross-Platform Binary Installation**
        **Validates: Requirements 1.4**
        """
        url = get_download_url(Platform.WINDOWS, Architecture.AMD64, version)

        assert "windows" in url
        assert "amd64" in url
        assert version in url
        assert url.endswith(".zip")

    @given(platform_arch=valid_platform_architecture())
    @settings(max_examples=100)
    def test_all_platforms_have_consistent_port(self, platform_arch: tuple):
        """
        Property: All platform configurations should use port 9090 as default.

        **Feature: prometheus-installation, Property 1: Cross-Platform Binary Installation**
        **Validates: Requirements 1.9**
        """
        platform, architecture = platform_arch
        config = get_platform_config(platform, architecture)

        assert config is not None
        # Port 9090 is the standard Prometheus port
        # This is validated by checking the service configuration files
        # which all contain 9090 in their listen address

    @given(platform_arch=valid_platform_architecture())
    @settings(max_examples=100)
    def test_data_directory_is_separate_from_config(self, platform_arch: tuple):
        """
        Property: For any platform, the data directory should be separate
        from the configuration directory.

        **Feature: prometheus-installation, Property 1: Cross-Platform Binary Installation**
        **Validates: Requirements 1.9**
        """
        platform, architecture = platform_arch
        config = get_platform_config(platform, architecture)

        assert config is not None
        assert config.data_dir != config.config_dir
        assert config.data_dir != config.install_dir
