import os
from typing import List, Optional

from great_expectations.data_context.store import ProfilerStore
from great_expectations.data_context.types.base import DataContextConfigDefaults


def list_profilers(
    profiler_store: ProfilerStore,
    ge_cloud_mode: bool,
) -> List[str]:
    if ge_cloud_mode:
        return profiler_store.list_keys()
    return [x.configuration_key for x in profiler_store.list_keys()]


def default_profilers_exist(directory_path: Optional[str]) -> bool:
    if not directory_path:
        return False

    checkpoints_directory_path: str = os.path.join(
        directory_path,
        DataContextConfigDefaults.DEFAULT_PROFILER_STORE_BASE_DIRECTORY_RELATIVE_NAME.value,
    )
    return os.path.isdir(checkpoints_directory_path)
