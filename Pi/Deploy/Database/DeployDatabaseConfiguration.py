#
# (c) Peralta Informatics 2007
# $Id: DeployDatabaseConfiguration.py 299 2008-01-19 08:42:05Z andrei $
#

import clr
import System.Collections.Generic

class DatabaseConfiguration(object):

    class HookConfiguration(object):
        Executable = None
        Arguments = None
        BeforeDrop = False

    def __init__(self):
        self.Name = None
        self.Server = None
        self.UserName = None
        self.Password = None
        self.Scripts = []
        self.Hooks = System.Collections.Generic.List[DatabaseConfiguration.HookConfiguration]()
        self.CreateOnce = 'False'
        self.Driver = None
        self.Modules = {}
