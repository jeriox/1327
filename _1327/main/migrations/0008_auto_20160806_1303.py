# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-08-06 11:03
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_auto_20160711_1653'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='menuitem',
            options={'ordering': ['order'], 'permissions': (('view_menuitem', 'User/Group is allowed to view this menu item'), ('changechildren_menuitem', 'User/Group is allowed to change children items'))},
        ),
    ]
