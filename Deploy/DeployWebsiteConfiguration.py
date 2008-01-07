#
# (c) Peralta Informatics 2007
# $Id: DeployWebsiteConfiguration.py 85 2007-12-12 19:25:32Z andrei $
#

class WebsiteConfiguration(object):

    class AuthenticationConfiguration(object):
        def __init__(self):
            self.Name = None
            self.Type = None

    class ScriptMap(object):
        def __init__(self):
            self.Extension = None
            self.ScriptProcessor = None
            self.Flags = None
            self.IncludedVerbs = None

    def __init__(self):
        self.Name = None
        self.RootFiles = []
        self.RootDirectories = []
        self.BinFiles = []
        self.ApplicationPrefix = None
        self.TargetServer = None
        self.TargetPath = None
        self.TargetRoot = None
        self.SourceConfig = None
        self.SourceRoot = None
        self.PassportUrl = None
        self.SignInUrl = None
        self.SignInImage = None
        self.SignOutUrl = None
        self.SignOutImage = None
        self.CaptchaEnabled = None

        self.CaptchaForeColor = None
        self.CaptchaBgColor = None
        self.CaptchaWidth = None
        self.CaptchaHeight = None
        
        self.Authentication = None

        self.Assembly = None
        self.Type = None
        self.Modules = []

        self.DirectoriesDictionary = {}

        self.ScriptMaps = []

    def __GetApplicationName(self):

        if self.Name != None:
            return self.Name

        else:
            raise Exception("Name attribute is 'None'")

    def __SetApplicationName(self, value):
        self.Name = value

    ApplicationName = property(__GetApplicationName, __SetApplicationName)

