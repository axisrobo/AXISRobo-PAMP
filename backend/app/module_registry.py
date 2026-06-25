"""Module registry for selective API deployment."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from fastapi import APIRouter

from app import architecture_review
from app import application_management
from app import add
from app import data_management
from app import project_management
from app import technology_stack_management


@dataclass(frozen=True)
class ModuleRegistration:
    key: str
    router: APIRouter
    prefix: str = "/api"


MODULE_REGISTRY: dict[str, ModuleRegistration] = {
    "add": ModuleRegistration(
        key="add",
        router=add.router,
    ),
    "architecture_review": ModuleRegistration(
        key="architecture_review",
        router=architecture_review.router,
    ),
    "application_management": ModuleRegistration(
        key="application_management",
        router=application_management.router,
    ),
    "data_management": ModuleRegistration(
        key="data_management",
        router=data_management.router,
    ),
    "project_management": ModuleRegistration(
        key="project_management",
        router=project_management.router,
    ),
    "technology_stack_management": ModuleRegistration(
        key="technology_stack_management",
        router=technology_stack_management.router,
    ),
}


def parse_enabled_modules(raw_value: str) -> set[str]:
    values = [item.strip() for item in (raw_value or "").split(",") if item.strip()]
    return set(values)


def iter_enabled_module_registrations(enabled_module_keys: Iterable[str]) -> list[ModuleRegistration]:
    result: list[ModuleRegistration] = []
    for key in enabled_module_keys:
        registration = MODULE_REGISTRY.get(key)
        if registration:
            result.append(registration)
    return result
