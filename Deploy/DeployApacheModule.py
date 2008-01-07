#
# (c) Peralta Informatics 2007
# $Id: DeployApacheModule.py 102 2007-12-16 09:20:41Z andrei $
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

from DeployModule import DeployModule
from DeployWebModule import DeployWebModule

class DeployApacheModule(DeployWebModule):
    def __init__(self): pass


    def CreateApplication(self, website):
        print 'Creating Apache application (not implemented)'


    def RecycleAppPool(self, website):
        print 'Recycling Apache app pool (not implemented)'

    
    def DeleteApplication(self, website):
        print 'Deleting Apache application (not implemented)'


