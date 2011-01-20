# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from Products.Silva.testing import SilvaLayer
import silva.security.renameusers


class RenameUsersLayer(SilvaLayer):
    default_packages = SilvaLayer.default_packages + [
        'silva.security.renameusers'
        ]
    default_users = dict(SilvaLayer.default_users.items() + {
        'sylvain': [],
        'pierre': [],
        'arthur': [],
        }.items())


FunctionalLayer = RenameUsersLayer(silva.security.renameusers)
