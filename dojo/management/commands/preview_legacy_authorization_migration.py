"""
Pre-flight preview of the legacy authorization migration.

Dry-run companion to ``dojo.0267_backfill_authorized_users``. Prints what
the data migration *would* change without writing anything to the database
so customers can audit the impact before they upgrade.

Usage::

    python manage.py preview_legacy_authorization_migration            # tabular
    python manage.py preview_legacy_authorization_migration --json     # JSON

Reports:

  * Per-product / per-product-type ``authorized_users`` rows that would be
    added (broken down by source: direct member rows vs flattened group
    members).
  * Users that would be flipped to ``is_superuser=True`` (Global_Role.Owner).
  * Users that would be flipped to ``is_staff=True`` (Global_Role.Maintainer
    / API_Importer).
  * Counts of role granularity that the legacy model cannot preserve
    (Reader vs Writer vs Maintainer per product, group membership as a
    permission-bearing entity, configuration permissions per codename).

Read-only. The RBAC tables themselves are never modified by either this
command or the data migration; running it on a fresh OS install is a no-op.
"""
import json

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Preview the legacy authorization migration's impact without applying it."

    def add_arguments(self, parser):
        parser.add_argument(
            "--json",
            action="store_true",
            dest="emit_json",
            help="Emit the report as JSON instead of human-readable tables.",
        )

    def handle(self, *args, emit_json=False, **options):
        if "dojo_role" not in connection.introspection.table_names():
            self.stdout.write(
                self.style.SUCCESS(
                    "No RBAC tables present — the legacy authorization migration "
                    "would be a no-op on this database.",
                ),
            )
            return

        report = self._build_report()
        if emit_json:
            self.stdout.write(json.dumps(report, indent=2, default=str))
        else:
            self._render_tables(report)

    # ------------------------------------------------------------------
    # Data collection
    # ------------------------------------------------------------------

    def _build_report(self):
        # Imported lazily so the command imports cleanly even when the
        # legacy shells are eventually deleted from dojo/authorization/
        # models.py (Track B step #13).
        from dojo.authorization.models import (  # noqa: PLC0415
            Dojo_Group_Member,
            Global_Role,
            Product_Group,
            Product_Member,
            Product_Type_Group,
            Product_Type_Member,
        )
        from dojo.models import Dojo_User, Product, Product_Type  # noqa: PLC0415

        product_member_pairs = set(Product_Member.objects.values_list("product_id", "user_id"))
        product_type_member_pairs = set(Product_Type_Member.objects.values_list("product_type_id", "user_id"))

        product_group_pairs = set()
        for product_id, group_id in Product_Group.objects.values_list("product_id", "group_id"):
            product_group_pairs.update((product_id, user_id) for user_id in Dojo_Group_Member.objects.filter(group_id=group_id).values_list("user_id", flat=True))

        product_type_group_pairs = set()
        for product_type_id, group_id in Product_Type_Group.objects.values_list("product_type_id", "group_id"):
            product_type_group_pairs.update((product_type_id, user_id) for user_id in Dojo_Group_Member.objects.filter(group_id=group_id).values_list("user_id", flat=True))

        # Already-existing authorized_users rows (so we report incremental adds).
        existing_product_pairs = set(Product.authorized_users.through.objects.values_list("product_id", "dojo_user_id"))
        existing_product_type_pairs = set(Product_Type.authorized_users.through.objects.values_list("product_type_id", "dojo_user_id"))

        new_product_pairs = (product_member_pairs | product_group_pairs) - existing_product_pairs
        new_product_type_pairs = (product_type_member_pairs | product_type_group_pairs) - existing_product_type_pairs

        owner_user_ids = set(
            Global_Role.objects.filter(role__name="Owner", user__isnull=False).values_list("user_id", flat=True),
        )
        owner_group_ids = list(
            Global_Role.objects.filter(role__name="Owner", group__isnull=False).values_list("group_id", flat=True),
        )
        owner_user_ids |= set(
            Dojo_Group_Member.objects.filter(group_id__in=owner_group_ids).values_list("user_id", flat=True),
        )
        new_superuser_ids = set(
            Dojo_User.objects.filter(id__in=owner_user_ids, is_superuser=False).values_list("id", flat=True),
        )

        elevated_user_ids = set(
            Global_Role.objects.filter(
                role__name__in=("Maintainer", "API_Importer"),
                user__isnull=False,
            ).values_list("user_id", flat=True),
        )
        elevated_group_ids = list(
            Global_Role.objects.filter(
                role__name__in=("Maintainer", "API_Importer"),
                group__isnull=False,
            ).values_list("group_id", flat=True),
        )
        elevated_user_ids |= set(
            Dojo_Group_Member.objects.filter(group_id__in=elevated_group_ids).values_list("user_id", flat=True),
        )
        new_staff_ids = set(
            Dojo_User.objects.filter(id__in=elevated_user_ids, is_staff=False).values_list("id", flat=True),
        )

        # Granularity that legacy cannot preserve.
        per_role_member_counts = _count_by_role_name(Product_Member)
        per_role_member_type_counts = _count_by_role_name(Product_Type_Member)
        group_role_count = Product_Group.objects.count() + Product_Type_Group.objects.count()

        return {
            "authorized_users_additions": {
                "product": {
                    "from_direct_members": len(product_member_pairs - existing_product_pairs),
                    "from_group_expansion": len(product_group_pairs - product_member_pairs - existing_product_pairs),
                    "total_new_pairs": len(new_product_pairs),
                },
                "product_type": {
                    "from_direct_members": len(product_type_member_pairs - existing_product_type_pairs),
                    "from_group_expansion": len(product_type_group_pairs - product_type_member_pairs - existing_product_type_pairs),
                    "total_new_pairs": len(new_product_type_pairs),
                },
            },
            "global_role_flag_flips": {
                "is_superuser_count": len(new_superuser_ids),
                "is_superuser_user_ids": sorted(new_superuser_ids),
                "is_staff_count": len(new_staff_ids),
                "is_staff_user_ids": sorted(new_staff_ids),
            },
            "granularity_lost": {
                "product_member_role_counts": per_role_member_counts,
                "product_type_member_role_counts": per_role_member_type_counts,
                "group_based_authorization_rows": group_role_count,
                "note": (
                    "Legacy collapses Reader / Writer / Maintainer / Owner per-product "
                    "distinction to membership-only. Group structure as a permission-"
                    "bearing entity is also lost; only individual user memberships "
                    "remain after the migration."
                ),
            },
        }

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render_tables(self, report):
        adds = report["authorized_users_additions"]
        flags = report["global_role_flag_flips"]
        lost = report["granularity_lost"]

        self.stdout.write(self.style.MIGRATE_HEADING("authorized_users additions"))
        self.stdout.write(
            f"  Product       : +{adds['product']['total_new_pairs']:>6} pairs "
            f"({adds['product']['from_direct_members']} direct, "
            f"{adds['product']['from_group_expansion']} from group expansion)",
        )
        self.stdout.write(
            f"  Product_Type  : +{adds['product_type']['total_new_pairs']:>6} pairs "
            f"({adds['product_type']['from_direct_members']} direct, "
            f"{adds['product_type']['from_group_expansion']} from group expansion)",
        )

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Global_Role flag flips"))
        self.stdout.write(f"  is_superuser <- True  : {flags['is_superuser_count']} user(s)")
        if flags["is_superuser_user_ids"]:
            self.stdout.write(f"      user_ids: {flags['is_superuser_user_ids']}")
        self.stdout.write(f"  is_staff     <- True  : {flags['is_staff_count']} user(s)")
        if flags["is_staff_user_ids"]:
            self.stdout.write(f"      user_ids: {flags['is_staff_user_ids']}")

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Granularity not preserved"))
        for label, counts in (
            ("Product_Member by role", lost["product_member_role_counts"]),
            ("Product_Type_Member by role", lost["product_type_member_role_counts"]),
        ):
            self.stdout.write(f"  {label}:")
            if not counts:
                self.stdout.write("      (none)")
            for role, count in counts.items():
                self.stdout.write(f"      {role:>14}: {count}")
        self.stdout.write(
            f"  Group-based authorization rows (lost): {lost['group_based_authorization_rows']}",
        )
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("  " + lost["note"]))


def _count_by_role_name(model):
    from django.db.models import Count  # noqa: PLC0415

    return {
        row["role__name"]: row["count"]
        for row in model.objects.values("role__name").annotate(count=Count("id"))
    }
