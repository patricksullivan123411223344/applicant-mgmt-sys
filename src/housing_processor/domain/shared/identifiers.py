from typing import NewType
from uuid import UUID

ApplicationId = NewType("ApplicationId", UUID)
ApplicantId = NewType("ApplicantId", UUID)
GroupId = NewType("GroupId", UUID)
ReviewItemId = NewType("ReviewItemId", UUID)
PropertyId = NewType("PropertyId", UUID)
