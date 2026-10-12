"""Tests for parsing device registration responses."""

import pytest

from stkclient.model import DeviceInfo


def test_xml_entities_rejected() -> None:
    """Reject XML entity expansion before processing device credentials."""
    xml = b'<!DOCTYPE response [<!ENTITY secret "expanded">]><response>&secret;</response>'
    with pytest.raises(ValueError, match="EntitiesForbidden"):
        DeviceInfo.from_xml(xml)
