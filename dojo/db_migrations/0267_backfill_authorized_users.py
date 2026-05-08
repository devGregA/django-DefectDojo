"""Backfill authorized_users from RBAC tables.

Forward-only data migration. Translates the dojo_product_member /
dojo_product_type_member / dojo_product_group / dojo_product_type_group /
dojo_global_role / dojo_dojo_group_member rows into Product.authorized_users
and Product_Type.authorized_users membership, plus is_superuser / is_staff
flag flips for users with elevated Global_Roles.

Idempotent: guarded on the presence of the dojo_role table so fresh OS
installs (which never had RBAC) become a no-op. The RBAC tables themselves
are NOT modified or dropped — they remain available verbatim so a later
dojo-pro install can pick them up unchanged.

Mapping (per the legacy authorization design):

  Product_Member.user (any role)        -> Product.authorized_users
  Product_Type_Member.user (any role)   -> Product_Type.authorized_users
  Product_Group.group + Dojo_Group_Member.user
                                        -> Product.authorized_users (flattened)
  Product_Type_Group.group + Dojo_Group_Member.user
                                        -> Product_Type.authorized_users (flattened)
  Global_Role(Owner) for user           -> User.is_superuser = True
  Global_Role(Owner) via group          -> all group members.is_superuser = True
  Global_Role(Writer|Maintainer|API_Importer) for user
                                        -> User.is_staff = True
  Global_Role(Writer|Maintainer|API_Importer) via group
                                        -> all group members.is_staff = True
  Global_Role(Reader)                   -> no global elevation
                                          (relies on per-product membership)

Things lost on this transition (acknowledged in the upgrade release notes):
  - Reader / Writer / Maintainer / Owner per-product role granularity
  - Group structure as a permission-bearing entity
  - The API_Importer global role specifically
  - Configuration permissions per add/edit/delete codename
"""
from django.db import migrations


def backfill_authorized_users(apps, schema_editor):
    connection = schema_editor.connection
    if "dojo_role" not in connection.introspection.table_names():
        # Fresh install: no RBAC tables. Nothing to do.
        return

    try:
        Product = apps.get_model("dojo", "Product")
        Product_Type = apps.get_model("dojo", "Product_Type")
        Dojo_User = apps.get_model("dojo", "Dojo_User")
        Product_Member = apps.get_model("dojo", "Product_Member")
        Product_Type_Member = apps.get_model("dojo", "Product_Type_Member")
        Product_Group = apps.get_model("dojo", "Product_Group")
        Product_Type_Group = apps.get_model("dojo", "Product_Type_Group")
        Dojo_Group_Member = apps.get_model("dojo", "Dojo_Group_Member")
        Global_Role = apps.get_model("dojo", "Global_Role")
    except LookupError:
        # Models already released from the dojo app state. Nothing to do.
        return

    # 1. Direct per-product / per-product-type memberships.
    for product_id, user_id in Product_Member.objects.values_list("product_id", "user_id"):
        Product.authorized_users.through.objects.get_or_create(
            product_id=product_id, dojo_user_id=user_id,
        )
    for product_type_id, user_id in Product_Type_Member.objects.values_list("product_type_id", "user_id"):
        Product_Type.authorized_users.through.objects.get_or_create(
            product_type_id=product_type_id, dojo_user_id=user_id,
        )

    # 2. Group memberships: flatten Dojo_Group_Member.user into authorized_users.
    for product_id, group_id in Product_Group.objects.values_list("product_id", "group_id"):
        member_user_ids = Dojo_Group_Member.objects.filter(group_id=group_id).values_list("user_id", flat=True)
        for user_id in member_user_ids:
            Product.authorized_users.through.objects.get_or_create(
                product_id=product_id, dojo_user_id=user_id,
            )
    for product_type_id, group_id in Product_Type_Group.objects.values_list("product_type_id", "group_id"):
        member_user_ids = Dojo_Group_Member.objects.filter(group_id=group_id).values_list("user_id", flat=True)
        for user_id in member_user_ids:
            Product_Type.authorized_users.through.objects.get_or_create(
                product_type_id=product_type_id, dojo_user_id=user_id,
            )

    # 3. Global_Role -> is_superuser / is_staff flags.
    owner_user_ids = list(
        Global_Role.objects.filter(role__name="Owner", user__isnull=False).values_list("user_id", flat=True),
    )
    owner_group_ids = list(
        Global_Role.objects.filter(role__name="Owner", group__isnull=False).values_list("group_id", flat=True),
    )
    owner_user_ids.extend(
        Dojo_Group_Member.objects.filter(group_id__in=owner_group_ids).values_list("user_id", flat=True),
    )
    if owner_user_ids:
        Dojo_User.objects.filter(id__in=owner_user_ids).update(is_superuser=True)

    elevated_user_ids = list(
        Global_Role.objects.filter(
            role__name__in=("Writer", "Maintainer", "API_Importer"),
            user__isnull=False,
        ).values_list("user_id", flat=True),
    )
    elevated_group_ids = list(
        Global_Role.objects.filter(
            role__name__in=("Writer", "Maintainer", "API_Importer"),
            group__isnull=False,
        ).values_list("group_id", flat=True),
    )
    elevated_user_ids.extend(
        Dojo_Group_Member.objects.filter(group_id__in=elevated_group_ids).values_list("user_id", flat=True),
    )
    if elevated_user_ids:
        Dojo_User.objects.filter(id__in=elevated_user_ids).update(is_staff=True)


def reverse_noop(apps, schema_editor):
    # Reverse is a no-op. Backfilled authorized_users membership and is_superuser /
    # is_staff flags are preserved if this migration is rolled back; reverse cannot
    # reliably distinguish migrated entries from manually-added ones, and the source
    # RBAC tables are still intact for a forward re-run anyway.
    return


class Migration(migrations.Migration):

    dependencies = [
        ("dojo", "0266_reintroduce_authorized_users"),
    ]

    operations = [
        migrations.RunPython(backfill_authorized_users, reverse_noop),
    ]
