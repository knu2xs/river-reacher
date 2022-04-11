from datetime import datetime
from functools import lru_cache
import json
from pathlib import Path
import re
from typing import Iterable, List, Optional, Union
from warnings import warn

from arcgis.geometry import Geometry, Polyline
from requests import get

from ._utils import html_to_markdown, get_if_match_length


class Reach(object):

    _aw_id: str = None
    _aw_dict: str = None

    def __init__(self, aw_id:Optional[str] = None) -> None:
        self.aw_id = aw_id

    @classmethod
    def from_aw_json(cls, path:Path) -> object:
        """
        Create and load the data directly from a cached JSON file.

        .. note::
            Mostly useful for development and debugging.

        Args:
            path: Path to where file is saved locally.

        Returns:
            Instantiated Reach object.
        """
        # create an instance of the class
        reach = cls()

        # load the file
        with open(path) as f:
            reach._aw_dict = json.load(f)

        # set the id
        reach.aw_id = reach._aw_dict['CContainerViewJSON_view']['CRiverMainGadgetJSON_main']['info']['id']

        return reach

    @property
    def aw_id(self) -> str:
        """
        American Whitewater unique identifier for the reach (if applicable).
        """
        return self._aw_id

    @aw_id.setter
    def aw_id(self, in_id=Union[int, str]) -> str:
        # make sure is formatted as a string
        if isinstance(in_id, int):
            self._aw_id = str(in_id)
        else:
            self._aw_id = in_id
        return in_id

    @property
    def aw_url(self):
        """
        If there a corresponding reach exists in AW, this is the link.
        """
        if self.aw_id is not None:
            url = f"https://www.americanwhitewater.org/content/River/view/river-detail/{self.aw_id}"
        else:
            url = None
        return url
    
    @property
    @lru_cache
    def aw_dict(self) -> dict:
        """
        Retrieve (if necessary) and return the dictionary of raw reach data from American Whitewater.
        """
        # if not set, retrieve from AW
        if self._aw_dict is None:

            # create the string to retrieve the data from
            url = f"https://www.americanwhitewater.org/content/River/detail/id/{self.aw_id}/.json"

            # retrieve the data from AW - retrying to handle dropped requests
            attempts = 0
            status_code = 0

            while attempts < 10 and status_code != 200:
                res = get(url)
                if res.status_code == 200 and len(res.content):
                    aw_json = res.json()
                elif res.status_code == 200 and not len(res.content):
                    aw_json = None
                elif res.status_code == 500:
                    aw_json = None
                else:
                    attempts += 1

            # if cannot retrieve any data, let somebody know
            if aw_json is None:
                warn(f"Cannot download data for reach_id {self.aw_id}")

        # if set, just return
        else:
            aw_json = self._aw_dict

        return aw_json

    def get_aw_property(self, key_and_index_list=List[Union[str, int]]) -> Union[str, dict]:
        """
        Retrieve deep nested properties from within the American Whitewater JSON.

        Args:
            key_and_index_list: Keys and indexes to navigate down into to retrieve values.

        Returns:
            Value at location requested in JSON.
        """
        # start by ensuring the AW ID is defined
        assert self._aw_id is not None, "Must define an AW ID to retrieve properties."

        # if the key and index list is just a single value, convert to list
        if isinstance(key_and_index_list, (str, int)):
            key_and_index_list = list(key_and_index_list)

        # initialize the return value to the entire AW dict
        ret_val = self.aw_dict

        # walk through the list to get the value needed
        for key_idx in key_and_index_list:

            # check to ensure a key exists and if it does, pull out the value
            if isinstance(key_idx, str):
                if key_idx not in ret_val.keys():
                    ret_val = None

            # if an index, ensure the list has length
            elif isinstance(key_idx, int):
                if len(ret_val[key_idx]) == 0:
                    ret_val = None

            # pull out the value if not none
            if ret_val is not None:
                ret_val = ret_val[key_idx]

            # but if it is none, break out
            else:
                break

        # if a string, do a little cleanup of leading and trailing spaces
        if isinstance(ret_val, str):
            ret_val = ret_val.strip()

        return ret_val

    @property
    @lru_cache
    def geometry(self) -> Polyline:
        """
        Line geometry of the reach.
        """
        # extract the coordinates from the AW JSON
        coord_list = self.get_aw_property(['CContainerViewJSON_view', 'CRiverMainGadgetJSON_main', 'info', 'geom',
                                           'coordinates'])

        # convert the coordinates to Esri JSON
        geom = Polyline({"paths" : [coord_list],"spatialReference" : {"wkid" : 4326}})

        return geom

    @property
    @lru_cache
    def description(self) -> str:
        """Reach description in Markdown."""
        # pluck the description out of the markdown
        raw_desc = self.get_aw_property(['CContainerViewJSON_view', 'CRiverMainGadgetJSON_main', 'info',
                                         'description'])

        # convert the html to markdown
        md_desc = html_to_markdown(raw_desc)

        return md_desc

    @property
    @lru_cache
    def abstract(self) -> str:
        """Reach abstract."""
        # try to pull out of AW JSON
        abstract = self.get_aw_property(['CContainerViewJSON_view', 'CRiverMainGadgetJSON_main', 'info',
                                         'abstract'])

        # if one is not provided, create one from the first 500 characters of the description
        if abstract is None:

            # remove all line returns, html tags, trim to 500 characters, and trim to last space to ensure full word
            abstract = self.description
            abstract = abstract.replace('\\', '').replace('/n', '')[:500]
            abstract = abstract[:abstract.rfind(' ')]
            abstract = abstract + '...'

        return abstract

    @property
    @lru_cache
    def difficulty(self) -> str:
        """Full string representation of difficulty."""
        diff = self.get_aw_property(['CContainerViewJSON_view', 'CRiverMainGadgetJSON_main', 'info',
                                     'class'])
        return diff

    @property
    @lru_cache
    def _difficulty_match(self) -> re.Match:
        match = re.match(
            '^([I|IV|V|VI|5\.\d]{1,3}(?=-))?-?([I|IV|V|VI|5\.\d]{1,3}[+|-]?)\(?([I|IV|V|VI|5\.\d]{0,3}[+|-]?)',
            self.difficulty
        )
        return match

    @property
    @lru_cache
    def difficulty_minimum(self) -> str:
        return get_if_match_length(self._difficulty_match.group(1))

    @property
    @lru_cache
    def difficulty_maximum(self) -> str:
        return get_if_match_length(self._difficulty_match.group(2))

    @property
    @lru_cache
    def difficulty_outlier(self) -> str:
        return get_if_match_length(self._difficulty_match.group(3))

    @property
    @lru_cache
    def aw_update_timestamp(self):
        dt_str = self.get_aw_property(['CContainerViewJSON_view', 'CRiverMainGadgetJSON_main', 'info', 'edited'])
        dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        return dt

    @property
    @lru_cache()
    def difficulty_filter(self):
        lookup_dict = {
            'I':    1.0,
            'I+':   1.1,
            'II-':  1.2,
            'II':   2.0,
            'II+':  2.1,
            'III-': 2.2,
            'III':  3.0,
            'III+': 3.1,
            'IV-':  3.2,
            'IV':   4.0,
            'IV+':  4.1,
            'V-':   4.3,
            'V':    5.0,
            'V+':   5.1
        }
        return lookup_dict[self.difficulty_maximum]
