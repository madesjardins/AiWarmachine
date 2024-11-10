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


class ModelInfoCategory(StrEnum, metaclass=MetaEnum):
    INDEPENDENT = "I"
    UNIT = "U"


class ModelInfoAttr(StrEnum, metaclass=MetaEnum):
    INFO_CATEGORY = "icat"
    NAME = "name"
    SHORT_NAME = "snm"
    VOCAL_NAMES = "vns"
    FACTION = "fact"
    BASIC_TYPE = "btyp"
    BASE_SIZE = "bsz"
    COST = "cost"
    FA = "fa"
    IS_CHARACTER = "char"
    KEYWORDS = "kws"
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


class ModelInfoBasicType(StrEnum, metaclass=MetaEnum):
    WARCASTER = "Warcaster"
    WARLOCK = "Warlock"
    INFERNAL_MASTER = "Infernal Master"
    WARJACK = "Warjack"
    WARBEAST = "Warbeast"
    MONSTROSITY = "Monstrosity"
    HORROR = "Horror"
    BATTLE_ENGINE = "Battle Engine"
    STRUCTURE = "Structure"
    SOLO = "Solo"
    GRUNT = "Grunt"
    TROOPER = "Trooper"
    COMMAND_ATTACHMENT = "Command Attachment"
    WEAPON_ATTACHMENT = "Weapon Attachment"


@dataclass
class ModelInfo:
    """"""
    icat: ModelInfoCategory
    name: str = ""
    snm: str = ""
    fact: str = "Mercenaries"
    btyp: str = ModelInfoBasicType.SOLO.value
    vns: List[str] = field(default_factory=list)
    bsz: int = 30
    cost: int = -1
    fa: int = -1
    char: bool = False
    kws: str = ""
    spd: int = -1
    aat: int = -1
    mat: int = -1
    rat: int = -1
    def_: int = -1
    arm: int = -1
    arc: int = -1
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
            fid.write(json.dumps({ModelInfoCategory.INDEPENDENT: {}, ModelInfoCategory.UNIT: {}}))

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
        self._data = {ModelInfoCategory.INDEPENDENT: {}, ModelInfoCategory.UNIT: {}}

    def save(self):
        """"""
        json_data = {ModelInfoCategory.INDEPENDENT: {}, ModelInfoCategory.UNIT: {}}
        for model_info_type in self._data.keys():
            for model_name, model_info in self._data[model_info_type].items():
                json_data[model_info_type][model_name] = model_info.as_dict()

        with open(self.file_path, "w") as fid:
            fid.write(json.dumps(json_data))

    def update(self, model_info: ModelInfo):
        """"""
        self._data[model_info.icat][model_info.name] = model_info

    def remove(self, name, info_category=ModelInfoCategory.INDEPENDENT):
        """"""
        try:
            del self._data[info_category][name]
        except KeyError:
            return False
        return True

    def remove_multi(self, names_list: list[str], info_category=ModelInfoCategory.INDEPENDENT) -> None:
        """"""
        for name in names_list:
            self.remove(name, info_category=info_category)

    def get_names(self, info_category=ModelInfoCategory.INDEPENDENT):
        """"""
        return copy.deepcopy(sorted(_name for _name in self._data[info_category].keys()))

    def get(self, name, info_category=ModelInfoCategory.INDEPENDENT) -> ModelInfo:
        """"""
        return self._data[info_category].get(name)

    def exists(self, name: str, info_category: ModelInfoCategory) -> bool:
        """"""
        return name in self._data[info_category]
