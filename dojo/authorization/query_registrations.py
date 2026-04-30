"""
Legacy authorization queryset filters.

The RBAC role-aware querysets have been replaced with the simpler legacy
model: each filter restricts results to objects whose underlying Product /
Product_Type the user is a member of (via ``authorized_users``), with
``is_superuser`` and ``is_staff`` bypasses.

The dojo/authorization/queries entry-point names (e.g. ``product.get_
authorized_products``) are preserved so the per-app queries.py modules and
the API filter classes that look them up via ``get_auth_filter()`` keep
working without code changes. Track B step #13 will simplify those callers.

RBAC-carrier queries (``product.get_authorized_members_for_product`` and
similar) return empty querysets for non-staff users — the membership tables
still exist on disk but legacy authorization does not consult them. The
dojo-pro plugin re-registers Pro implementations of these filters at startup
that DO consult the tables.
"""
from crum import get_current_user
from django.db.models import Q

from dojo.authorization.models import (
    Dojo_Group_Member,
    Global_Role,
    Product_Group,
    Product_Member,
    Product_Type_Group,
    Product_Type_Member,
)
from dojo.authorization.query_filters import register_auth_filter
from dojo.authorization.roles_permissions import permission_to_action
from dojo.location.models import Location, LocationFindingReference, LocationProductReference
from dojo.models import (
    App_Analysis,
    Cred_Mapping,
    Dojo_Group,
    Dojo_User,
    DojoMeta,
    Endpoint,
    Endpoint_Status,
    Engagement,
    Engagement_Presets,
    Finding,
    Finding_Group,
    JIRA_Issue,
    JIRA_Project,
    Languages,
    Product,
    Product_API_Scan_Configuration,
    Product_Type,
    Risk_Acceptance,
    Stub_Finding,
    Test,
    Test_Import,
    Tool_Product_Settings,
    Vulnerability_Id,
)


def _resolve_user(user):
    return user if user is not None else get_current_user()


def _is_unrestricted(user, action):
    """
    Returns True if the user can see every object regardless of membership.
    Superuser and staff both bypass — matches pre-2020 behavior where
    is_staff was an absolute bypass for every perm_type. The ``action``
    arg is retained for callers that may want to gate StaffOnly /
    SuperuserOnly differently in the future.
    """
    if not user or getattr(user, "is_anonymous", False):
        return False
    if user.is_superuser:
        return True
    return bool(user.is_staff)


def _authorized_product_ids(user):
    return Product.objects.filter(
        Q(authorized_users=user) | Q(prod_type__authorized_users=user),
    ).values("id")


def _authorized_product_type_ids(user):
    return Product_Type.objects.filter(authorized_users=user).values("id")


def _filter_by_authorized_products(queryset, product_path, permission, user=None):
    """
    Generic helper: restrict ``queryset`` to rows whose ``product_path`` FK
    points at a Product the user is authorized for. ``product_path`` is a
    Django ORM lookup like ``"product"`` or ``"engagement__product"``.
    """
    user = _resolve_user(user)
    if user is None or getattr(user, "is_anonymous", False):
        return queryset.none()
    action = permission_to_action(permission)
    if _is_unrestricted(user, action):
        return queryset
    return queryset.filter(**{f"{product_path}__id__in": _authorized_product_ids(user)})


def _carrier_queryset(qs, user, action):
    """
    Visibility for RBAC carrier rows under legacy: staff/superuser see
    every row; everyone else sees nothing.
    """
    if user is None or getattr(user, "is_anonymous", False):
        return qs.none()
    if _is_unrestricted(user, action) or user.is_staff:
        return qs
    return qs.none()


# ---------------------------------------------------------------------------
# Product / Product_Type
# ---------------------------------------------------------------------------


def _get_authorized_products(permission, user=None):
    user = _resolve_user(user)
    if user is None or getattr(user, "is_anonymous", False):
        return Product.objects.none()
    if _is_unrestricted(user, permission_to_action(permission)):
        return Product.objects.all().order_by("name")
    return Product.objects.filter(
        Q(authorized_users=user) | Q(prod_type__authorized_users=user),
    ).distinct().order_by("name")


register_auth_filter("product.get_authorized_products", _get_authorized_products)


def _get_authorized_product_types(permission, user=None):
    user = _resolve_user(user)
    if user is None or getattr(user, "is_anonymous", False):
        return Product_Type.objects.none()
    if _is_unrestricted(user, permission_to_action(permission)):
        return Product_Type.objects.all().order_by("name")
    return Product_Type.objects.filter(authorized_users=user).order_by("name")


register_auth_filter("product_type.get_authorized_product_types", _get_authorized_product_types)


# ---------------------------------------------------------------------------
# Children of Product / Product_Type (membership inherited)
# ---------------------------------------------------------------------------


def _get_authorized_engagements(permission):
    return _filter_by_authorized_products(Engagement.objects.all(), "product", permission)


register_auth_filter("engagement.get_authorized_engagements", _get_authorized_engagements)


def _get_authorized_tests(permission, product=None):
    qs = Test.objects.all()
    if product is not None:
        qs = qs.filter(engagement__product=product)
    return _filter_by_authorized_products(qs, "engagement__product", permission)


register_auth_filter("test.get_authorized_tests", _get_authorized_tests)


def _get_authorized_test_imports(permission):
    return _filter_by_authorized_products(Test_Import.objects.all(), "test__engagement__product", permission)


register_auth_filter("test.get_authorized_test_imports", _get_authorized_test_imports)


def _get_authorized_risk_acceptances(permission):
    return _filter_by_authorized_products(Risk_Acceptance.objects.all(), "engagement__product", permission)


register_auth_filter("risk_acceptance.get_authorized_risk_acceptances", _get_authorized_risk_acceptances)


def _get_authorized_finding_groups(permission, user=None):
    return _filter_by_authorized_products(
        Finding_Group.objects.all(), "test__engagement__product", permission, user=user,
    )


register_auth_filter("finding_group.get_authorized_finding_groups", _get_authorized_finding_groups)


def _get_authorized_finding_groups_for_queryset(permission, queryset, user=None):
    return _filter_by_authorized_products(queryset, "test__engagement__product", permission, user=user)


register_auth_filter("finding_group.get_authorized_finding_groups_for_queryset", _get_authorized_finding_groups_for_queryset)


def _get_authorized_app_analysis(permission):
    return _filter_by_authorized_products(App_Analysis.objects.all(), "product", permission)


register_auth_filter("product.get_authorized_app_analysis", _get_authorized_app_analysis)


def _get_authorized_dojo_meta(permission):
    user = get_current_user()
    if user is None or getattr(user, "is_anonymous", False):
        return DojoMeta.objects.none()
    if _is_unrestricted(user, permission_to_action(permission)):
        return DojoMeta.objects.all()
    authorized_products = _authorized_product_ids(user)
    authorized_product_types = _authorized_product_type_ids(user)
    return DojoMeta.objects.filter(
        Q(product__id__in=authorized_products)
        | Q(product_type__id__in=authorized_product_types)
        | Q(finding__test__engagement__product__id__in=authorized_products)
        | Q(endpoint__product__id__in=authorized_products),
    )


register_auth_filter("product.get_authorized_dojo_meta", _get_authorized_dojo_meta)


def _get_authorized_languages(permission):
    return _filter_by_authorized_products(Languages.objects.all(), "product", permission)


register_auth_filter("product.get_authorized_languages", _get_authorized_languages)


def _get_authorized_engagement_presets(permission):
    return _filter_by_authorized_products(Engagement_Presets.objects.all(), "product", permission)


register_auth_filter("product.get_authorized_engagement_presets", _get_authorized_engagement_presets)


def _get_authorized_product_api_scan_configurations(permission):
    return _filter_by_authorized_products(
        Product_API_Scan_Configuration.objects.all(), "product", permission,
    )


register_auth_filter("product.get_authorized_product_api_scan_configurations", _get_authorized_product_api_scan_configurations)


def _get_authorized_jira_projects(permission, user=None):
    user = _resolve_user(user)
    if user is None or getattr(user, "is_anonymous", False):
        return JIRA_Project.objects.none()
    if _is_unrestricted(user, permission_to_action(permission)):
        return JIRA_Project.objects.all()
    authorized_products = _authorized_product_ids(user)
    authorized_product_types = _authorized_product_type_ids(user)
    return JIRA_Project.objects.filter(
        Q(product__id__in=authorized_products)
        | Q(product__prod_type__id__in=authorized_product_types)
        | Q(engagement__product__id__in=authorized_products),
    ).distinct()


register_auth_filter("jira_link.get_authorized_jira_projects", _get_authorized_jira_projects)


def _get_authorized_jira_issues(permission):
    user = get_current_user()
    if user is None or getattr(user, "is_anonymous", False):
        return JIRA_Issue.objects.none()
    if _is_unrestricted(user, permission_to_action(permission)):
        return JIRA_Issue.objects.all()
    authorized_products = _authorized_product_ids(user)
    return JIRA_Issue.objects.filter(
        Q(engagement__product__id__in=authorized_products)
        | Q(finding__test__engagement__product__id__in=authorized_products)
        | Q(finding_group__test__engagement__product__id__in=authorized_products),
    )


register_auth_filter("jira_link.get_authorized_jira_issues", _get_authorized_jira_issues)


def _get_authorized_tool_product_settings(permission):
    return _filter_by_authorized_products(Tool_Product_Settings.objects.all(), "product", permission)


register_auth_filter("tool_product.get_authorized_tool_product_settings", _get_authorized_tool_product_settings)


def _get_authorized_cred_mappings(permission):
    user = get_current_user()
    if user is None or getattr(user, "is_anonymous", False):
        return Cred_Mapping.objects.none()
    if _is_unrestricted(user, permission_to_action(permission)):
        return Cred_Mapping.objects.all()
    authorized_products = _authorized_product_ids(user)
    return Cred_Mapping.objects.filter(
        Q(product__id__in=authorized_products)
        | Q(engagement__product__id__in=authorized_products)
        | Q(test__engagement__product__id__in=authorized_products)
        | Q(finding__test__engagement__product__id__in=authorized_products),
    )


register_auth_filter("cred.get_authorized_cred_mappings", _get_authorized_cred_mappings)


def _get_authorized_cred_mappings_for_queryset(permission, queryset):
    user = get_current_user()
    if user is None or getattr(user, "is_anonymous", False):
        return queryset.none()
    if _is_unrestricted(user, permission_to_action(permission)):
        return queryset
    authorized_products = _authorized_product_ids(user)
    return queryset.filter(
        Q(product__id__in=authorized_products)
        | Q(engagement__product__id__in=authorized_products)
        | Q(test__engagement__product__id__in=authorized_products)
        | Q(finding__test__engagement__product__id__in=authorized_products),
    )


register_auth_filter("cred.get_authorized_cred_mappings_for_queryset", _get_authorized_cred_mappings_for_queryset)


# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------


def _get_authorized_locations(permission, queryset=None, user=None):
    user = _resolve_user(user)
    qs = queryset if queryset is not None else Location.objects.all()
    if user is None or getattr(user, "is_anonymous", False):
        return qs.none()
    if _is_unrestricted(user, permission_to_action(permission)):
        return qs
    authorized_products = _authorized_product_ids(user)
    return qs.filter(products__product__id__in=authorized_products).distinct()


register_auth_filter("location.get_authorized_locations", _get_authorized_locations)


def _get_authorized_location_finding_reference(permission, queryset=None, user=None):
    user = _resolve_user(user)
    qs = queryset if queryset is not None else LocationFindingReference.objects.all()
    if user is None or getattr(user, "is_anonymous", False):
        return qs.none()
    if _is_unrestricted(user, permission_to_action(permission)):
        return qs
    authorized_products = _authorized_product_ids(user)
    return qs.filter(finding__test__engagement__product__id__in=authorized_products)


register_auth_filter("location.get_authorized_location_finding_reference", _get_authorized_location_finding_reference)


def _get_authorized_location_product_reference(permission, queryset=None, user=None):
    user = _resolve_user(user)
    qs = queryset if queryset is not None else LocationProductReference.objects.all()
    if user is None or getattr(user, "is_anonymous", False):
        return qs.none()
    if _is_unrestricted(user, permission_to_action(permission)):
        return qs
    authorized_products = _authorized_product_ids(user)
    return qs.filter(product__id__in=authorized_products)


register_auth_filter("location.get_authorized_location_product_reference", _get_authorized_location_product_reference)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


def _get_authorized_endpoints(permission):
    return _filter_by_authorized_products(Endpoint.objects.all(), "product", permission)


register_auth_filter("endpoint.get_authorized_endpoints", _get_authorized_endpoints)


def _get_authorized_endpoint_status(permission):
    return _filter_by_authorized_products(
        Endpoint_Status.objects.all(), "endpoint__product", permission,
    )


register_auth_filter("endpoint.get_authorized_endpoint_status", _get_authorized_endpoint_status)


# ---------------------------------------------------------------------------
# Findings / Stub_Findings / Vulnerability_Ids
# ---------------------------------------------------------------------------


def _get_authorized_findings(permission, queryset=None, user=None):
    user = _resolve_user(user)
    qs = queryset if queryset is not None else Finding.objects.all()
    if user is None or getattr(user, "is_anonymous", False):
        return qs.none()
    if _is_unrestricted(user, permission_to_action(permission)):
        return qs
    return qs.filter(test__engagement__product__id__in=_authorized_product_ids(user))


register_auth_filter("finding.get_authorized_findings", _get_authorized_findings)


def _get_authorized_stub_findings(permission):
    return _filter_by_authorized_products(
        Stub_Finding.objects.all(), "test__engagement__product", permission,
    )


register_auth_filter("finding.get_authorized_stub_findings", _get_authorized_stub_findings)


def _get_authorized_vulnerability_ids(permission, queryset=None, user=None):
    user = _resolve_user(user)
    qs = queryset if queryset is not None else Vulnerability_Id.objects.all()
    if user is None or getattr(user, "is_anonymous", False):
        return qs.none()
    if _is_unrestricted(user, permission_to_action(permission)):
        return qs
    return qs.filter(finding__test__engagement__product__id__in=_authorized_product_ids(user))


register_auth_filter("finding.get_authorized_vulnerability_ids", _get_authorized_vulnerability_ids)


# ---------------------------------------------------------------------------
# RBAC carrier queries — staff/superuser see all rows, others see none
# ---------------------------------------------------------------------------


def _get_authorized_members_for_product(product, permission):
    return _carrier_queryset(
        Product_Member.objects.filter(product=product).select_related("role", "user"),
        get_current_user(),
        permission_to_action(permission),
    )


register_auth_filter("product.get_authorized_members_for_product", _get_authorized_members_for_product)


def _get_authorized_global_members_for_product(product, permission):
    return _carrier_queryset(
        Global_Role.objects.filter(group=None, role__isnull=False).select_related("role", "user"),
        get_current_user(),
        permission_to_action(permission),
    )


register_auth_filter("product.get_authorized_global_members_for_product", _get_authorized_global_members_for_product)


def _get_authorized_groups_for_product(product, permission):
    return _carrier_queryset(
        Product_Group.objects.filter(product=product).select_related("role"),
        get_current_user(),
        permission_to_action(permission),
    )


register_auth_filter("product.get_authorized_groups_for_product", _get_authorized_groups_for_product)


def _get_authorized_global_groups_for_product(product, permission):
    return _carrier_queryset(
        Global_Role.objects.filter(user=None, role__isnull=False).select_related("role"),
        get_current_user(),
        permission_to_action(permission),
    )


register_auth_filter("product.get_authorized_global_groups_for_product", _get_authorized_global_groups_for_product)


def _get_authorized_product_members(permission):
    return _carrier_queryset(
        Product_Member.objects.all().select_related("role"),
        get_current_user(),
        permission_to_action(permission),
    )


register_auth_filter("product.get_authorized_product_members", _get_authorized_product_members)


def _get_authorized_product_members_for_user(user, permission):
    return _carrier_queryset(
        Product_Member.objects.filter(user=user).select_related("role", "product"),
        get_current_user(),
        permission_to_action(permission),
    )


register_auth_filter("product.get_authorized_product_members_for_user", _get_authorized_product_members_for_user)


def _get_authorized_product_groups(permission):
    return _carrier_queryset(
        Product_Group.objects.all().select_related("role"),
        get_current_user(),
        permission_to_action(permission),
    )


register_auth_filter("product.get_authorized_product_groups", _get_authorized_product_groups)


def _get_authorized_members_for_product_type(product_type, permission):
    return _carrier_queryset(
        Product_Type_Member.objects.filter(product_type=product_type).select_related("role", "user"),
        get_current_user(),
        permission_to_action(permission),
    )


register_auth_filter("product_type.get_authorized_members_for_product_type", _get_authorized_members_for_product_type)


def _get_authorized_global_members_for_product_type(product_type, permission):
    return _carrier_queryset(
        Global_Role.objects.filter(group=None, role__isnull=False).select_related("role", "user"),
        get_current_user(),
        permission_to_action(permission),
    )


register_auth_filter("product_type.get_authorized_global_members_for_product_type", _get_authorized_global_members_for_product_type)


def _get_authorized_groups_for_product_type(product_type, permission):
    return _carrier_queryset(
        Product_Type_Group.objects.filter(product_type=product_type).select_related("role"),
        get_current_user(),
        permission_to_action(permission),
    )


register_auth_filter("product_type.get_authorized_groups_for_product_type", _get_authorized_groups_for_product_type)


def _get_authorized_global_groups_for_product_type(product_type, permission):
    return _carrier_queryset(
        Global_Role.objects.filter(user=None, role__isnull=False).select_related("role"),
        get_current_user(),
        permission_to_action(permission),
    )


register_auth_filter("product_type.get_authorized_global_groups_for_product_type", _get_authorized_global_groups_for_product_type)


def _get_authorized_product_type_members(permission):
    return _carrier_queryset(
        Product_Type_Member.objects.all().select_related("role"),
        get_current_user(),
        permission_to_action(permission),
    )


register_auth_filter("product_type.get_authorized_product_type_members", _get_authorized_product_type_members)


def _get_authorized_product_type_members_for_user(user, permission):
    return _carrier_queryset(
        Product_Type_Member.objects.filter(user=user).select_related("role", "product_type"),
        get_current_user(),
        permission_to_action(permission),
    )


register_auth_filter("product_type.get_authorized_product_type_members_for_user", _get_authorized_product_type_members_for_user)


def _get_authorized_product_type_groups(permission):
    return _carrier_queryset(
        Product_Type_Group.objects.all().select_related("role"),
        get_current_user(),
        permission_to_action(permission),
    )


register_auth_filter("product_type.get_authorized_product_type_groups", _get_authorized_product_type_groups)


# ---------------------------------------------------------------------------
# User / Group queries
# ---------------------------------------------------------------------------


def _get_authorized_users(permission, user=None):
    user = _resolve_user(user)
    if user is None or getattr(user, "is_anonymous", False):
        return Dojo_User.objects.none()
    if _is_unrestricted(user, permission_to_action(permission)) or user.is_staff:
        return Dojo_User.objects.all().order_by("first_name", "last_name")
    return Dojo_User.objects.filter(pk=user.pk)


register_auth_filter("user.get_authorized_users", _get_authorized_users)


def _get_authorized_users_for_product_type(users, product_type, permission):
    user = get_current_user()
    if user is None or getattr(user, "is_anonymous", False):
        return users.none()
    if _is_unrestricted(user, permission_to_action(permission)) or user.is_staff:
        return users
    return users.none()


register_auth_filter("user.get_authorized_users_for_product_type", _get_authorized_users_for_product_type)


def _get_authorized_users_for_product_and_product_type(users, product, permission):
    user = get_current_user()
    if user is None or getattr(user, "is_anonymous", False):
        return users.none()
    if _is_unrestricted(user, permission_to_action(permission)) or user.is_staff:
        return users
    return users.none()


register_auth_filter("user.get_authorized_users_for_product_and_product_type", _get_authorized_users_for_product_and_product_type)


def _get_authorized_groups(permission):
    user = get_current_user()
    if user is None or getattr(user, "is_anonymous", False):
        return Dojo_Group.objects.none()
    if _is_unrestricted(user, permission_to_action(permission)) or user.is_staff:
        return Dojo_Group.objects.all().order_by("name")
    return Dojo_Group.objects.none()


register_auth_filter("group.get_authorized_groups", _get_authorized_groups)


def _get_authorized_group_members(permission):
    return _carrier_queryset(
        Dojo_Group_Member.objects.all().select_related("role", "group", "user"),
        get_current_user(),
        permission_to_action(permission),
    )


register_auth_filter("group.get_authorized_group_members", _get_authorized_group_members)


def _get_authorized_group_members_for_user(user):
    request_user = get_current_user()
    if request_user is None or getattr(request_user, "is_anonymous", False):
        return Dojo_Group_Member.objects.none()
    if request_user.is_superuser or request_user.is_staff:
        return Dojo_Group_Member.objects.filter(user=user).select_related("group", "role")
    return Dojo_Group_Member.objects.none()


register_auth_filter("group.get_authorized_group_members_for_user", _get_authorized_group_members_for_user)
