try:
    from dojo.authorization.query_filters import get_auth_filter
except ImportError:
    def get_auth_filter(key): return None

try:
    from dojo.authorization.models import Global_Role, Product_Type_Group, Product_Type_Member
except ImportError:
    Global_Role = None
    Product_Type_Group = None
    Product_Type_Member = None

from dojo.models import Product_Type
from dojo.request_cache import cache_for_request


# Cached: all parameters are hashable, no dynamic queryset filtering
@cache_for_request
def get_authorized_product_types(permission):
    impl = get_auth_filter("product_type.get_authorized_product_types")
    if impl:
        return impl(permission)
    return Product_Type.objects.all().order_by("name")


def get_authorized_product_type_members(permission):
    impl = get_auth_filter("product_type.get_authorized_product_type_members")
    if impl:
        return impl(permission)
    return Product_Type_Member.objects.all().order_by("id").select_related("role")


def get_authorized_product_type_groups(permission):
    impl = get_auth_filter("product_type.get_authorized_product_type_groups")
    if impl:
        return impl(permission)
    return Product_Type_Group.objects.all().order_by("id").select_related("role")
