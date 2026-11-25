"""工具输出的数据格式。"""

from typing import Literal

from pydantic import BaseModel, Field


class Requirement(BaseModel):
    skill: str
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
    day: int
    hours: float = Field(gt=0, le=12)
    priority: Literal["高", "中", "低"]
    topic: str
    tasks: list[str]
    outcome: str


class Plan(BaseModel):
    days: list[Day]
    milestones: list[str]
