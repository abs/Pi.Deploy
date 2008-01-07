#
# (c) Peralta Informatics 2007
# $Id: DeployDatabaseConfiguration.py 116 2007-12-18 07:31:56Z andrei $
#

import clr
import System.Collections.Generic

class DatabaseConfiguration(object):

    class HookConfiguration(object):
        Executable = None
        Arguments = None

    def __init__(self):
        self.Name = None
        self.Server = None
        self.UserName = None
        self.Password = None
        self.Scripts = []
        self.Hooks = System.Collections.Generic.List[DatabaseConfiguration.HookConfiguration]()
        self.CreateOnce = 'False'
        self.Driver = None
        self.Modules = []

