class GeCloudIdAwareRef:
    """
    This class serves as a base class for refs tied to a Great Expectations Cloud ID.
    """

    def __init__(self, id_: str) -> None:
        self._id_ = id_

    @property
    def id_(self):
        return self._id_


class GeCloudResourceRef(GeCloudIdAwareRef):
    """
    This class represents a reference to a Great Expectations object persisted to Great Expectations Cloud.
    """

    def __init__(self, resource_type: str, id_: str, url: str) -> None:
        self._resource_type = resource_type
        self._url = url
        super().__init__(id_=id_)

    @property
    def resource_type(self):
        # e.g. "checkpoint"
        return self._resource_type

    @property
    def url(self):
        return self._url
