#
# (c) Peralta Informatics 2007
# $Id: DeployDatabaseModule.py 299 2008-01-19 08:42:05Z andrei $
#

import clr
import sys
import os
import shutil

clr.AddReference("System.Data")
clr.AddReference("System.Xml")

import System.Data
import System.Data.SqlClient
import System.Diagnostics
import System.Text
import System.Xml

from Pi.Deploy import DeployUtilities
from Pi.Deploy.DeployConfiguration import Configuration
from Pi.Deploy.DeployAction import Action
from Pi.Deploy.DeployModule import DeployModule

from DeployDatabaseConfiguration import DatabaseConfiguration



SourceFilesAttributeName             = 'SourceFiles'
DirectoriesAttributeName             = 'Directories'

DatabaseElementName                  = 'Database'
NameAttributeName                    = 'Name'
ServerAttributeName                  = 'Server'
UserNameAttributeName                = 'UserName'
PasswordAttributeName                = 'Password'
CreateOnceAttributeName              = 'CreateOnce'
DriverAttributeName                  = 'Driver'
ApplicationNameAttributeName         = 'ApplicationName'
IntegratedSecurityAttributeName      = 'IntegratedSecurity'
TrustedConnectionAttributeName       = 'TrustedConnection'

ScriptsElementName                   = 'Scripts'

HooksElementName                     = 'Hooks'
HookElementName                      = 'Hook'
ExecutableElementName                = 'Executable'
ArgumentsElementName                 = 'Arguments'


class DeployDatabaseModule(DeployModule):

    def __init__(self):
        pass


    def CreateWebConfigSections(self, document, configuration):

        if hasattr(configuration, 'Databases'):

            for database in configuration.Databases:

                for module in database.Modules.values():
                    module.CreateWebConfigSections(document, configuration)


    def ReadConfiguration(self, reader, configuration, database = None):
        
        if not hasattr(configuration, 'Databases'):
            configuration.Databases = []

        if reader.NodeType == System.Xml.XmlNodeType.Element: 

            if reader.LocalName == DatabaseElementName and reader.NamespaceURI == self.NamespaceUri:

                if database == None:
                    database = DatabaseConfiguration()
                    configuration.Databases.Add(database)

                self.__ReadDatabaseConfiguration(reader, database)

                database.ConnectionString = self.CreateConnectionString(database)


    def __ReadDatabaseConfiguration(self, reader, database):

        if reader.MoveToAttribute(NameAttributeName):
            database.Name = reader.ReadContentAsString()

        if reader.MoveToAttribute(ServerAttributeName):
            database.Server = reader.ReadContentAsString()

        if reader.MoveToAttribute(ApplicationNameAttributeName):
            database.ApplicationName = reader.ReadContentAsString()

        if reader.MoveToAttribute(IntegratedSecurityAttributeName):
            database.IntegratedSecurity = reader.ReadContentAsString()

        if reader.MoveToAttribute(TrustedConnectionAttributeName):
            database.TrustedConnection = reader.ReadContentAsString()

        if reader.MoveToAttribute(UserNameAttributeName):
            database.UserName = reader.ReadContentAsString()

        if reader.MoveToAttribute(PasswordAttributeName):
            database.Password = reader.ReadContentAsString()

        else:
            database.Password = System.Convert.ToBase64String(System.Guid.NewGuid().ToByteArray())

        if reader.MoveToAttribute(CreateOnceAttributeName):

            if reader.ReadContentAsString() == 'true':
                database.CreateOnce = True
                    
            else:
                database.CreateOnce = False

        if reader.MoveToAttribute(DriverAttributeName):
            database.Driver = reader.ReadContentAsString()

        if reader.MoveToAttribute(SourceFilesAttributeName):

            for file in reader.ReadContentAsString().split():
                database.Scripts.append(file)

        reader.MoveToElement()

        depth = reader.Depth

        while reader.Read() and reader.Depth > depth:

            if reader.NodeType == System.Xml.XmlNodeType.Element:

                if reader.LocalName == HooksElementName and reader.NamespaceURI == self.NamespaceUri:
                    self.__ReadHookConfiguration(reader, database)

                if reader.NamespaceURI in Configuration.Modules: 
                    namespaceURI = reader.NamespaceURI
                    handler = Configuration.Modules[namespaceURI]
                    handler.ReadConfiguration(reader, database)

                    database.Modules[namespaceURI] = handler


    def __ReadHookConfiguration(self, reader, database):
        reader.MoveToElement()

        depth = reader.Depth

        while reader.Read() and reader.Depth > depth:

            if reader.NodeType == System.Xml.XmlNodeType.Element:

                if reader.LocalName == HookElementName and reader.NamespaceURI == self.NamespaceUri:

                    hook = DatabaseConfiguration.HookConfiguration()

                    if reader.MoveToAttribute(ExecutableElementName):
                        hook.Executable = reader.ReadContentAsString()

                    if reader.MoveToAttribute(ArgumentsElementName):
                        hook.Arguments = reader.ReadContentAsString()

                    database.Hooks.Add(hook)

    def CreateConnectionString(self, configuration):
        print 'Creating connection string (not implemented) ...'

    def PopulateDatabase(self, configuration):
        print 'Populating database (not implemented) ...'

    def DropDatabase(self, configuration):
        print 'Dropping database (not implemented) ...'

    def BuildDatabase(self, configuration):
        print 'Building database (not implemented) ...'

    def DatabaseExists(self, configuration):
        return False

    def Execute(self, configuration, action):

        if not hasattr(configuration, 'Databases'):
            return

        for database in configuration.Databases:

            if action & Action.SkipDatabase: 
                print 'Skipping database deployment ...'
                return


            if action & Action.DeleteDatabase:

                if self.DatabaseExists(database) == True and database.CreateOnce == True:
                    continue

                self.DropDatabase(database)

            if action & Action.DeployDatabase:

                if self.DatabaseExists(database) == True and database.CreateOnce == True:
                    continue

                self.BuildDatabase(database)
                self.PopulateDatabase(database)

            if action & Action.BuildReleaseBundle:
                releaseLabel = configuration.ReleaseLabel

                for database in configuration.Databases:

                    releaseDirectoryName = '%s-release-%s' % (database.Name, releaseLabel)

                    print 'Building release DB bundle %s' % (releaseDirectoryName)

                    releaseDirectoryInfo = System.IO.DirectoryInfo(releaseDirectoryName)

                    if releaseDirectoryInfo.Exists is True:
                        releaseDirectoryInfo.Delete(True)

                    releaseDirectoryInfo.Create()

                    for encodedScriptPath in database.Scripts:
                        scriptPath = DeployUtilities.ExpandEnvironmentVariables(encodedScriptPath)
                        shutil.copy(scriptPath, releaseDirectoryName) 

                    os.chdir(releaseDirectoryName)

                    DeployUtilities.RunExternalCommand('zip', System.String.Format('-r {0}.zip *', releaseDirectoryName))

                    os.chdir('..')

                    releasesDirectoryInfo = System.IO.DirectoryInfo('releases')

                    if releasesDirectoryInfo.Exists is not True:
                        releasesDirectoryInfo.Create()

                    shutil.move(System.String.Format('{0}/{0}.zip', releaseDirectoryName), 'releases')


    def PrintConfiguration(self, configuration, database = None):

        if not hasattr(configuration, 'Databases'):
            return

        if database == None:

            for database in configuration.Databases:        
                self.__PrintConfiguration(database)
                
                for module in database.Modules.values():
                    module.PrintConfiguration(database)

        else:
            self.__PrintConfiguration(database)


    def __PrintConfiguration(self, database):
        print '>> Database'
        print '    Name:              ' + database.Name
        print '    Server:            ' + database.Server
        print '    User:              ' + database.UserName
        print '    Password:          ' + database.Password
        print '    Once:              ' + str(database.CreateOnce)
        print '    Driver:            ' + database.Driver

        print '    SQL files:'

        for script in database.Scripts:
            print '        SQL file:      ' + DeployUtilities.ExpandEnvironmentVariables(script)

        print '    Hooks:'

        for hook in database.Hooks:
            print '        Hook:              ' + hook.Executable
            print '        Arguments:         ' + hook.Arguments

        print '    Modules:'

        for module in database.Modules.values():
            print '        Module:            ' + str(module)

            module.PrintConfiguration(database)

