"""
Release the RBAC tables from dojo's app state.

Pairs with ``pro.0049_adopt_rbac_tables``: Pro adopts the seven RBAC
tables (``dojo_role``, ``dojo_global_role``, ``dojo_dojo_group_member``,
``dojo_product_member``, ``dojo_product_group``, ``dojo_product_type_member``,
``dojo_product_type_group``) into Pro's app state via a state-only
``CreateModel`` for each. This migration flips the same seven models in
dojo's state to ``managed=False`` so dojo never issues DDL for them again.

Together this ownership transfer is bit-for-bit non-destructive: no DDL
runs, no rows move, no constraints are dropped or rebuilt. The tables
sit dormant in OS-only deployments (used only by Pro) and continue to
hold whatever data the customer's deployment had.

The model class definitions in ``dojo/authorization/models.py`` remain as
``managed=False`` shells until Track B step #13 simplifies the OS callers
that still ``isinstance``-check / import them; at that point the shells
go away entirely. Pro's ``apps.ready()`` symbol shadowing keeps the
RBAC code paths active under Pro deployments regardless.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("dojo", "0267_backfill_authorized_users"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="dojo_group_member",
            options={"managed": False},
        ),
        migrations.AlterModelOptions(
            name="global_role",
            options={"managed": False},
        ),
        migrations.AlterModelOptions(
            name="product_group",
            options={"managed": False},
        ),
        migrations.AlterModelOptions(
            name="product_member",
            options={"managed": False},
        ),
        migrations.AlterModelOptions(
            name="product_type_group",
            options={"managed": False},
        ),
        migrations.AlterModelOptions(
            name="product_type_member",
            options={"managed": False},
        ),
        migrations.AlterModelOptions(
            name="role",
            options={"managed": False, "ordering": ("name",)},
        ),
        migrations.AlterModelTable(
            name="dojo_group_member",
            table="dojo_dojo_group_member",
        ),
        migrations.AlterModelTable(
            name="global_role",
            table="dojo_global_role",
        ),
        migrations.AlterModelTable(
            name="product_group",
            table="dojo_product_group",
        ),
        migrations.AlterModelTable(
            name="product_member",
            table="dojo_product_member",
        ),
        migrations.AlterModelTable(
            name="product_type_group",
            table="dojo_product_type_group",
        ),
        migrations.AlterModelTable(
            name="product_type_member",
            table="dojo_product_type_member",
        ),
        migrations.AlterModelTable(
            name="role",
            table="dojo_role",
        ),
    ]
