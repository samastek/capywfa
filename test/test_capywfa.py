# SPDX-FileCopyrightText: 2026 Siemens
# SPDX-License-Identifier: MIT

import os
import tempfile

from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component, ComponentType
from packageurl import PackageURL

from capywfa.capywfa import pass3_download_sources, MapResult
from capywfa.cdx_support import set_cdx, get_cdx


def create_test_component(name, version, map_result=None, source_check=None):
    """Helper function to create a test component with CDX properties."""
    component = Component(
        name=name,
        type=ComponentType.LIBRARY,
        version=version,
        purl=PackageURL("deb", "debian", name, version, {"arch": "source"})
    )
    if map_result is not None:
        set_cdx(component, "MapResult", map_result)
    if source_check is not None:
        set_cdx(component, "Sw360SourceFileCheck", source_check)
    return component


def test_pass3_download_sources_no_pkg_dir():
    """Test that pass3_download_sources works when no package directory is provided."""
    bom = Bom(components=[
        create_test_component("testpkg", "1.0-1", MapResult.NO_MATCH)
    ])
    result = pass3_download_sources(bom, None)
    assert result == bom
    # Should not set SourceFileComment when pkg_dir is None
    assert not get_cdx(bom.components[0], "SourceFileComment")


def test_pass3_download_sources_local_package_found():
    """Test that local packages are detected and marked as available."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "testpkg_1.0-1.dsc")
        with open(test_file, "w") as f:
            f.write("test")

        bom = Bom(components=[
            create_test_component("testpkg", "1.0-1", MapResult.NO_MATCH)
        ])

        result = pass3_download_sources(bom, tmpdir)

        assert get_cdx(result.components[0], "SourceFileComment") == "sources locally available"


def test_pass3_download_sources_local_package_not_found():
    """Test that packages are not marked when local files don't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bom = Bom(components=[
            create_test_component("testpkg", "1.0-1", MapResult.NO_MATCH)
        ])

        result = pass3_download_sources(bom, tmpdir)

        # Should not set SourceFileComment when no matching file found
        assert not get_cdx(result.components[0], "SourceFileComment")


def test_pass3_download_sources_version_with_epoch():
    """Test that version with epoch is handled correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "testpkg_1.0-1.dsc")
        with open(test_file, "w") as f:
            f.write("test")

        # Component has epoch in version
        bom = Bom(components=[
            create_test_component("testpkg", "2:1.0-1", MapResult.NO_MATCH)
        ])

        result = pass3_download_sources(bom, tmpdir)
        assert get_cdx(result.components[0], "SourceFileComment") == "sources locally available"
