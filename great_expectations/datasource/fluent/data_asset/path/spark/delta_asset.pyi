from great_expectations.datasource.fluent.data_asset.path.directory_asset import DirectoryDataAsset
from great_expectations.datasource.fluent.data_asset.path.regex_asset import RegexDataAsset

class DeltaAsset(RegexDataAsset): ...
class DirectoryDeltaAsset(DirectoryDataAsset): ...
