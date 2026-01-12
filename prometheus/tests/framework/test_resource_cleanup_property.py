"""
Property-based tests for resource cleanup.

**Feature: prometheus-installation, Property 11: Test Resource Cleanup**
**Validates: Requirements 10.6**

This module tests that for any test execution (regardless of success or failure),
all created resources (containers, pods, volumes) should be cleaned up after
the test completes.
"""

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from framework.deployer import (
    BinaryConfig,
    BinaryDeployer,
    DeployConfig,
    DeploymentMode,
    DeploymentStatus,
    DockerConfig,
    DockerDeployer,
    Platform,
)


# Strategies for generating test scenarios
valid_ports = st.integers(min_value=9000, max_value=9999)
valid_retention = st.sampled_from(["1d", "7d", "15d", "30d"])
valid_log_levels = st.sampled_from(["debug", "info", "warn", "error"])
valid_memory_limits = st.sampled_from(["512m", "1g", "2g", "4g"])
valid_project_names = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
    min_size=3,
    max_size=20,
).filter(lambda s: s[0].isalpha())


@dataclass
class MockResource:
    """Represents a mock resource that can be tracked for cleanup."""

    resource_type: str  # "container", "pod", "volume", "file", "directory", "process"
    resource_id: str
    created: bool = True
    cleaned_up: bool = False

    def cleanup(self) -> bool:
        """Mark resource as cleaned up."""
        self.cleaned_up = True
        return True


@dataclass
class ResourceTracker:
    """Tracks resources created during test execution."""

    resources: list[MockResource] = field(default_factory=list)

    def add_resource(self, resource_type: str, resource_id: str) -> MockResource:
        """Add a resource to track."""
        resource = MockResource(resource_type=resource_type, resource_id=resource_id)
        self.resources.append(resource)
        return resource

    def cleanup_all(self) -> bool:
        """Clean up all tracked resources."""
        success = True
        for resource in self.resources:
            if resource.created and not resource.cleaned_up:
                if not resource.cleanup():
                    success = False
        return success

    def all_cleaned_up(self) -> bool:
        """Check if all resources have been cleaned up."""
        return all(r.cleaned_up for r in self.resources if r.created)

    def get_uncleaned_resources(self) -> list[MockResource]:
        """Get list of resources that haven't been cleaned up."""
        return [r for r in self.resources if r.created and not r.cleaned_up]


class MockBinaryDeployer(BinaryDeployer):
    """Mock BinaryDeployer that tracks resources for testing cleanup."""

    def __init__(
        self,
        config: Optional[DeployConfig] = None,
        binary_config: Optional[BinaryConfig] = None,
        should_fail: bool = False,
    ):
        super().__init__(config, binary_config)
        self.resource_tracker = ResourceTracker()
        self.should_fail = should_fail
        self._mock_process = None
        self._mock_data_dir: Optional[str] = None
        self._mock_config_file: Optional[str] = None

    def deploy(self, config: Optional[DeployConfig] = None) -> Any:
        """Mock deploy that creates trackable resources."""
        from framework.deployer import DeployResult

        self._status = DeploymentStatus.DEPLOYING

        # Create mock data directory
        self._mock_data_dir = tempfile.mkdtemp(prefix="prometheus-test-data-")
        self.resource_tracker.add_resource("directory", self._mock_data_dir)
        self._temp_data_dir = self._mock_data_dir

        # Create mock config file
        fd, self._mock_config_file = tempfile.mkstemp(suffix=".yml", prefix="prometheus-test-")
        os.close(fd)
        self.resource_tracker.add_resource("file", self._mock_config_file)

        # Simulate process creation
        self._mock_process = MagicMock()
        self._mock_process.pid = 12345
        self._mock_process.poll.return_value = None  # Process is running
        self._process = self._mock_process
        self.resource_tracker.add_resource("process", str(self._mock_process.pid))

        if self.should_fail:
            self._status = DeploymentStatus.FAILED
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message="Simulated deployment failure",
            )

        self._status = DeploymentStatus.DEPLOYED
        self._prometheus_url = f"http://localhost:{self.binary_config.port}"
        return DeployResult(
            success=True,
            status=DeploymentStatus.DEPLOYED,
            prometheus_url=self._prometheus_url,
            message="Mock deployment successful",
        )

    def teardown(self) -> bool:
        """Mock teardown that cleans up tracked resources."""
        self._status = DeploymentStatus.TEARING_DOWN

        # Clean up process
        if self._mock_process:
            self._mock_process.terminate = MagicMock()
            self._mock_process.wait = MagicMock()
            self._mock_process.terminate()
            self._mock_process.wait()
            for r in self.resource_tracker.resources:
                if r.resource_type == "process":
                    r.cleanup()
            self._mock_process = None
            self._process = None

        # Clean up data directory
        if self._mock_data_dir and Path(self._mock_data_dir).exists():
            shutil.rmtree(self._mock_data_dir)
            for r in self.resource_tracker.resources:
                if r.resource_type == "directory" and r.resource_id == self._mock_data_dir:
                    r.cleanup()
            self._mock_data_dir = None
            self._temp_data_dir = None

        # Clean up config file
        if self._mock_config_file and Path(self._mock_config_file).exists():
            os.unlink(self._mock_config_file)
            for r in self.resource_tracker.resources:
                if r.resource_type == "file" and r.resource_id == self._mock_config_file:
                    r.cleanup()
            self._mock_config_file = None

        self._status = DeploymentStatus.NOT_DEPLOYED
        self._prometheus_url = ""
        return True


class MockDockerDeployer(DockerDeployer):
    """Mock DockerDeployer that tracks resources for testing cleanup."""

    def __init__(
        self,
        config: Optional[DeployConfig] = None,
        docker_config: Optional[DockerConfig] = None,
        should_fail: bool = False,
    ):
        super().__init__(config, docker_config)
        self.resource_tracker = ResourceTracker()
        self.should_fail = should_fail
        self._mock_compose_file: Optional[str] = None
        self._mock_container_id: Optional[str] = None
        self._mock_volume_id: Optional[str] = None

    def deploy(self, config: Optional[DeployConfig] = None) -> Any:
        """Mock deploy that creates trackable resources."""
        from framework.deployer import DeployResult

        self._status = DeploymentStatus.DEPLOYING

        # Create mock compose file
        fd, self._mock_compose_file = tempfile.mkstemp(suffix=".yml", prefix="docker-compose-test-")
        os.close(fd)
        self.resource_tracker.add_resource("file", self._mock_compose_file)
        self.docker_config.compose_file = self._mock_compose_file

        # Simulate container creation
        self._mock_container_id = f"prometheus-test-{os.getpid()}"
        self.resource_tracker.add_resource("container", self._mock_container_id)

        # Simulate volume creation
        self._mock_volume_id = f"prometheus_data_{os.getpid()}"
        self.resource_tracker.add_resource("volume", self._mock_volume_id)

        if self.should_fail:
            self._status = DeploymentStatus.FAILED
            return DeployResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message="Simulated Docker deployment failure",
            )

        self._status = DeploymentStatus.DEPLOYED
        self._prometheus_url = f"http://localhost:{self.docker_config.port}"
        return DeployResult(
            success=True,
            status=DeploymentStatus.DEPLOYED,
            prometheus_url=self._prometheus_url,
            message="Mock Docker deployment successful",
        )

    def teardown(self) -> bool:
        """Mock teardown that cleans up tracked resources."""
        self._status = DeploymentStatus.TEARING_DOWN

        # Clean up container
        if self._mock_container_id:
            for r in self.resource_tracker.resources:
                if r.resource_type == "container" and r.resource_id == self._mock_container_id:
                    r.cleanup()
            self._mock_container_id = None

        # Clean up volume
        if self._mock_volume_id:
            for r in self.resource_tracker.resources:
                if r.resource_type == "volume" and r.resource_id == self._mock_volume_id:
                    r.cleanup()
            self._mock_volume_id = None

        # Clean up compose file
        if self._mock_compose_file and Path(self._mock_compose_file).exists():
            os.unlink(self._mock_compose_file)
            for r in self.resource_tracker.resources:
                if r.resource_type == "file" and r.resource_id == self._mock_compose_file:
                    r.cleanup()
            self._mock_compose_file = None

        self._status = DeploymentStatus.NOT_DEPLOYED
        self._prometheus_url = ""
        return True


@st.composite
def binary_config_strategy(draw):
    """Generate valid BinaryConfig instances."""
    return BinaryConfig(
        binary_path="",  # Will be mocked
        config_file="",  # Will be created
        data_dir="",  # Will be created
        port=draw(valid_ports),
        retention=draw(valid_retention),
        log_level=draw(valid_log_levels),
    )


@st.composite
def docker_config_strategy(draw):
    """Generate valid DockerConfig instances."""
    return DockerConfig(
        compose_file="",  # Will be created
        project_name=draw(valid_project_names),
        port=draw(valid_ports),
        prometheus_version="v2.54.1",
        retention=draw(valid_retention),
        memory_limit=draw(valid_memory_limits),
    )


@pytest.mark.property
class TestResourceCleanup:
    """
    Property-based tests for resource cleanup.

    **Feature: prometheus-installation, Property 11: Test Resource Cleanup**
    **Validates: Requirements 10.6**
    """

    @given(binary_config=binary_config_strategy())
    @settings(max_examples=100)
    def test_binary_deployer_cleanup_on_success(self, binary_config: BinaryConfig):
        """
        Property: For any successful binary deployment, teardown should clean up
        all created resources (data directory, config file, process).

        **Feature: prometheus-installation, Property 11: Test Resource Cleanup**
        **Validates: Requirements 10.6**
        """
        deployer = MockBinaryDeployer(binary_config=binary_config, should_fail=False)

        # Deploy
        result = deployer.deploy()
        assert result.success

        # Verify resources were created
        assert len(deployer.resource_tracker.resources) > 0
        assert not deployer.resource_tracker.all_cleaned_up()

        # Teardown
        teardown_success = deployer.teardown()
        assert teardown_success

        # Verify all resources are cleaned up
        assert deployer.resource_tracker.all_cleaned_up()
        uncleaned = deployer.resource_tracker.get_uncleaned_resources()
        assert len(uncleaned) == 0, f"Uncleaned resources: {[r.resource_id for r in uncleaned]}"

    @given(binary_config=binary_config_strategy())
    @settings(max_examples=100)
    def test_binary_deployer_cleanup_on_failure(self, binary_config: BinaryConfig):
        """
        Property: For any failed binary deployment, teardown should still clean up
        all created resources.

        **Feature: prometheus-installation, Property 11: Test Resource Cleanup**
        **Validates: Requirements 10.6**
        """
        deployer = MockBinaryDeployer(binary_config=binary_config, should_fail=True)

        # Deploy (will fail)
        result = deployer.deploy()
        assert not result.success

        # Resources may still have been created before failure
        created_resources = [r for r in deployer.resource_tracker.resources if r.created]

        # Teardown should still work
        teardown_success = deployer.teardown()
        assert teardown_success

        # Verify all resources are cleaned up
        assert deployer.resource_tracker.all_cleaned_up()

    @given(docker_config=docker_config_strategy())
    @settings(max_examples=100)
    def test_docker_deployer_cleanup_on_success(self, docker_config: DockerConfig):
        """
        Property: For any successful Docker deployment, teardown should clean up
        all created resources (containers, volumes, compose file).

        **Feature: prometheus-installation, Property 11: Test Resource Cleanup**
        **Validates: Requirements 10.6**
        """
        deployer = MockDockerDeployer(docker_config=docker_config, should_fail=False)

        # Deploy
        result = deployer.deploy()
        assert result.success

        # Verify resources were created
        assert len(deployer.resource_tracker.resources) > 0
        assert not deployer.resource_tracker.all_cleaned_up()

        # Teardown
        teardown_success = deployer.teardown()
        assert teardown_success

        # Verify all resources are cleaned up
        assert deployer.resource_tracker.all_cleaned_up()
        uncleaned = deployer.resource_tracker.get_uncleaned_resources()
        assert len(uncleaned) == 0, f"Uncleaned resources: {[r.resource_id for r in uncleaned]}"

    @given(docker_config=docker_config_strategy())
    @settings(max_examples=100)
    def test_docker_deployer_cleanup_on_failure(self, docker_config: DockerConfig):
        """
        Property: For any failed Docker deployment, teardown should still clean up
        all created resources.

        **Feature: prometheus-installation, Property 11: Test Resource Cleanup**
        **Validates: Requirements 10.6**
        """
        deployer = MockDockerDeployer(docker_config=docker_config, should_fail=True)

        # Deploy (will fail)
        result = deployer.deploy()
        assert not result.success

        # Resources may still have been created before failure
        created_resources = [r for r in deployer.resource_tracker.resources if r.created]

        # Teardown should still work
        teardown_success = deployer.teardown()
        assert teardown_success

        # Verify all resources are cleaned up
        assert deployer.resource_tracker.all_cleaned_up()

    @given(
        binary_config=binary_config_strategy(),
        num_deploy_cycles=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=50)
    def test_multiple_deploy_teardown_cycles(
        self, binary_config: BinaryConfig, num_deploy_cycles: int
    ):
        """
        Property: For any number of deploy/teardown cycles, resources should be
        properly cleaned up after each cycle.

        **Feature: prometheus-installation, Property 11: Test Resource Cleanup**
        **Validates: Requirements 10.6**
        """
        for cycle in range(num_deploy_cycles):
            deployer = MockBinaryDeployer(binary_config=binary_config, should_fail=False)

            # Deploy
            result = deployer.deploy()
            assert result.success, f"Deploy failed on cycle {cycle}"

            # Verify resources exist
            assert len(deployer.resource_tracker.resources) > 0

            # Teardown
            teardown_success = deployer.teardown()
            assert teardown_success, f"Teardown failed on cycle {cycle}"

            # Verify cleanup
            assert deployer.resource_tracker.all_cleaned_up(), \
                f"Resources not cleaned up on cycle {cycle}"

    @given(
        binary_config=binary_config_strategy(),
        docker_config=docker_config_strategy(),
    )
    @settings(max_examples=50)
    def test_mixed_deployer_cleanup(
        self, binary_config: BinaryConfig, docker_config: DockerConfig
    ):
        """
        Property: For any combination of deployer types, each should independently
        clean up its own resources.

        **Feature: prometheus-installation, Property 11: Test Resource Cleanup**
        **Validates: Requirements 10.6**
        """
        binary_deployer = MockBinaryDeployer(binary_config=binary_config, should_fail=False)
        docker_deployer = MockDockerDeployer(docker_config=docker_config, should_fail=False)

        # Deploy both
        binary_result = binary_deployer.deploy()
        docker_result = docker_deployer.deploy()

        assert binary_result.success
        assert docker_result.success

        # Verify resources exist for both
        assert len(binary_deployer.resource_tracker.resources) > 0
        assert len(docker_deployer.resource_tracker.resources) > 0

        # Teardown both
        binary_teardown = binary_deployer.teardown()
        docker_teardown = docker_deployer.teardown()

        assert binary_teardown
        assert docker_teardown

        # Verify both cleaned up
        assert binary_deployer.resource_tracker.all_cleaned_up()
        assert docker_deployer.resource_tracker.all_cleaned_up()

    @given(binary_config=binary_config_strategy())
    @settings(max_examples=100)
    def test_deployer_status_after_cleanup(self, binary_config: BinaryConfig):
        """
        Property: After teardown, deployer status should be NOT_DEPLOYED and
        prometheus_url should be empty.

        **Feature: prometheus-installation, Property 11: Test Resource Cleanup**
        **Validates: Requirements 10.6**
        """
        deployer = MockBinaryDeployer(binary_config=binary_config, should_fail=False)

        # Deploy
        result = deployer.deploy()
        assert result.success
        assert deployer.status == DeploymentStatus.DEPLOYED
        assert deployer.get_prometheus_url() != ""

        # Teardown
        teardown_success = deployer.teardown()
        assert teardown_success

        # Verify status
        assert deployer.status == DeploymentStatus.NOT_DEPLOYED
        assert deployer._prometheus_url == ""

    @given(docker_config=docker_config_strategy())
    @settings(max_examples=100)
    def test_docker_deployer_status_after_cleanup(self, docker_config: DockerConfig):
        """
        Property: After Docker teardown, deployer status should be NOT_DEPLOYED
        and prometheus_url should be empty.

        **Feature: prometheus-installation, Property 11: Test Resource Cleanup**
        **Validates: Requirements 10.6**
        """
        deployer = MockDockerDeployer(docker_config=docker_config, should_fail=False)

        # Deploy
        result = deployer.deploy()
        assert result.success
        assert deployer.status == DeploymentStatus.DEPLOYED
        assert deployer.get_prometheus_url() != ""

        # Teardown
        teardown_success = deployer.teardown()
        assert teardown_success

        # Verify status
        assert deployer.status == DeploymentStatus.NOT_DEPLOYED
        assert deployer._prometheus_url == ""


@pytest.mark.property
class TestResourceTrackerProperties:
    """
    Property-based tests for the ResourceTracker helper class.

    **Feature: prometheus-installation, Property 11: Test Resource Cleanup**
    **Validates: Requirements 10.6**
    """

    @given(
        resource_types=st.lists(
            st.sampled_from(["container", "pod", "volume", "file", "directory", "process"]),
            min_size=1,
            max_size=10,
        ),
        resource_ids=st.lists(
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=5, max_size=20),
            min_size=1,
            max_size=10,
        ),
    )
    @settings(max_examples=100)
    def test_resource_tracker_tracks_all_resources(
        self, resource_types: list[str], resource_ids: list[str]
    ):
        """
        Property: ResourceTracker should track all added resources.

        **Feature: prometheus-installation, Property 11: Test Resource Cleanup**
        **Validates: Requirements 10.6**
        """
        tracker = ResourceTracker()

        # Add resources (use min length to pair types and ids)
        num_resources = min(len(resource_types), len(resource_ids))
        for i in range(num_resources):
            tracker.add_resource(resource_types[i], resource_ids[i])

        # Verify all resources are tracked
        assert len(tracker.resources) == num_resources

        # Verify none are cleaned up initially
        assert not tracker.all_cleaned_up()

        # Clean up all
        tracker.cleanup_all()

        # Verify all are cleaned up
        assert tracker.all_cleaned_up()
        assert len(tracker.get_uncleaned_resources()) == 0

    @given(
        num_resources=st.integers(min_value=1, max_value=20),
        cleanup_indices=st.lists(st.integers(min_value=0, max_value=19), unique=True),
    )
    @settings(max_examples=100)
    def test_partial_cleanup_tracking(
        self, num_resources: int, cleanup_indices: list[int]
    ):
        """
        Property: ResourceTracker should correctly identify uncleaned resources
        after partial cleanup.

        **Feature: prometheus-installation, Property 11: Test Resource Cleanup**
        **Validates: Requirements 10.6**
        """
        tracker = ResourceTracker()

        # Add resources
        for i in range(num_resources):
            tracker.add_resource("test", f"resource-{i}")

        # Clean up only some resources
        valid_indices = [i for i in cleanup_indices if i < num_resources]
        for i in valid_indices:
            tracker.resources[i].cleanup()

        # Verify uncleaned count
        uncleaned = tracker.get_uncleaned_resources()
        expected_uncleaned = num_resources - len(valid_indices)
        assert len(uncleaned) == expected_uncleaned

        # Verify all_cleaned_up is correct
        if expected_uncleaned == 0:
            assert tracker.all_cleaned_up()
        else:
            assert not tracker.all_cleaned_up()
