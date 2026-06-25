"""Scoped business role resolution — delegates to EE module when enabled."""


async def resolve_scoped_roles(user, db):
    from app.config import settings
    if settings.EE_ENABLED:
        from app.ee.role_resolver import resolve_scoped_roles as _ee_resolve
        return await _ee_resolve(user, db)
    return user


async def _is_team_member(itcode, db):
    from app.config import settings
    if settings.EE_ENABLED:
        from app.ee.role_resolver import _is_team_member as _ee_fn
        return await _ee_fn(itcode, db)
    return False


async def _is_app_owner(user_id, email_prefix, db):
    from app.config import settings
    if settings.EE_ENABLED:
        from app.ee.role_resolver import _is_app_owner as _ee_fn
        return await _ee_fn(user_id, email_prefix, db)
    return False


async def _is_project_owner(user_id, db):
    from app.config import settings
    if settings.EE_ENABLED:
        from app.ee.role_resolver import _is_project_owner as _ee_fn
        return await _ee_fn(user_id, db)
    return False
