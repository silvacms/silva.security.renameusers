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
from Acquisition import aq_base


class IRenameUsersFields(interface.Interface):

    mapping = silvaschema.Bytes(
        title=u"CSV file mapping new users identifier to old ones",
        description=u"Two columns CSV file, first column being " \
            "the new user identifier, second one the old.",
        required=True)

    update_roles = schema.Bool(
        title=u"Update content local roles",
        description=u"Rename user identifier in Zope local roles.",
        default=True,
        required=True)

    update_ownership = schema.Bool(
        title=u"Update content ownership information",
        default=True,
        required=True)

    update_version = schema.Bool(
        title=u"Update Silva content versions as well",
        description=u"Rename local roles/ownership on Silva content version.",
        default=False,
        required=True)

    update_members = schema.Bool(
        title=u"Update members objects to the new identifier",
        description=u"Rename Silva members and update theirs identifiers.",
        default=True,
        required=True)

    @interface.invariant
    def update_roles_invariant(options):
        if (options.update_version and not (
                options.update_roles or options.update_ownership)):
            raise interface.Invalid(
                u"Cannot update version ownership without "
                u"updating all permission access/ownership information.")


def update_roles(mapping, content):
    to_remove = []
    to_add = []
    changed = 0
    for identifier, roles in content.get_local_roles():
        if identifier in mapping:
            to_remove.append(identifier)
            to_add.append((mapping[identifier], roles))
            changed += 1
    for identifier in to_remove:
        content.manage_delLocalRoles([identifier])
    for identifier, roles in to_add:
        content.manage_setLocalRoles(identifier, roles)
    return changed

def update_ownership(mapping, content):
    info = aq_base(content).getOwnerTuple()
    if info is not None:
        if info[1] in mapping:
            acl_users = content.acl_users
            user = acl_users.getUser(mapping[info[1]])
            if user is not None:
                content.changeOwnership(user.__of__(acl_users), False)
                return 1
    return 0


class RenameUsersForm(silvaforms.ZMIForm):
    grok.context(ExtensionService)
    grok.name('manage_renameUsers')

    label = u"Rename users"
    description = u"User identifiers mass-modification."
    fields = silvaforms.Fields(IRenameUsersFields)

    def update_silva_contents(self, mapping, updaters, do_version=False):
        if not updaters:
            return []
        changes = [0] * len(updaters)
        for content in walk_silva_tree(self.context.get_root(), version=do_version):
            for index, updater in enumerate(updaters):
                changes[index] += updater(mapping, content)
        return changes

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

        updaters = []
        messages_format = []
        if data['update_roles']:
            updaters.append(update_roles)
            messages_format.append('reaffected %d roles')
        if data['update_ownership']:
            updaters.append(update_ownership)
            messages_format.append('changed %d owners')

        changes = self.update_silva_contents(
            mapping, updaters, data['update_version'])
        for index, count in enumerate(changes):
            messages.append(messages_format[index] % (count))

        self.status = u', '.join(messages) + u'.'
        return silvaforms.SUCCESS


