"""
This is a stubbed out test file designed to be used with PyTest, but can 
easily be modified to support any testing framework.
"""

from datetime import datetime
from pathlib import Path

from arcgis.geometry import Polyline
import pytest
from river_reacher import Reach

# get paths to useful resources - notably where the src directory is
self_pth = Path(__file__)
dir_test = self_pth.parent
dir_prj = dir_test.parent

# location of data to test against
dir_test_data = dir_test/'test_data'
aw_json_194_pth = dir_test_data/'aw_194.json'


@pytest.fixture(scope='session')
def reach_194():
    reach = Reach.from_aw_json(aw_json_194_pth)
    return reach


def test_reach_from_aw_json():
    reach = Reach.from_aw_json(aw_json_194_pth)
    assert isinstance(reach, Reach)


def test_reach_geometry(reach_194):
    geom = reach_194.geometry
    assert isinstance(geom, Polyline)
    assert geom.spatial_reference['wkid'] == 4326


def test_reach_description(reach_194):
    desc = reach_194.description
    assert isinstance(desc, str)
    assert len(desc) > 0
    assert "<" not in desc
    assert ">" not in desc


def test_reach_abstract(reach_194):
    abst = reach_194.abstract
    assert isinstance(abst, str)
    assert 0 < len(abst) < 501


def test_difficulty(reach_194):
    diff = reach_194.difficulty
    assert isinstance(diff, str)
    assert diff == 'V+'


def test_difficulty_minimum(reach_194):
    diff_min = reach_194.difficulty_minimum
    assert diff_min is None


def test_difficulty_maximum(reach_194):
    diff_max = reach_194.difficulty_maximum
    assert diff_max == 'V+'


def test_difficulty_outlier(reach_194):
    diff_out = reach_194.difficulty_outlier
    assert diff_out is None


def test_aw_update_timestamp(reach_194):
    ts = reach_194.aw_update_timestamp
    assert isinstance(ts, datetime)
