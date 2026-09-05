"""Pydantic schemas for request/response validation."""

from typing import Optional
from pydantic import BaseModel


class HostCreate(BaseModel):
    name: str
    group_id: Optional[int] = None
    vars: dict = {}


class HostUpdate(BaseModel):
    name: str
    group_id: Optional[int] = None
    vars: dict = {}


class GroupCreate(BaseModel):
    name: str
    vars: dict = {}


class GroupUpdate(BaseModel):
    name: str
    vars: dict = {}


class LoginRequest(BaseModel):
    username: str
    password: str
