# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import csv

from five import grok
from silva.core.conf import schema as silvaschema
from silva.core.services.utils import walk_silva_tree
from zeam.form import silva as silvaforms
from zope import interface, schema

# There is no interface (yet) for that service.
from Products.Silva.ExtensionService import ExtensionService


class IRenameUsersFields(interface.Interface):

    mapping = silvaschema.Bytes(
        title=u"CSV file mapping new users identifier to old ones",
        description=u"Two columns CSV file, first column being " \
            "the new user identifier, second one the old.",
        required=True)

    update_roles = schema.Bool(
        title=u"Update permission access to use the new identifier",
        default=True,
        required=True)

    update_members = schema.Bool(
        title=u"Update members objects to the new identifier",
        description=u"Rename members objects and update theirs identifiers.",
        default=True,
        required=True)


class RenameUsersForm(silvaforms.ZMIForm):
    grok.context(ExtensionService)
    grok.name('manage_renameUsers')

    label = u"Rename user identifiers"
    description = u"Non-undoable user identifiers mass-modification."
    fields = silvaforms.Fields(IRenameUsersFields)

    def update_roles(self, mapping):
        modification_count = 0
        for content in walk_silva_tree(self.context.get_root()):
            to_remove = []
            to_add = []
            for identifier, roles in content.get_local_roles():
                if identifier in mapping:
                    to_remove.append(identifier)
                    to_add.append((mapping[identifier], roles))
                    modification_count += 1
            for identifier in to_remove:
                content.manage_delLocalRoles([identifier])
            for identifier, roles in to_add:
                content.manage_setLocalRoles(identifier, roles)
        return modification_count

    def rename_members(self, mapping):
        modification_count = 0
        members = self.context.get_root().Members
        member_ids = set(members.objectIds())
        for old_id, new_id in mapping.iteritems():
            if old_id in member_ids:
                # Rename the object by hand since manage_renameObject
                # is not supported.
                member = members[old_id]
                del members[old_id]
                member_ids.remove(old_id)
                if new_id not in member_ids:
                    # Well, there can be multiple old id for a new
                    # one.
                    member.id = new_id
                    members[new_id] = member
                    member_ids.add(new_id)
                modification_count += 1
        return modification_count

    @silvaforms.action("Rename")
    def rename(self):
        data, errors = self.extractData()
        if errors:
            return silvaforms.FAILURE
        mapping = {}
        try:
            reader = csv.reader(data['mapping'], delimiter=';')
            for line_number, line in enumerate(reader):
                if len(line) != 2:
                    msg = u'Invalid number of identifiers in CSV at line %d !'
                    self.status = msg % (line_number + 1)
                    return silvaforms.FAILURE
                new_id = line[0].strip()
                old_id = line[1].strip()
                if old_id in mapping and mapping[old_id] != new_id:
                    msg = u'Duplicate mapping for user %s at line %d !'
                    self.status = msg % (old_id, line_number + 1)
                    return silvaforms.FAILURE
                mapping[old_id] = new_id
        except csv.Error:
            self.status = u'Invalid CSV file.'
            return silvaforms.FAILURE
        messages = [u'Updated %d users' % (len(mapping))]
        if data['update_members']:
            count = self.rename_members(mapping)
            messages.append('renamed %d members objects' % count)
        if data['update_roles']:
            count = self.update_roles(mapping)
            messages.append('reaffected %d roles' % count)
        self.status = u', '.join(messages) + u'.'
        return silvaforms.SUCCESS


