# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import csv

from five import grok
from silva.core.conf import schema as silvaschema
from zeam.form import silva as silvaforms
from zope import interface

# There is no interface (yet) for that service.
from Products.Silva.ExtensionService import ExtensionService


class IRenameUsersFields(interface.Interface):

    mapping = silvaschema.Bytes(
        title=u"CSV file mapping new users identifier to old ones",
        description=u"Two columns CSV file, first column being " \
            "the old user identifier, second one the new.",
        required=True)


class RenameUsersForm(silvaforms.ZMIForm):
    grok.context(ExtensionService)
    grok.name('manage_renameUsers')

    label = u"Rename users"
    fields = silvaforms.Fields(IRenameUsersFields)

    def update_access(self, mapping):
        pass

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
                old_id = line[0].strip()
                new_id = line[1].strip()
                if old_id in mapping:
                    msg = u'Duplicate mapping for user %s at line %d !'
                    self.status = msg % (old_id, line_number + 1)
                    return silvaforms.FAILURE
                mapping[old_id] = new_id
        except csv.Error:
            self.status = u'Invalid CSV file.'
            return silvaforms.FAILURE
        self.update_access(mapping)
        self.status = u'Updated for %d users.' % (len(mapping))
        return silvaforms.SUCCESS


