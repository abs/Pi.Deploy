#
# (c) Peralta Informatics 2007
# $Id: DeployWebModule.py 299 2008-01-19 08:42:05Z andrei $
#

import clr

clr.AddReference('System.Xml')

import System.IO
import System.Text
import System.Xml

import sys
import os
import shutil
import types
import time
import datetime

from os import path

from Pi.Deploy.DeployAction import Action
from Pi.Deploy.DeployConfiguration import Configuration
from Pi.Deploy.DeployModule import DeployModule
from Pi.Deploy.Web.DeployWebsiteConfiguration import WebsiteConfiguration


DeployWebNamespaceUri                = 'http://schemas.peralta-informatics.com/Deploy/Web/2007'

WebsiteElementName                   = 'Website'
NameAttributeName                    = 'Name'

SourceFilesAttributeName             = 'SourceFiles'
DirectoriesAttributeName             = 'Directories'

TargetServerAttributeName            = 'TargetServer'
TargetPathAttributeName              = 'TargetPath'
TargetRootAttributeName              = 'TargetRoot'
SourceConfigAttributeName            = 'SourceConfig'
SourceRootAttributeName              = 'SourceRoot'

RootElementName                      = 'Root'
BinElementName                       = 'Bin'
DirectoryElementName                 = 'Directory'
ScriptMapsElementName                = 'ScriptMaps'

AddElementName                       = 'Add'
ExtensionAttributeName               = 'Extension'
ScriptProcessorAttributeName         = 'ScriptProcessor'
FlagsAttributeName                   = 'Flags'
IncludedVerbsAttributeName           = 'IncludedVerbs'

AuthenticationElementName            = 'Authentication'
AuthenticationNameAttributeName      = 'Name'
AuthenticationTypeAttributeName      = 'Type'


class DeployWebModule(DeployModule):
    def __init__(self):
        pass

    def ReadConfiguration(self, reader, configuration):
        
        if not hasattr(configuration, 'Websites'):
            configuration.Websites = []

        if reader.NodeType == System.Xml.XmlNodeType.Element: 

            if reader.LocalName == WebsiteElementName and reader.NamespaceURI == DeployWebNamespaceUri:
                website = WebsiteConfiguration()

                configuration.Websites.Add(website)

                self.__ReadWebsiteConfiguration(reader, website)


    def __ReadWebsiteConfiguration(self, reader, website):

        if reader.MoveToAttribute(NameAttributeName):
            website.Name = reader.ReadContentAsString()

        if reader.MoveToAttribute(TargetServerAttributeName):
            website.TargetServer = reader.ReadContentAsString()
            
        if reader.MoveToAttribute(TargetPathAttributeName):
            website.TargetPath = reader.ReadContentAsString()

        if reader.MoveToAttribute(TargetRootAttributeName):
            website.TargetRoot = reader.ReadContentAsString()

        if reader.MoveToAttribute(SourceConfigAttributeName):
            website.SourceConfig = reader.ReadContentAsString()

        if reader.MoveToAttribute(SourceRootAttributeName):
            website.SourceRoot = reader.ReadContentAsString()

        reader.MoveToElement()

        depth = reader.Depth

        while reader.Read() and reader.Depth > depth:

            if reader.NodeType == System.Xml.XmlNodeType.Element:

                if reader.LocalName == ScriptMapsElementName and reader.NamespaceURI == DeployWebNamespaceUri:
                    self.__ReadScriptMaps(reader, website.ScriptMaps)

                if reader.LocalName == RootElementName and reader.NamespaceURI == DeployWebNamespaceUri:
                    self.__ReadRoot(reader, website.RootFiles, website.RootDirectories)
                    
                if reader.LocalName == DirectoryElementName and reader.NamespaceURI == DeployWebNamespaceUri:
                    self.__ReadDirectory(reader, website.DirectoriesDictionary)

                if reader.LocalName == BinElementName and reader.NamespaceURI == DeployWebNamespaceUri:
                    self.__ReadBin(reader, website.BinFiles)
                    
                if reader.LocalName == AuthenticationElementName and reader.NamespaceURI == DeployWebNamespaceUri:
                    self.__ReadAuthenticationConfiguration(reader, website)
                        
                if reader.NamespaceURI in Configuration.Modules: 

                    handler = Configuration.Modules[reader.NamespaceURI]
                    handler.ReadConfiguration(reader, website)

                    website.Modules[reader.NamespaceURI] = handler

                
    def __ReadScriptMap(self, reader):

        scriptMap = WebsiteConfiguration.ScriptMap()

        if reader.MoveToAttribute(ExtensionAttributeName):
            scriptMap.Extension = reader.ReadContentAsString()    
            
        if reader.MoveToAttribute(ScriptProcessorAttributeName):    
            scriptMap.ScriptProcessor = reader.ReadContentAsString()

        if reader.MoveToAttribute(FlagsAttributeName):
            scriptMap.Flags = reader.ReadContentAsString()

        if reader.MoveToAttribute(IncludedVerbsAttributeName):
            scriptMap.IncludedVerbs = reader.ReadContentAsString()

        return scriptMap


    def __ReadScriptMaps(self, reader, scriptMapsList):

        depth = reader.Depth

        while reader.Read() and reader.Depth > depth:

            if reader.NodeType == System.Xml.XmlNodeType.Element:

                if reader.LocalName == AddElementName and reader.NamespaceURI == DeployWebNamespaceUri:
                    
                    scriptMapsList.append(ReadScriptMap(reader))
        
    def __ReadRoot(self, reader, files, directories):

        if reader.MoveToAttribute(SourceFilesAttributeName):
            for file in reader.ReadContentAsString().split():
                files.append(file)

        if reader.MoveToAttribute(DirectoriesAttributeName):
            for directory in reader.ReadContentAsString().split():
                directories.append(directory)

    def __ReadBin(self, reader, list):

        if reader.MoveToAttribute(SourceFilesAttributeName):
            for file in reader.ReadContentAsString().split():
                list.append(file)

    def __ReadAuthenticationConfiguration(self, reader, website):
        website.Authentication = WebsiteConfiguration.AuthenticationConfiguration()

        if reader.MoveToAttribute(WebAuthenticationNameAttributeName):
            website.Authentication.Name = reader.ReadContentAsString()

        if reader.MoveToAttribute(WebAuthenticationTypeAttributeName):
            website.Authentication.Type = reader.ReadContentAsString()
                    

    def DeleteWebsite(self, website):
        print 'Deleting website ...'

        targetRootDirectory = System.IO.DirectoryInfo('%s/%s' % (website.TargetPath, website.ApplicationName))

        if targetRootDirectory.Exists is True:
            targetRootDirectory.Delete(True)

            print 'Deleting %s' % (targetRootDirectory.FullPath)


    def CreateWebsite(self, website):
        print 'Creating website ...'


    def CreateWebConfig(self, website):
        if website.SourceConfig is None: return None

        print 'Creating Web.config file for %s on %s' % (website.ApplicationName, website.TargetPath)

        try:
            webConfigDocument = System.Xml.XmlDocument()
            webConfigDocument.Load('%s/%s' % (website.SourceRoot, website.SourceConfig))

            connectionStringsNode = webConfigDocument.SelectSingleNode('/configuration/connectionStrings')

            if connectionStringsNode is not None:

                for database in website.Databases:

                    for module in website.Modules.values():
                        
                        if hasattr(module, 'CreateConnectionString'):
                            addElement = webConfigDocument.CreateElement('add')
                            addElement.SetAttribute('name', '%s' % (database.Name))
                            addElement.SetAttribute('connectionString', module.CreateConnectionString(database))

                            connectionStringsNode.AppendChild(webConfigDocument.ImportNode(addElement, False))

            for module in website.Modules.values():
                module.CreateWebConfigSections(webConfigDocument, website)

            return webConfigDocument

        except:
            raise

            
    def RecycleAppPool(self, website):
        print 'Recycling app pool ...'


    def __CopyDirectory(self, directory, targetDirectory):

        if directory.Name == '.svn':
            return
        
        print "Copying '%s' directory to '%s'" % (directory.FullPath, targetDirectory.FullPath)


        if targetDirectory.Exists is not True:
            targetDirectory.Create()

        for file in directory.GetFiles():
            file.CopyTo('%s/%s' % (targetDirectory.FullPath, file.Name), True)

        for file in targetDirectory.GetFiles():
            file.Attributes = System.IO.FileAttributes.Normal

        for subdirectoryInfo in directory.GetDirectories():
            subdirectory = '%s/%s' % (directory, subdirectoryInfo.Name)
            targetSubdirectory = '%s/%s' % (targetDirectory, subdirectoryInfo.Name)

            self.__CopyDirectory(System.IO.DirectoryInfo(subdirectory), System.IO.DirectoryInfo(targetSubdirectory))


    def CopyFiles(self, website):
        try:
            sourceRootDirectory = System.IO.DirectoryInfo(website.SourceRoot)

            if sourceRootDirectory.Exists is not True:
                print 'Directory %s does not exist.' % (website.SourceRoot)
                raise
            
            print "Copying '%s' files to '%s'" % (website.ApplicationName, website.TargetPath)

            targetRootDirectory = System.IO.DirectoryInfo('%s/%s' % (website.TargetPath, website.ApplicationName))
            targetBinDirectory = System.IO.DirectoryInfo('%s/bin' % (targetRootDirectory.FullName))

            if targetRootDirectory.Exists is True:
                targetRootDirectory.Delete(True)

            if targetRootDirectory.Exists is not True:
                targetRootDirectory.Create()

            if targetBinDirectory.Exists is not True:
                targetBinDirectory.Create()

            for sourceFileName in website.RootFiles:
                file = System.IO.FileInfo('%s/%s' % (website.SourceRoot, sourceFileName))
                file.CopyTo('%s/%s' % (targetRootDirectory.FullPath, sourceFileName), True)
                print "Copying '%s'" % (file.Name)

            for file in targetRootDirectory.GetFiles():
                file.Attributes = System.IO.FileAttributes.Normal

            for sourceFileName in website.BinFiles:
                file = System.IO.FileInfo('%s/bin/%s' % (website.SourceRoot, sourceFileName))
                file.CopyTo('%s/%s' % (targetBinDirectory.FullPath, sourceFileName), True)
                print "Copying '%s'" % (file.Name)

            for file in targetBinDirectory.GetFiles():
                file.Attributes = System.IO.FileAttributes.Normal

            for directoryName in website.RootDirectories:
                directory = System.IO.DirectoryInfo('%s/%s' % (website.SourceRoot, directoryName))
                targetDirectory = System.IO.DirectoryInfo('%s/%s' % (targetRootDirectory, path.basename(directoryName)))

                self.__CopyDirectory(directory, targetDirectory)

            for directoryName, files in website.DirectoriesDictionary.iteritems():
                directory = System.IO.DirectoryInfo('%s/%s' % (website.SourceRoot, directoryName))
                targetDirectory = System.IO.DirectoryInfo('%s/%s' % (targetRootDirectory, path.basename(directoryName)))

                print "Copying '%s' directory to '%s'" % (directory.FullPath, targetDirectory.FullPath)

                if targetDirectory.Exists is not True:
                    targetDirectory.Create()

                for fileName in files:
                    fileInfo = System.IO.FileInfo('%s/%s' % (directory.FullName, fileName))

                    fileInfo.CopyTo('%s/%s' % (targetDirectory.FullPath, fileInfo.Name), True)
                    print "Copying '%s' to '%s'" % (fileInfo.FullPath, targetDirectory.FullPath)

        except:
            raise


    def WriteWebConfig(self, webConfigDocument, website):
        print 'Writing web config ...'

        xmlWriterSettings = System.Xml.XmlWriterSettings()

        xmlWriterSettings.Indent = True
        xmlWriterSettings.OmitXmlDeclaration = True
        xmlWriterSettings.NewLineOnAttributes = True

        xmlWriterSettings.NewLineHandling = System.Xml.NewLineHandling.None

        xmlWriter = System.Xml.XmlWriter.Create('%s/Web.config' % (website.SourceRoot), xmlWriterSettings)

        webConfigDocument.Save(xmlWriter)
        xmlWriter.Flush()

        xmlWriter = System.Xml.XmlWriter.Create('%s/%s/Web.config' % (website.TargetPath, website.ApplicationName), xmlWriterSettings)

        webConfigDocument.Save(xmlWriter)
        xmlWriter.Flush()


    def Execute(self, configuration, action):
        try:

            if not hasattr(configuration, 'Websites'):
                return

            for website in configuration.Websites:
    
                if action & Action.DeleteWebsite:
                    self.DeleteWebsite(website)

                if action & Action.PushFiles:
                    self.CopyFiles(website)

                if action & Action.UpdateWebConfig or action & Action.CreateWebsite:
                    webConfigDocument = self.CreateWebConfig(website)

                    if webConfigDocument != None:
                        self.WriteWebConfig(webConfigDocument, website)

                    else:
                        print 'Web.config is None'

                if action & Action.CreateWebsite:
                    self.CreateWebsite(website)

                if action & Action.UpdateWebConfig:
                    self.RecycleAppPool(website)
                
                for module in website.Modules.values():
                    module.Execute(website, action)

        except System.Exception, e:
            print e
            raise


    def PrintConfiguration(self, configuration):

        for website in configuration.Websites:

            print '>> Website'
            print '    Name:              ' + website.Name
            print '    Application:       ' + website.ApplicationName

            print '    Assembly:          ' + website.Assembly
            print '    Type:              ' + website.Type

            print '    Target Server:     ' + website.TargetServer
            print '    Target Path:       ' + website.TargetPath
            print '    Target Root:       ' + website.TargetRoot
            print '    Source Config:     ' + website.SourceConfig
            print '    Source Root:       ' + website.SourceRoot

            print '    Root files:'
            for file in website.RootFiles:
                print '        Root file:         ' + file

            print '    Directories:'
            for directory in website.RootDirectories:
                print '        Directory:         ' + path.basename(directory)

            print '    Bin files:'

            for file in website.BinFiles:
                print '        Bin file:          ' + file

            if len(website.ScriptMaps) > 0:
                print '>> Script Maps'

                for scriptMap in website.ScriptMaps:

                    print '    Extension:           ' + scriptMap.Extension
                    print '    Script Processor:    ' + scriptMap.ScriptProcessor
                    print '    Flags:               ' + scriptMap.Flags
                    print '    Included Verbs       ' + scriptMap.IncludedVerbs

            if website.Authentication is not None:
                print '>> Authentication'
                print '    Name:              ' + website.Authentication.Name
                print '    Type:              ' + website.Authentication.Type

            if len(website.DirectoriesDictionary) > 0:
                print '>> Directories'

                for directoryName, files in website.DirectoriesDictionary.iteritems():
                    print '    Name:          ' + directoryName

                    print '    Files'

                    for file in files:
                        print '        File:          ' + file

            print '    Modules:'

            for module in website.Modules.values():
                print '        Module            ' + str(module)

                module.PrintConfiguration(website)

