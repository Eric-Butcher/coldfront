# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Generated by Django 2.2.4 on 2019-10-17 15:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("resource", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="historicalresourceattribute",
            name="value",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="resourceattribute",
            name="value",
            field=models.TextField(),
        ),
    ]
