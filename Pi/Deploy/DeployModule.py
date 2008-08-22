#
# (c) Peralta Informatics 2007
# $Id: DeployModule.py 116 2007-12-18 07:31:56Z andrei $
#

import clr
import sys
import os
import shutil

clr.AddReference("System.Data")
clr.AddReference("System.Xml")

import System.Collections.Generic
import System.Data
import System.Data.SqlClient
import System.Text
import System.Xml

class DeployModule(object):
    def __init__(self):
        pass

    def Execute(self, configuration, action): pass
    def ReadConfiguration(self, reader, configuration): pass
    def CreateWebConfigSections(self, webConfigDocument, configuration): pass
    def PopulateDatabase(self, database): pass
    def PrintHelp(self): pass
    def PrintConfiguration(self, configuration): pass

    NamespaceUri = property()
    Name = property()

