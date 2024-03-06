# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation - Paul Golter
from __future__ import annotations

import inspect
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Union, Tuple, TypeVar
from pathlib import Path
import gazu
from .logger import LoggerFactory
from . import bkglobals
from . import prefs

logger = LoggerFactory.getLogger()

D = TypeVar("D", bound="BaseDataClass")


class Session:
    """
    Class that will be instanced to blender_kitsu addon preferences.
    It's used to authenticate user against backend.
    If instance gets deleted authentication will be lost.
    """

    def __init__(self, email: str = "", passwd: str = "", host: str = "") -> None:
        self._email = email
        self._passwd = passwd
        self._host = self.get_host_api_url(host)
        self._data: SessionData = SessionData()

        if self._host:
            gazu.client.set_host(self._host)

    def start(self) -> SessionData:
        # Clear all data.
        gazu.cache.disable()
        gazu.cache.clear_all()

        # Enable cache.
        gazu.cache.enable()

        if not self._is_host_up():
            raise gazu.exception.HostException

        # Login.
        self._login()

        return self._data

    def end(self) -> bool:
        if not self._data.login:
            logger.debug("Failed to log out. Session not started yet")
            return False

        self._data = SessionData(gazu.log_out())  # returns empty dict
        gazu.cache.clear_all()
        logger.info("Session ended")
        return True

    def _is_host_up(self) -> bool:
        if gazu.client.host_is_up():
            logger.debug("Host is up and running at: %s", self.host)
            return True
        else:
            logger.error("Failed to reach host at: %s", self.host)
            return False

    def _login(self) -> None:
        session_dict = gazu.log_in(self._email, self._passwd)
        self._data.update(session_dict)
        logger.info("Login was successful. Session started with user %s", self.email)

    def is_auth(self) -> bool:
        return self._data.login

    def set_credentials(self, email: str, passwd: str) -> None:
        self.email = email
        self.passwd = passwd

    def get_config(self) -> Dict[str, str]:
        return {
            "email": self.email,
            "passwd": self._passwd,
            "host": self.host,
        }  # TODO: save those in SessionData

    def set_config(self, config: Dict[str, str]) -> None:
        email = config.get("email", "")
        passwd = config.get("passwd", "")
        host = config.get("host", "")
        self.email = email
        self._passwd = passwd
        self.host = host

    def valid_config(self) -> bool:
        if "" in {self.email, self._passwd, self.host}:
            return False
        else:
            return True

    @classmethod
    def get_host_api_url(cls, url: str) -> str:
        if not url:
            return ""
        if url[-4:] == "/api":
            return url
        if url[-1] == "/":
            url = url[:-1]
        return url + "/api"

    @property
    def host(self) -> str:
        return self._host

    @host.setter
    def host(self, host: str) -> None:
        host_backup = self._host
        if host:
            self._host = self.get_host_api_url(host)
            gazu.client.set_host(self._host)
            if not gazu.client.host_is_valid():
                logger.error("Host is not valid: %s", host)
                self._host = host_backup
                gazu.client.set_host(self._host)

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, email: str) -> None:
        self._email = email

    @property
    def data(self) -> SessionData:
        return self._data

    def __del__(self) -> None:
        self.end()


class BaseDataClass:
    """
    Base class that gives us some useful methods we need on all other dataclasses.
    """

    @classmethod
    def from_dict(cls: type[D], env: Dict[str, Any]) -> D:
        """
        Initializes DataClass by dictionary. Only passes keys that exist in this
        classes parameters. This is useful to work around unexpected parameters.
        """
        # In general it is a good idea to use this function to initialize
        # DataClasses from Kitsu dictionaries with this function as the Kitsu
        # API is subject to change. With this we can avoid a Situation in which we
        # constantly have to synchronize the DataClass Parameters with the current state
        # of the Kitsu API.
        valid_key_values = {}

        # At least keep track of unexpected arguments and log them.
        unexpected_args: List[str] = []
        for k, v in env.items():
            if k not in inspect.signature(cls).parameters:
                unexpected_args.append(f"{k}:{type(v).__name__}={str(v)}")
                continue
            valid_key_values[k] = v

        # Log unexpected args.
        if unexpected_args:
            logger.debug(
                "%s received unexpected arguments: %s",
                cls.__name__,
                ", ".join(unexpected_args),
            )

        # Return final class with fitting parameters.
        return cls(**valid_key_values)


class Entity(BaseDataClass):
    """
    Base Class that defines methods every Entity type should have.
    """

    @classmethod
    def by_name(cls, name: str) -> Optional[Any]:
        raise NotImplementedError()

    @classmethod
    def by_id(cls, id: str) -> Any:
        raise NotImplementedError()


@dataclass
class SessionData(BaseDataClass):
    login: bool = False
    user: Dict[str, str] = field(default_factory=dict)
    ldap: bool = False
    access_token: str = ""
    refresh_token: str = ""

    def update(self, data_dict: Dict[str, Union[str, Dict[str, str]]]) -> None:
        for k, v in data_dict.items():
            setattr(self, k, v)


class ProjectList:
    """
    Class to get object oriented representation of backend productions data structure.
    """

    def __init__(self):
        self._projects: List[Project] = []
        self._init_projects()

    @property
    def names(self) -> List[str]:
        return [p.name for p in self._projects]

    @property
    def projects(self) -> List[Project]:
        return self._projects

    def _init_projects(self) -> None:
        for project in gazu.project.all_projects():
            self._projects.append(Project.from_dict(project))


@dataclass
class Project(Entity):
    """
    Class to get object oriented representation of backend project data structure.
    Can shortcut some functions from gazu api because active project is given through class instance.
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    """

    id: str = ""
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    code: Optional[str] = None
    description: Optional[str] = None
    shotgun_id: Optional[str] = None
    data: None = None
    has_avatar: bool = False
    fps: Optional[str] = None
    ratio: Optional[str] = None
    resolution: Optional[str] = None
    production_type: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    man_days: Optional[str] = None
    nb_episodes: int = 0  # Set in the Project settings (not counting actual Episodes)
    episode_span: int = 0
    project_status_id: str = ""
    type: str = ""
    project_status_name: str = ""
    file_tree: Dict[str, Any] = field(default_factory=dict)
    team: List[Any] = field(default_factory=list)
    asset_types: List[Any] = field(default_factory=list)
    task_types: List[Any] = field(default_factory=list)
    task_statuses: List[Any] = field(default_factory=list)

    @classmethod
    def by_name(cls, project_name: str) -> Optional[Project]:
        # Can return None if seq does not exist.
        project_dict = gazu.project.get_project_by_name(project_name)
        if project_dict:
            return cls.from_dict(project_dict)
        return None

    @classmethod
    def by_id(cls, project_id: str) -> Project:
        project_dict = gazu.project.get_project(project_id)
        return cls.from_dict(project_dict)

    # EPISODES
    # ---------------
    def get_episode(self, ep_id: str) -> Episode:
        return Episode.by_id(ep_id)

    def get_episodes_all(self) -> List[Episode]:
        episodes = [Episode.from_dict(s) for s in gazu.shot.all_episodes_for_project(asdict(self))]
        return sorted(episodes, key=lambda x: x.name)

    # SEQUENCES
    # ---------------

    def get_sequence(self, seq_id: str) -> Sequence:
        return Sequence.by_id(seq_id)

    def get_sequence_by_name(
        self, seq_name: str, episode: Union[str, Dict[str, Any], None] = None
    ) -> Optional[Sequence]:
        return Sequence.by_name(self, seq_name, episode=episode)

    def get_sequences_all(self) -> List[Sequence]:
        sequences = [
            Sequence.from_dict(s) for s in gazu.shot.all_sequences_for_project(asdict(self))
        ]
        return sorted(sequences, key=lambda x: x.name)

    def create_sequence(self, sequence_name: str, episode_id: Optional[str] = None) -> Sequence:
        # This function returns a seq dict even if seq already exists, it does not override.
        seq_dict = gazu.shot.new_sequence(asdict(self), sequence_name, episode=episode_id)
        return Sequence.from_dict(seq_dict)

    # SHOT
    # ---------------

    def get_shot(self, shot_id: str) -> Shot:
        return Shot.by_id(shot_id)

    def get_shots_all(self) -> List[Shot]:
        shots = [Shot.from_dict(s) for s in gazu.shot.all_shots_for_project(asdict(self))]
        return sorted(shots, key=lambda x: x.name)

    def get_shot_by_name(self, sequence: Sequence, name: str) -> Optional[Shot]:
        return Shot.by_name(sequence, name)

    def create_shot(
        self,
        sequence: Sequence,
        shot_name: str,
        nb_frames: Optional[int] = None,
        frame_in: Optional[int] = None,
        frame_out: Optional[int] = None,
        data: Dict[str, Any] = {},
    ) -> Shot:
        # This function returns a shot dict even if shot already exists, it does not override.
        shot_dict = gazu.shot.new_shot(
            asdict(self),
            asdict(sequence),
            shot_name,
            nb_frames,
            frame_in=frame_in,
            frame_out=frame_out,
            data=data,
        )
        return Shot.from_dict(shot_dict)

    def update_shot(self, shot: Shot) -> Dict[str, Any]:
        return gazu.shot.update_shot(asdict(shot))  # type: ignore

    # ASSET TYPES
    # ---------------

    def get_all_asset_types(self) -> List[AssetType]:
        assettypes = [
            AssetType.from_dict(at) for at in gazu.asset.all_asset_types_for_project(asdict(self))
        ]
        return sorted(assettypes, key=lambda x: x.name)

    def get_asset_type_by_name(self, asset_type_name: str) -> Optional[AssetType]:
        return AssetType.by_name(asset_type_name)

    # ASSETS
    # ---------------

    def get_all_assets(self) -> List[Asset]:
        assets = [Asset.from_dict(a) for a in gazu.asset.all_assets_for_project(asdict(self))]
        return sorted(assets, key=lambda x: x.name)

    def get_asset_by_name(self, asset_name: str) -> Optional[Asset]:
        return Asset.by_name(self, asset_name)

    def get_all_assets_for_type(self, assettype: AssetType) -> List[Asset]:
        assets = [
            Asset.from_dict(a)
            for a in gazu.asset.all_assets_for_project_and_type(asdict(self), asdict(assettype))
        ]
        return sorted(assets, key=lambda x: x.name)

    # TASKS
    # ---------------

    def __bool__(self) -> bool:
        return bool(self.id)

    # EDITS
    # ---------------
    def get_all_edits(self) -> List[Edit]:
        edits = [Edit.from_dict(t) for t in gazu.edit.all_edits_for_project(asdict(self))]
        return sorted(edits, key=lambda x: x.name)


@dataclass
class Episode(Entity):
    """
    Class to get object-oriented representation of backend episode data structure.
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    """

    id: str = ""
    name: str = ""
    description: Optional[str] = None

    @classmethod
    def by_name(cls, project: Project, ep_name: str) -> Optional[Episode]:
        # Can return None if ep does not exist.
        ep_dict = gazu.shot.get_episode_by_name(asdict(project), ep_name)
        if ep_dict:
            return cls.from_dict(ep_dict)
        return None

    @classmethod
    def by_id(cls, ep_id: str) -> Episode:
        ep_dict = gazu.shot.get_episode(ep_id)
        return cls.from_dict(ep_dict)

    def __bool__(self) -> bool:
        return bool(self.id)

    def get_all_asset(self) -> List[Asset]:
        assets = [Asset.from_dict(at) for at in gazu.asset.all_assets_for_episode(asdict(self))]
        return sorted(assets, key=lambda x: x.name)

    def get_sequences_all(self) -> List[Sequence]:
        sequences = [
            Sequence.from_dict(s) for s in gazu.shot.all_sequences_for_episode(asdict(self))
        ]
        return sorted(sequences, key=lambda x: x.name)


@dataclass
class Sequence(Entity):
    """
    Class to get object-oriented representation of backend sequence data structure.
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    """

    id: str = ""
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    code: Optional[str] = None
    description: Optional[str] = None
    shotgun_id: Optional[str] = None
    canceled: bool = False
    nb_frames: Optional[int] = None
    project_id: str = ""
    entity_type_id: str = ""
    parent_id: str = ""
    source_id: Optional[str] = None
    preview_file_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = field(default_factory=dict)
    type: str = ""
    project_name: str = ""

    @classmethod
    def by_name(
        cls,
        project: Project,
        seq_name: str,
        episode: Union[str, Dict[str, Any], None] = None,
    ) -> Optional[Sequence]:
        # Can return None if seq does not exist.
        seq_dict = gazu.shot.get_sequence_by_name(asdict(project), seq_name, episode=episode)
        if seq_dict:
            return cls.from_dict(seq_dict)
        return None

    @classmethod
    def by_id(cls, seq_id: str) -> Sequence:
        seq_dict = gazu.shot.get_sequence(seq_id)
        return cls.from_dict(seq_dict)

    def get_all_shots(self) -> List[Shot]:
        shots = [Shot.from_dict(shot) for shot in gazu.shot.all_shots_for_sequence(asdict(self))]
        return sorted(shots, key=lambda x: x.name)

    def get_all_task_types(self) -> List[TaskType]:
        return [TaskType.from_dict(t) for t in gazu.task.all_task_types_for_sequence(asdict(self))]

    def get_all_tasks(self) -> List[Task]:
        return [Task.from_dict(t) for t in gazu.task.all_tasks_for_sequence(asdict(self))]

    def update(self) -> Sequence:
        gazu.shot.update_sequence(asdict(self))
        return self

    def update_data(self, data: Dict[str, Any]) -> Sequence:
        gazu.shot.update_sequence_data(asdict(self), data=data)
        if not self.data:
            self.data = {}
        for key in data:
            self.data[key] = data[key]
        return self

    def __bool__(self) -> bool:
        return bool(self.id)


@dataclass
class AssetType(Entity):
    """
    Class to get object oriented representation of backend sequence data structure.
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    """

    id: str = ""
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    type: str = ""

    @classmethod
    def by_name(cls, asset_type_name: str) -> Optional[AssetType]:
        # Can return None if asset type does not exist.
        type_dict = gazu.asset.get_asset_type_by_name(asset_type_name)
        if type_dict:
            return cls.from_dict(type_dict)
        return None

    @classmethod
    def by_id(cls, type_id: str) -> AssetType:
        type_dict = gazu.asset.get_asset_type(type_id)
        return cls.from_dict(type_dict)

    def __bool__(self) -> bool:
        return bool(self.id)


@dataclass
class Shot(Entity):
    """
    Class to get object oriented representation of backend shot data structure.
    Has multiple constructor functions (by_name, by_id, init>by_dict
    """

    id: str = ""
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    canceled: bool = False
    code: Optional[str] = None
    description: Optional[str] = None
    entity_type_id: str = ""
    episode_id: Optional[str] = None
    episode_name: str = ""
    fps: str = ""
    frame_in: str = ""
    frame_out: str = ""
    nb_frames: int = 0
    parent_id: str = ""
    preview_file_id: Optional[str] = None
    project_id: str = ""
    project_name: str = ""
    sequence_id: str = ""
    sequence_name: str = ""
    source_id: Optional[str] = None
    shotgun_id: Optional[str] = None
    type: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    tasks: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def by_name(cls, sequence: Sequence, shot_name: str) -> Optional[Shot]:
        # Can return None if shot does not exist.
        shot_dict = gazu.shot.get_shot_by_name(asdict(sequence), shot_name)
        if shot_dict:
            return cls.from_dict(shot_dict)
        return None

    @classmethod
    def by_id(cls, shot_id: str) -> Shot:
        shot_dict = gazu.shot.get_shot(shot_id)
        return cls.from_dict(shot_dict)

    def get_all_task_types(self) -> List[TaskType]:
        return [TaskType.from_dict(t) for t in gazu.task.all_task_types_for_shot(asdict(self))]

    def get_all_tasks(self) -> List[Task]:
        return [Task.from_dict(t) for t in gazu.task.all_tasks_for_shot(asdict(self))]

    def get_all_assets(self) -> List[Asset]:
        return [Asset.from_dict(t) for t in gazu.asset.all_assets_for_shot(asdict(self))]

    def get_sequence(self) -> Sequence:
        return Sequence.from_dict(gazu.shot.get_sequence_from_shot(asdict(self)))

    def update(self) -> Shot:
        gazu.shot.update_shot(asdict(self))
        return self

    def get_3d_start(self) -> int:
        try:
            logger.info(f"3d_start not found on server, defaulting to '{bkglobals.FRAME_START}'")
            return int(self.data["3d_start"])
        except:
            return bkglobals.FRAME_START

    def get_task_name(self, task_type_short_name: str) -> str:  #
        return f"{self.name}{bkglobals.DELIMITER}{task_type_short_name}"

    def get_output_collection_name(self, task_type_short_name: str) -> str:
        return f"{self.get_task_name(task_type_short_name)}{bkglobals.DELIMITER}output"

    def get_dir(self, context) -> str:
        project_root_dir = prefs.project_root_dir_get(context)
        all_shots_dir = project_root_dir.joinpath('pro').joinpath('shots')

        # Add Episode to Path if available
        if self.episode_id:
            base_dir = all_shots_dir.joinpath(self.episode_name)
        else:
            base_dir = all_shots_dir

        seq = self.get_sequence()
        shot_dir = base_dir.joinpath(seq.name).joinpath(self.name)
        return shot_dir.__str__()

    def get_filepath(self, context, task_type_short_name: str) -> str:
        file_name = self.get_task_name(task_type_short_name) + '.blend'
        return Path(self.get_dir(context)).joinpath(file_name).__str__()

    def update_data(self, data: Dict[str, Any]) -> Shot:
        gazu.shot.update_shot_data(asdict(self), data=data)
        if not self.data:
            self.data = {}
        for key in data:
            self.data[key] = data[key]
        return self

    def remove(self, force: bool = False) -> str:
        return str(gazu.shot.remove_shot(asdict(self), force=force))

    def __bool__(self) -> bool:
        return bool(self.id)


@dataclass
class Asset(Entity):
    """
    Class to get object oriented representation of backend sequence data structure.
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    """

    id: str = ""
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    code: Optional[str] = None
    description: Optional[str] = None
    shotgun_id: Optional[str] = None
    canceled: bool = False
    project_id: str = ""
    entity_type_id: str = ""
    parent_id: str = ""
    preview_file_id: str = ""
    type: str = ""
    project_name: str = ""
    asset_type_id: str = ""
    source_id: str = ""
    asset_type_name: str = ""
    episode_id: str = ""
    nb_frames: Optional[int] = None
    data: Dict[str, Any] = field(default_factory=dict)
    entities_out: List[Any] = field(default_factory=list)
    instance_casting: List[Any] = field(default_factory=list)
    entities_in: List[str] = field(default_factory=list)
    tasks: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def by_name(
        cls,
        project: Project,
        asset_name: str,
        asset_type: Optional[AssetType] = None,
    ) -> Optional[Asset]:
        # Convert args to dict for api call.
        project_dict = asdict(project)
        asset_type_dict = asdict(asset_type) if asset_type else asset_type

        # Can return None if asset does not exist.
        asset_dict = gazu.asset.get_asset_by_name(
            project_dict, asset_name, asset_type=asset_type_dict
        )
        if asset_dict:
            return cls.from_dict(asset_dict)
        return None

    @classmethod
    def by_id(cls, asset_id: str) -> Asset:
        asset_dict = gazu.asset.get_asset(asset_id)
        return cls.from_dict(asset_dict)

    def get_all_task_types(self) -> List[TaskType]:
        return [TaskType.from_dict(t) for t in gazu.task.all_task_types_for_asset(asdict(self))]

    def get_all_tasks(self) -> List[Task]:
        return [Task.from_dict(t) for t in gazu.task.all_tasks_for_asset(asdict(self))]

    def __bool__(self) -> bool:
        return bool(self.id)


@dataclass
class TaskType(Entity):
    """
    Class to get object oriented representation of backend sequence data structure.
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    TaksType is the 'category' a single task belongs to. e.G 'Animation'
    """

    id: str = ""
    pid: str = ""
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    short_name: str = ""
    color: str = ""
    priority: int = 0
    for_shots: Optional[bool] = None
    for_entity: str = ""
    allow_timelog: bool = True
    shotgun_id: Optional[str] = None
    department_id: str = ""
    type: str = ""

    @classmethod
    def by_name(cls, task_type_name: str) -> Optional[TaskType]:
        # Can return None if task type does not exist.
        task_type_dict = gazu.task.get_task_type_by_name(task_type_name)

        if task_type_dict:
            return cls.from_dict(task_type_dict)
        return None

    @classmethod
    def by_id(cls, task_type_id: str) -> TaskType:
        task_type_dict = gazu.task.get_task_type(task_type_id)
        return cls.from_dict(task_type_dict)

    @classmethod
    def all_task_types(cls) -> List[TaskType]:
        return [cls.from_dict(t) for t in gazu.task.all_task_types()]

    @classmethod
    def all_shot_task_types(cls) -> List[TaskType]:
        return [cls.from_dict(t) for t in gazu.task.all_task_types() if t["for_entity"] == "Shot"]

    @classmethod
    def all_asset_task_types(cls) -> List[TaskType]:
        return [cls.from_dict(t) for t in gazu.task.all_task_types() if t["for_entity"] == "Asset"]

    @classmethod
    def all_sequence_task_types(cls) -> List[TaskType]:
        return [
            cls.from_dict(t) for t in gazu.task.all_task_types() if t["for_entity"] == "Sequence"
        ]

    @classmethod
    def all_edit_task_types(cls) -> List[TaskType]:
        return [cls.from_dict(t) for t in gazu.task.all_task_types() if t["for_entity"] == "Edit"]

    def get_short_name(self) -> str:
        # HACK to accomodate custom task types @ blender studio
        if self.name in ["Anim3D", "Anim2D"]:
            return "anim"

        for key, value in bkglobals.SHOT_TASK_MAPPING.items():
            if value == self.name:
                return key

    def __bool__(self) -> bool:
        return bool(self.id)


@dataclass
class Task(Entity):
    """
    Class to get object oriented representation of backend sequence data structure.
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    A Task is a specific task that belongs to a TaskType. e.G Animation of shA1010 would be a task
    with the TaskType 'Animation'
    """

    id: str = ""
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    description: Optional[str] = None
    priority: int = 0
    duration: int = 0
    estimation: int = 0
    completion_rate: int = 0
    retake_count: int = 0
    sort_order: int = 0
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    due_date: Optional[str] = None
    real_start_date: Optional[str] = None
    last_comment_date: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    shotgun_id: Optional[str] = None
    project_id: str = ""
    task_type_id: str = ""
    task_status_id: str = ""
    entity_id: str = ""
    assigner_id: str = ""
    type: str = ""
    assignees: List[Dict[str, Any]] = field(default_factory=list)
    entity: Dict[str, Any] = field(default_factory=dict)  # entitity dict
    task_type: Dict[str, Any] = field(default_factory=dict)  # tastk type dict
    task_status: Dict[str, Any] = field(default_factory=dict)  # tastk status dict
    project: Dict[str, Any] = field(default_factory=dict)  # project dict
    entity_type: Dict[str, Any] = field(default_factory=dict)  # entity type dict
    persons: Dict[str, Any] = field(default_factory=dict)  # persons dict
    assigner: Dict[str, Any] = field(default_factory=dict)  # assiger dict
    sequence: Dict[str, Any] = field(default_factory=dict)  # sequence dict

    # If you call with all_tasks_for_shot you get these extra.
    project_name: str = ""
    task_type_name: str = ""
    task_status_name: str = ""
    entity_type_name: str = ""
    entity_name: str = ""

    # Extra attributes from gazu.user.all_tasks_to_do().
    project_has_avatar: str = "False"
    entity_description: str = ""
    entity_preview_file_id: str = ""
    entity_source_id: str = ""
    sequence_name: str = ""
    episode_id: str = ""
    episode_name: str = ""
    task_estimation: str = ""
    task_duration: str = ""
    task_due_date: str = ""
    task_type_color: str = ""
    task_status_color: str = ""
    task_status_short_name: str = ""
    last_comment: Dict[str, Any] = field(default_factory=dict)  # comment dict

    @classmethod
    def by_name(
        cls,
        asset_shot: Union[Asset, Shot],
        task_type: TaskType,
        name: str = "main",
    ) -> Optional[Task]:
        # Convert args to dict for api call.
        asset_shotdict = asdict(asset_shot)
        task_type_dict = asdict(task_type)

        # Can return None if task does not exist.
        task_dict = gazu.task.get_task_by_name(asset_shotdict, task_type_dict, name)

        if task_dict:
            return cls.from_dict(task_dict)
        return None

    @classmethod
    def by_id(cls, task_id: str) -> Task:
        task_dict = gazu.task.get_task(task_id)
        return cls.from_dict(task_dict)

    @classmethod
    def new_task(
        cls,
        entity: Any,
        task_type: TaskType,
        name: str = "main",
        task_status: Optional[TaskStatus] = None,
        assigner: Optional[Person] = None,
        assignees: Optional[List[Person]] = [],
    ) -> Task:
        # Convert args.
        assigner = asdict(assigner) if assigner else assigner
        task_status = asdict(task_status) if task_status else task_status
        assignees = asdict(assignees) if assignees else assignees

        task_dict = gazu.task.new_task(
            asdict(entity),
            asdict(task_type),
            name=name,
            task_status=task_status,
            assigner=assigner,
            assignees=assignees,
        )
        return cls.from_dict(task_dict)

    @classmethod
    def all_tasks_for_entity_and_task_type(cls, entity: Any, task_type: TaskType) -> List[Task]:
        task_list = gazu.task.all_tasks_for_entity_and_task_type(asdict(entity), asdict(task_type))
        return [cls.from_dict(t) for t in task_list]

    @classmethod
    def all_tasks_for_task_type(cls, project: Project, task_type: TaskType) -> List[Task]:
        task_list = gazu.task.all_tasks_for_task_type(asdict(project), asdict(task_type))
        return [cls.from_dict(t) for t in task_list]

    def get_last_comment(self) -> Comment:
        comment_dict = gazu.task.get_last_comment_for_task(asdict(self))
        return Comment.from_dict(comment_dict)

    def get_all_comments(self) -> List[Comment]:
        return [Comment.from_dict(c) for c in gazu.task.all_comments_for_task(asdict(self))]

    def add_comment(
        self,
        task_status: TaskStatus,
        comment: str = "",
        user: Optional[Person] = None,
        checklist: List[Dict[str, Any]] = [],
        attachments: List[Dict[str, Any]] = [],
        # I think attachements is equal to attachment_files in Comment class.
        created_at: Optional[str] = None,
    ) -> Comment:
        # Convert args.
        person = asdict(user) if user else user

        comment_dict = gazu.task.add_comment(
            asdict(self),
            asdict(task_status),
            comment=comment,
            person=person,
            checklist=checklist,
            attachments=attachments,
            created_at=created_at,
        )
        comment_obj = Comment.from_dict(comment_dict)
        return comment_obj

    def add_preview_to_comment(
        self, comment: Comment, preview_file_path: str, frame_number=0
    ) -> Preview:
        preview_dict = gazu.task.add_preview(
            asdict(self), asdict(comment), preview_file_path, normalize_movie=False
        )
        gazu.task.set_main_preview(preview_dict["id"], frame_number)
        return Preview.from_dict(preview_dict)

    def __bool__(self) -> bool:
        return bool(self.id)


@dataclass
class TaskStatus(Entity):
    """
    Class to get object oriented representation of backend sequence data structure.
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    """

    id: str = ""
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    short_name: str = ""
    color: str = ""
    is_done: bool = False
    is_artist_allowed: bool = True
    is_client_allowed: bool = True
    is_retake: bool = False
    shotgun_id: Optional[str] = None
    is_reviewable: bool = True
    type: str = ""

    @classmethod
    def by_short_name(cls, short_name: str) -> Optional[TaskStatus]:
        # Can return None if task status does not exist.
        task_status_dict = gazu.task.get_task_status_by_short_name(short_name)

        if task_status_dict:
            return cls.from_dict(task_status_dict)
        return None

    @classmethod
    def by_name(cls, name: str) -> Optional[TaskStatus]:
        # Can return None if task status does not exist.
        task_status_dict = gazu.task.get_task_status_by_name(name)

        if task_status_dict:
            return cls.from_dict(task_status_dict)
        return None

    @classmethod
    def by_id(cls, task_status_id: str) -> TaskStatus:
        task_status_dict = gazu.task.get_task_status(task_status_id)
        return cls.from_dict(task_status_dict)

    @classmethod
    def all_task_statuses(cls) -> List[TaskStatus]:
        return [cls.from_dict(ts) for ts in gazu.task.all_task_statuses()]

    def __bool__(self) -> bool:
        return bool(self.id)


@dataclass
class Comment(BaseDataClass):
    """
    Class to get object oriented representation of backend sequence data structure.
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    """

    id: str = ""
    created_at: str = ""
    updated_at: str = ""
    shotgun_id: Optional[str] = None
    object_id: str = ""
    object_type: str = ""
    text: str = ""  # actual comment text
    data: Optional[Dict[str, Any]] = None  # not sure
    checklist: List[Dict[str, Any]] = field(default_factory=list)
    pinned: Optional[bool] = None
    task_status_id: str = ""
    person_id: str = ""
    preview_file_id: Optional[str] = None
    type: str = ""
    person: Dict[str, Any] = field(default_factory=dict)
    task_status: Dict[str, Any] = field(default_factory=dict)
    acknowledgements: List[str] = field(default_factory=list)
    previews: List[Dict[str, Any]] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    attachment_files: List[Dict[str, Any]] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.id)


@dataclass
class Preview(BaseDataClass):
    """
    Class to get object oriented representation of backend sequence data structure.
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    """

    id: str = ""
    created_at: str = ""
    updated_at: str = ""
    name: str = ""
    original_name: Optional[str] = None
    revision: int = 2
    position: int = 2
    extension: str = ""
    description: Optional[str] = None
    path: Optional[str] = None
    source: str = ""
    file_size: int = 0
    status: str = ""
    annotations: List[Dict[str, Any]] = field(default_factory=list)
    task_id: str = ""
    person_id: str = ""
    source_file_id: Optional[str] = None
    shotgun_id: Optional[str] = None
    is_movie: bool = False
    url: Optional[str] = None
    uploaded_movie_url: Optional[str] = None
    uploaded_movie_name: Optional[str] = None
    type: str = ""

    def set_main_preview(self):
        gazu.task.set_main_preview(asdict(self), 0)

    def __bool__(self) -> bool:
        return bool(self.id)


@dataclass
class User(BaseDataClass):
    """
    Class to get object oriented representation of backend sequence data structure.
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    """

    id: str = ""
    created_at: str = ""
    updated_at: str = ""
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    active: bool = True
    last_presence: Optional[str] = None
    desktop_login: str = ""
    shotgun_id: Optional[str] = None
    timezone: str = ""
    locale: str = ""
    data: Optional[Dict[str, Any]] = None
    role: str = ""
    has_avatar: bool = False
    notifications_enabled: bool = False
    notifications_slack_enabled: bool = False
    notifications_slack_userid: str = ""
    type: str = "Person"
    full_name: str = ""

    def __post_init__(self):
        try:
            user_dict = gazu.client.get_current_user()
        except:  # gazu.exception.NotAuthenticatedException
            logger.info("No current user authenticated")
        else:
            self.__dict__.update(user_dict)

    def all_open_projects(self) -> List[Project]:
        project_list = [
            Project.from_dict(project_dict) for project_dict in gazu.user.all_open_projects()
        ]
        return project_list

    def all_tasks_to_do(self) -> List[Task]:
        task_list = [Task.from_dict(task_dict) for task_dict in gazu.user.all_tasks_to_do()]
        return task_list

    # SHOTS.

    def all_sequences_for_project(self, project: Project) -> List[Sequence]:
        seq_list = [
            Sequence.from_dict(seq_dict)
            for seq_dict in gazu.user.all_sequences_for_project(asdict(project))
        ]
        return seq_list

    def all_shots_for_sequence(self, sequence: Sequence) -> List[Shot]:
        shot_list = [
            Shot.from_dict(shot_dict)
            for shot_dict in gazu.user.all_shots_for_sequence(asdict(sequence))
        ]
        return shot_list

    def all_tasks_for_shot(self, shot: Shot) -> List[Task]:
        task_list = [
            Task.from_dict(task_dict) for task_dict in gazu.user.all_tasks_for_shot(asdict(shot))
        ]
        return task_list

    def all_tasks_for_sequence(self, sequence: Sequence) -> List[Task]:
        task_list = [
            Task.from_dict(task_dict)
            for task_dict in gazu.user.all_tasks_for_sequence(asdict(sequence))
        ]
        return task_list

    # ASSETS.

    def all_asset_types_for_project(self, project: Project) -> List[AssetType]:
        asset_type_list = [
            AssetType.from_dict(asset_type_dict)
            for asset_type_dict in gazu.user.all_asset_types_for_project(asdict(project))
        ]
        return asset_type_list

    def all_assets_for_asset_type_and_project(
        self, project: Project, asset_type: AssetType
    ) -> List[Asset]:
        asset_list = [
            Asset.from_dict(asset_dict)
            for asset_dict in gazu.user.all_assets_for_asset_type_and_project(
                asdict(project), asdict(asset_type)
            )
        ]
        return asset_list

    def all_tasks_for_asset(self, asset: Asset) -> List[Task]:
        task_list = [
            Task.from_dict(task_dict) for task_dict in gazu.user.all_tasks_for_asset(asdict(asset))
        ]
        return task_list

    def __bool__(self) -> bool:
        return bool(self.id)


@dataclass
class Person(Entity):
    """
    Class to get object oriented representation of backend sequence data structure.
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    """

    id: str = ""
    created_at: str = ""
    updated_at: str = ""
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    active: bool = True
    last_presence: Optional[str] = None
    desktop_login: str = ""
    shotgun_id: Optional[str] = None
    timezone: str = ""
    locale: str = ""
    data: Optional[Dict[str, Any]] = None
    role: str = ""
    has_avatar: bool = False
    notifications_enabled: bool = False
    notifications_slack_enabled: bool = False
    notifications_slack_userid: str = ""
    type: str = "Person"
    full_name: str = ""

    def by_id(cls, user_id: str) -> Person:
        person_dict = gazu.person.get_person(user_id)
        return cls.from_dict(person_dict)

    def __bool__(self) -> bool:
        return bool(self.id)


@dataclass
class Edit(Entity):
    """
    Class to get object oriented representation of backend edit data structure.
    Can shortcut some functions from gazu api because active project is given through class instance.
    Has multiple constructor functions (by_name, by_id, init>by_dict)
    """

    id: str = ""
    name: str = ""
    frame_start: str = ""
    description: Optional[str] = None

    @classmethod
    def by_name(cls, project: Project, edit_name: str) -> Optional[Edit]:
        # Can return None if edit does not exist.
        edit_dict = gazu.shot.get_edit_by_name(asdict(project), edit_name)
        if edit_dict:
            return cls.from_dict(edit_dict)
        return None

    @classmethod
    def by_id(cls, ep_id: str) -> Edit:
        ep_dict = gazu.edit.get_edit(ep_id)
        return cls.from_dict(ep_dict)

    def __bool__(self) -> bool:
        return bool(self.id)

    def get_previews(self):
        return gazu.edit.all_previews_for_edit(asdict(self))

    def get_frame_start(self):
        try:
            return int(self.frame_start)
        except ValueError:
            return

    def set_frame_start(self, frame_start):
        # TODO Test/Debug
        self.frame_start = frame_start
        gazu.edit.update_edit(asdict(self))
        return


class Cache:
    @classmethod
    def clear_all(cls):
        logger.debug("Cleared Server Cache")
        return gazu.cache.clear_all()
