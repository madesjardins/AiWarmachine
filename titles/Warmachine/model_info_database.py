#
# This file is part of the AiWarmachine distribution (https://github.com/madesjardins/AiWarmachine).
# Copyright (c) 2023-2024 Marc-Antoine Desjardins.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
"""Model info database contains information about models and units."""

import os
import json
import copy
from enum import StrEnum, EnumMeta
import shutil
from typing import Self, List, Dict
from dataclasses import dataclass, field, asdict

from . import constants
from importlib import reload
reload(constants)


class MetaEnum(EnumMeta):
    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        return True


class ModelInfoType(StrEnum, metaclass=MetaEnum):
    MODEL = "M"
    UNIT = "U"


class ModelInfoAttr(StrEnum, metaclass=MetaEnum):
    NAME = "name"
    INFO_TYPE = "ityp"
    SHORT_NAME = "snm"
    VOCAL_NAMES = "vns"
    BASE_SIZE = "bsz"
    COST = "cost"
    FA = "fa"
    TYPES = "typs"
    SPD = "spd"
    AAT = "aat"
    MAT = "mat"
    RAT = "rat"
    DEF = "def_"
    ARM = "arm"
    ARC = "arc"
    CTRL = "ctrl"
    FURY = "fury"
    THR = "thr"
    ADVANTAGES = "advs"
    RESISTANCES = "res"
    SPECIAL_RULES = "srls"
    FEAT = "feat"
    HEALTH = "hp"
    SPELLS = "spls"
    RACK_SLOTS = "slts"
    WEAPONS = "wpns"
    HARDPOINTS = "hrds"
    TROOPERS = "trps"


class ModelInfoModelTypeBasic(StrEnum, metaclass=MetaEnum):
    GRUNT = "Grunt"
    SOLO = "Solo"
    WARCASTER = "Warcaster"
    WARLOCK = "Warlock"
    WARJACK = "Warjack"
    WARBEAST = "Warbeast"


@dataclass
class ModelInfo:
    """"""
    ityp: ModelInfoType
    name: str = ""
    snm: str = ""
    vns: List[str] = field(default_factory=list)
    bsz: int = 30
    cost: int = -1
    fa: int = -1
    typs: List[str] = field(default_factory=list)
    spd: int = -1
    aat: int = -1
    mat: int = -1
    rat: int = -1
    def_: int = -1
    arm: int = -1
    ctrl: int = -1
    fury: int = -1
    thr: int = -1
    advs: List[str] = field(default_factory=list)
    res: List[str] = field(default_factory=list)
    srls: List[str] = field(default_factory=list)
    feat: str = ""
    hp: Dict[str, str] = field(default_factory=dict)
    spls: List[str] = field(default_factory=list)
    slts: List[str] = field(default_factory=list)
    wpns: List[str] = field(default_factory=list)
    hrds: List[str] = field(default_factory=list)
    trps: List[str] = field(default_factory=list)

    @staticmethod
    def from_dict(info: dict) -> Self:
        """"""
        model_info = ModelInfo(**copy.deepcopy(info))
        return model_info

    def duplicate(self) -> Self:
        """"""
        new_obj = ModelInfo(**self.as_dict())
        new_obj.name += " (copy)"
        return new_obj

    def update(self, info: dict) -> None:
        """"""
        for attr, value in copy.deepcopy(info).items():
            if hasattr(self, attr):
                setattr(self, attr, value)

    def as_dict(self) -> dict:
        """"""
        return copy.deepcopy(asdict(self))


class ModelInfoDatabase(object):
    """Model info database class."""

    @staticmethod
    def create_new(name):
        """"""
        file_path = f"{constants.MODEL_INFO_DATABASE_DIR_PATH}/{name}.json"
        if os.path.exists(file_path):
            raise ValueError(f"Models database '{name}' already exists.")

        if not os.path.exists(constants.MODEL_INFO_DATABASE_DIR_PATH):
            os.makedirs(constants.MODEL_INFO_DATABASE_DIR_PATH)
        with open(file_path, 'w') as fid:
            fid.write(json.dumps({ModelInfoType.MODEL: {}, ModelInfoType.UNIT: {}}))

        return ModelInfoDatabase(file_path)

    @staticmethod
    def duplicate(orig_name, dup_name):
        """"""
        orig_file_path = f"{constants.MODEL_INFO_DATABASE_DIR_PATH}/{orig_name}.json"
        if not os.path.exists(orig_file_path):
            raise ValueError(f"Models database '{orig_name}' does not exist.")

        dup_file_path = f"{constants.MODEL_INFO_DATABASE_DIR_PATH}/{dup_name}.json"
        if os.path.exists(dup_file_path):
            raise ValueError(f"Models database '{dup_name}' already exists.")

        shutil.copy2(orig_file_path, dup_file_path)

        return ModelInfoDatabase(dup_file_path)

    def __init__(self, file_path):
        """"""
        super().__init__()
        self.file_path = file_path
        self._load()

    def _load(self):
        """Load the current database"""
        with open(self.file_path, "r") as fid:
            json_data = json.loads(fid.read())

        self.clear()
        for model_info_type in json_data.keys():
            for model_name, model_info_dict in json_data[model_info_type].items():
                self._data[model_info_type][model_name] = ModelInfo.from_dict(info=model_info_dict)

    def revert(self):
        """"""
        self._load()

    def clear(self):
        """"""
        self._data = {ModelInfoType.MODEL: {}, ModelInfoType.UNIT: {}}

    def save(self):
        """"""
        json_data = {ModelInfoType.MODEL: {}, ModelInfoType.UNIT: {}}
        for model_info_type in self._data.keys():
            for model_name, model_info in self._data[model_info_type].items():
                json_data[model_info_type][model_name] = model_info.as_dict()

        with open(self.file_path, "w") as fid:
            fid.write(json.dumps(json_data))

    def update(self, model_info: ModelInfo):
        """"""
        self._data[model_info.ityp][model_info.name] = model_info

    def remove(self, name, info_type=ModelInfoType.MODEL):
        """"""
        try:
            del self._data[info_type][name]
        except KeyError:
            return False
        return True

    def remove_multi(self, names_list: list[str], info_type=ModelInfoType.MODEL) -> None:
        """"""
        for name in names_list:
            self.remove(name, info_type=info_type)

    def get_names(self, info_type=ModelInfoType.MODEL):
        """"""
        return copy.deepcopy(sorted(_name for _name in self._data[info_type].keys()))

    def get(self, name, info_type=ModelInfoType.MODEL) -> ModelInfo:
        """"""
        return self._data[info_type].get(name)

    def exists(self, name: str, info_type: ModelInfoType) -> bool:
        """"""
        return name in self._data[info_type]
