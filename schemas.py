"""工具输出的数据格式。"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Requirement(BaseModel):
    skill: Text
    evidence: str = Field(description="JD 中逐字引用的依据")


class Job(BaseModel):
    title: str
    education: str
    experience: str
    required: list[Requirement]
    preferred: list[Requirement]
    responsibilities: list[str]


class Gap(BaseModel):
    skill: str
    status: Literal["已掌握", "部分掌握", "尚未掌握"]
    importance: str
    evidence: str
    reason: str


class Gaps(BaseModel):
    items: list[Gap]


class Day(BaseModel):
    day: int = Field(ge=1)
    hours: float = Field(gt=0, le=12)
    priority: Literal["高", "中", "低"]
    topic: Text
    tasks: list[Text] = Field(min_length=1)
    outcome: Text


class Plan(BaseModel):
    days: list[Day]
    milestones: list[Text] = Field(min_length=1)
