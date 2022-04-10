from functools import lru_cache
import json
from pathlib import Path
from typing import Iterable, List, Optional, Union
from warnings import warn

from requests import get


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

        return reach

    @property
    def aw_id(self) -> str:
        """
        American Whitewater unique identifier for the reach (if applicable).
        """
        return self._aw_id

    @property.setter
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
    

    @lru_cache
    @property
    def aw_dict(self) -> dict:
        """
        Retrieve (if necessary) and return the dictionary of raw reach data from American Whitewater.
        """
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

        return aw_json


    @property.setter
    def aw_dict(self, input_dictionary) -> dict:
        self.aw_dict = input_dictionary
        return self.aw_dict


    def get_aw_property(self, key_and_index_list=List[str, int]) -> Union[str, dict]:
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
        if not isinstance(key_and_index_list, Iterable):
            key_and_index_list = list(key_and_index_list)

        # initialize the return value to the entire AW dict
        ret_val = self.aw_dict

        # walk through the list to get the value needed
        for key_idx in key_and_index_list:
            ret_val = ret_val[key_idx]

        return ret_val