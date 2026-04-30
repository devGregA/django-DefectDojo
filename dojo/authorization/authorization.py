"""
Legacy authorization checks.

The hierarchical RBAC role system has been replaced with the simpler
pre-2020 model: a user is authorized for an action on an object iff

  * the user is a superuser, or
  * the user is staff and the action is non-destructive
    (View / Edit / Add / Import; Delete and member-management require explicit
    staff confirmation but legacy treats every staff user as eligible), or
  * the user is in the relevant ``authorized_users`` ManyToMany
    (climbing the Product_Type → Product → Engagement → Test → Finding
    hierarchy until an explicit membership is found).

Per-product role granularity (Reader / Writer / Maintainer / Owner),
group-level authorization, and configuration permissions per add/edit/delete
codename are not present in this model. Deployments that need that fidelity
should run the dojo-pro plugin, which keeps the RBAC layer alive and shadows
this module's symbols at startup so the same code paths route through Pro.

The public surface (function names + signatures) is preserved so existing
callers in dojo/views.py, dojo/forms.py, etc. keep compiling. Track B step
#13 simplifies callers to pass action strings directly; until that lands,
the existing ``Permissions.X`` enum members are still accepted and reduced
to a legacy Action via ``permission_to_action()``.
"""
from django.core.exceptions import PermissionDenied
from django.db.models import Model, QuerySet

from dojo.authorization.models import (
    Dojo_Group_Member,
    Product_Group,
    Product_Member,
    Product_Type_Group,
    Product_Type_Member,
)
from dojo.authorization.roles_permissions import (
    Action,
    permission_to_action,
)
from dojo.location.models import AbstractLocation, Location
from dojo.models import (
    App_Analysis,
    Cred_Mapping,
    Dojo_Group,
    Dojo_User,
    Endpoint,
    Engagement,
    Finding,
    Finding_Group,
    Languages,
    Product,
    Product_API_Scan_Configuration,
    Product_Type,
    Risk_Acceptance,
    Stub_Finding,
    Test,
)


def user_has_configuration_permission(user: Dojo_User, permission: str):
    if not user:
        return False
    if user.is_anonymous:
        return False
    return user.has_perm(permission)


def user_is_superuser_or_global_owner(user: Dojo_User) -> bool:
    """
    Legacy: there is no Owner role; only the superuser flag elevates
    a user to system-wide authority.
    """
    if not user or getattr(user, "is_anonymous", False):
        return False
    return bool(user.is_superuser)


def user_has_permission(user: Dojo_User, obj: Model, permission) -> bool:
    """
    Legacy object-level authorization check.

    Resolution order:

      1. anonymous → deny
      2. superuser → allow
      3. action → mapped from Permissions / string / Action via permission_to_action
      4. SuperuserOnly action → deny (already handled superuser above)
      5. StaffOnly / Delete → require is_staff
      6. View / Edit / Add / Import → is_staff bypasses unconditionally,
         otherwise check membership in the obj.authorized_users chain
         (climbing Product_Type ← Product ← Engagement ← Test ← Finding).
         This matches the pre-Auth-V2 (pre-2020) behavior where is_staff
         was an absolute bypass on every perm_type — see
         dojo/user/helper.py at commit e7805aa14~ for the historical
         reference.

    The Member / Group / Cred_Mapping / etc. carrier objects don't expose
    authorized_users themselves; they delegate to their wrapped product
    or product type, except for self-removal (a user is always allowed to
    delete their own membership row).
    """
    if not user or getattr(user, "is_anonymous", False):
        return False
    if user.is_superuser:
        return True

    action = permission_to_action(permission)

    if action == Action.SuperuserOnly:
        return False

    if action in {Action.StaffOnly, Action.Delete}:
        return bool(user.is_staff)

    # Member/group self-deletion: any user can remove their own membership
    if isinstance(obj, Product_Type_Member | Product_Member | Dojo_Group_Member) and obj.user_id == user.id:
        return True

    return _user_authorized_for(user, obj, action)


def _user_authorized_for(user: Dojo_User, obj: Model, action: Action) -> bool:
    """
    Membership-chain check. Returns True if user has any membership that
    grants ``action`` on ``obj``.
    """
    if obj is None:
        return False

    if isinstance(obj, Product_Type):
        if user.is_staff:
            return True
        return obj.authorized_users.filter(pk=user.pk).exists()

    if isinstance(obj, Product):
        if user.is_staff:
            return True
        if obj.authorized_users.filter(pk=user.pk).exists():
            return True
        return bool(obj.prod_type_id and obj.prod_type.authorized_users.filter(pk=user.pk).exists())

    if isinstance(obj, Engagement):
        return _user_authorized_for(user, obj.product, action)

    if isinstance(obj, Test):
        return _user_authorized_for(user, obj.engagement.product, action) if obj.engagement_id else False

    if isinstance(obj, Finding | Stub_Finding):
        return _user_authorized_for(user, obj.test.engagement.product, action)

    if isinstance(obj, Finding_Group):
        return _user_authorized_for(user, obj.test.engagement.product, action)

    if isinstance(obj, Risk_Acceptance):
        if obj.engagement_id is not None:
            return _user_authorized_for(user, obj.engagement.product, action)
        return False

    if isinstance(obj, Location):
        return any(_user_authorized_for(user, ref.product, action) for ref in obj.products.all())

    if isinstance(obj, AbstractLocation):
        return _user_authorized_for(user, obj.location, action)

    if isinstance(obj, Endpoint | Languages | App_Analysis | Product_API_Scan_Configuration):
        return _user_authorized_for(user, obj.product, action)

    if isinstance(obj, Product_Type_Member | Product_Type_Group):
        return _user_authorized_for(user, obj.product_type, action)

    if isinstance(obj, Product_Member | Product_Group):
        return _user_authorized_for(user, obj.product, action)

    if isinstance(obj, Dojo_Group | Dojo_Group_Member):
        # Group authorization is staff-only in legacy; non-staff already filtered out.
        return bool(user.is_staff)

    if isinstance(obj, Cred_Mapping):
        if obj.product_id:
            return _user_authorized_for(user, obj.product, action)
        if obj.engagement_id:
            return _user_authorized_for(user, obj.engagement.product, action)
        if obj.test_id:
            return _user_authorized_for(user, obj.test.engagement.product, action)
        if obj.finding_id:
            return _user_authorized_for(user, obj.finding.test.engagement.product, action)
        return False

    msg = f"No legacy authorization implemented for class {type(obj).__name__}"
    raise NoAuthorizationImplementedError(msg)


def user_has_global_permission(user: Dojo_User, permission) -> bool:
    """
    Legacy: global permissions reduce to is_superuser / is_staff.

    The one Django configuration-permission carve-out preserved from the
    pre-2020 model: ``dojo.add_product_type`` lets a non-staff user
    create product types if explicitly granted via Django auth.
    """
    if not user or getattr(user, "is_anonymous", False):
        return False
    if user.is_superuser:
        return True

    action = permission_to_action(permission)

    if permission == "add" and user_has_configuration_permission(user, "dojo.add_product_type"):
        return True

    if action == Action.SuperuserOnly:
        return False
    return bool(user.is_staff)


def user_has_configuration_permission_or_403(user: Dojo_User, permission: str) -> None:
    if not user_has_configuration_permission(user, permission):
        raise PermissionDenied


def user_has_permission_or_403(user: Dojo_User, obj: Model, permission) -> None:
    if not user_has_permission(user, obj, permission):
        raise PermissionDenied


def user_has_global_permission_or_403(user: Dojo_User, permission) -> None:
    if not user_has_global_permission(user, permission):
        raise PermissionDenied


# ---------------------------------------------------------------------------
# Backward-compat shims for the role hierarchy. Legacy authorization does not
# branch on roles, but call sites still import these symbols. Returning empty
# results keeps them harmless until Track B step #13 simplifies the callers.
# ---------------------------------------------------------------------------


def get_roles_for_permission(permission) -> set[int]:
    return set()


def role_has_permission(role: int, permission) -> bool:
    return False


def role_has_global_permission(role: int, permission) -> bool:
    return False


class NoAuthorizationImplementedError(Exception):
    def __init__(self, message):
        self.message = message


class PermissionDoesNotExistError(Exception):
    def __init__(self, message):
        self.message = message


class RoleDoesNotExistError(Exception):
    def __init__(self, message):
        self.message = message


# ---------------------------------------------------------------------------
# RBAC member / group lookup helpers. These return empty/None under legacy —
# the underlying tables (Product_Member, Product_Type_Member, etc.) still
# exist in the database, but legacy authorization does not consult them.
# Track B step #13 will remove call sites; until then these stubs prevent
# AttributeError / TypeError in transitional code.
# ---------------------------------------------------------------------------


def get_product_member(user: Dojo_User, product: Product) -> Product_Member | None:
    return None


def get_product_member_dict(user: Dojo_User) -> dict[int, Product_Member]:
    return {}


def get_product_type_member(user: Dojo_User, product_type: Product_Type) -> Product_Type_Member | None:
    return None


def get_product_type_member_dict(user: Dojo_User) -> dict[int, Product_Type_Member]:
    return {}


def get_product_groups(user: Dojo_User, product: Product) -> list[Product_Group]:
    return []


def get_product_groups_dict(user: Dojo_User) -> dict[int, list[Product_Group]]:
    return {}


def get_product_type_groups(user: Dojo_User, product_type: Product_Type) -> list[Product_Type_Group]:
    return []


def get_product_type_groups_dict(user: Dojo_User) -> dict[int, list[Product_Type_Group]]:
    return {}


def get_groups(user: Dojo_User) -> QuerySet[Dojo_Group]:
    return Dojo_Group.objects.none()


def get_group_member(user: Dojo_User, group: Dojo_Group) -> Dojo_Group_Member | None:
    return None


def get_group_members_dict(user: Dojo_User) -> dict[int, Dojo_Group_Member]:
    return {}
