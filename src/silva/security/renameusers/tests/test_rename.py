# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import unittest

from silva.core.services.interfaces import IMemberService
from silva.security.renameusers.testing import FunctionalLayer
from zope.component import getUtility

from Products.Silva.tests.helpers import test_filename
from Products.Silva.ftesting import zmi_settings


class RenameUsersTestCase(unittest.TestCase):
    layer = FunctionalLayer
    FORM_URL = '/root/service_extensions/manage_renameUsers'

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('manager')

    def create_member_objects(self):
        members = getUtility(IMemberService)
        for userid in ['member', 'author', 'chiefeditor', 'editor']:
            # Getting a member object for the first time will create
            # it.
            members.get_member(userid)

    def test_form_access_validation(self):
        browser = self.layer.get_browser(zmi_settings)
        self.assertEqual(browser.open(self.FORM_URL), 401)
        browser.login('manager')
        self.assertEqual(browser.open(self.FORM_URL), 200)
        self.assertEqual(browser.inspect.zmi_title, ['Rename users'])

        form = browser.get_form('form')
        self.assertEqual(form.inspect.actions, ['Rename'])
        self.assertEqual(form.inspect.actions['rename'].click(), 200)
        self.assertEqual(browser.inspect.zmi_status, ['There were errors.'])

    def test_rename_member_objects(self):
        self.create_member_objects()
        self.assertEqual(
            list(self.root.Members.objectIds()),
            ['author', 'chiefeditor', 'editor', 'manager'])

        browser = self.layer.get_browser(zmi_settings)
        browser.login('manager')
        self.assertEqual(browser.open(self.FORM_URL), 200)

        csv_filename = test_filename('renames.csv', globals())
        form = browser.get_form('form')
        form.get_control('form.field.update_roles').value = False
        form.get_control('form.field.update_ownership').value = False
        form.get_control('form.field.update_members').value = True
        form.get_control('form.field.mapping').value = csv_filename
        self.assertEqual(form.inspect.actions['rename'].click(), 200)
        self.assertEqual(
            browser.inspect.zmi_status,
            ['Updated 3 users, renamed 2 members objects.'])

        self.assertEqual(
            list(self.root.Members.objectIds()),
            ['arthur', 'chiefeditor', 'editor', 'sylvain'])
        self.assertEqual(
            self.root.Members.arthur.id,
            'arthur')

    def test_rename_roles(self):
        get_user_roles = self.root.get_local_roles_for_userid
        self.assertEqual(get_user_roles('sylvain'), ())
        self.assertEqual(get_user_roles('manager'), ('Owner',))

        browser = self.layer.get_browser(zmi_settings)
        browser.login('manager')
        self.assertEqual(browser.open(self.FORM_URL), 200)

        csv_filename = test_filename('renames.csv', globals())
        form = browser.get_form('form')
        form.get_control('form.field.update_roles').value = True
        form.get_control('form.field.update_ownership').value = False
        form.get_control('form.field.update_members').value = False
        form.get_control('form.field.mapping').value = csv_filename
        self.assertEqual(form.inspect.actions['rename'].click(), 200)
        self.assertEqual(
            browser.inspect.zmi_status,
            ['Updated 3 users, reaffected 2 roles.'])

        self.assertEqual(get_user_roles('sylvain'), ('Owner',))
        self.assertEqual(get_user_roles('manager'), ())

    def test_change_ownership(self):
        get_owner = lambda obj: obj.getOwner().getId()
        self.assertEqual(get_owner(self.root), 'manager')
        self.assertEqual(get_owner(self.root.index), 'manager')

        browser = self.layer.get_browser(zmi_settings)
        browser.login('manager')
        self.assertEqual(browser.open(self.FORM_URL), 200)

        csv_filename = test_filename('renames.csv', globals())
        form = browser.get_form('form')
        form.get_control('form.field.update_roles').value = False
        form.get_control('form.field.update_ownership').value = True
        form.get_control('form.field.update_members').value = False
        form.get_control('form.field.mapping').value = csv_filename
        self.assertEqual(form.inspect.actions['rename'].click(), 200)
        self.assertEqual(
            browser.inspect.zmi_status,
            ['Updated 3 users, changed 1 owners.'])

        self.assertEqual(get_owner(self.root), 'sylvain')
        self.assertEqual(get_owner(self.root.index), 'sylvain')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(RenameUsersTestCase))
    return suite
