#
# (c) Peralta Informatics 2007
# $Id: DeployIisModule.py 299 2008-01-19 08:42:05Z andrei $
#

import clr
import sys
import os
import shutil
import types
import time
import datetime

from os import path

clr.AddReference("System.Data")
clr.AddReference("System.Xml")
clr.AddReference("System.DirectoryServices")

import System.Data
import System.Data.SqlClient
import System.DirectoryServices
import System.IO
import System.Text
import System.Xml

from Pi.Deploy.Web.DeployWebModule import DeployWebModule


class DeployIisModule(DeployWebModule):

    def __init__(self):
        pass


    def CreateWebConfig(self, website):

        if website.SourceConfig is None: return None

        print 'Creating Web.config file for %s on %s' % (website.ApplicationName, website.TargetPath)

        try:
            webConfigDocument = System.Xml.XmlDocument()
            webConfigDocument.Load('%s\\%s' % (website.SourceRoot, website.SourceConfig))

            connectionStringsNode = webConfigDocument.SelectSingleNode('/configuration/connectionStrings')

            if connectionStringsNode is not None:
                addElement = webConfigDocument.CreateElement('add')

                addElement.SetAttribute('name', '%s' % (website.Databases[0].Name))

                addElement.SetAttribute('connectionString', System.String.Format("Server={0};Database={1};Integrated Security='SSPI';", website.Databases[0].Server, website.Databases[0].Name))

                connectionStringsNode.AppendChild(webConfigDocument.ImportNode(addElement, False))

            for module in website.Modules.values():
                module.CreateWebConfigSections(webConfigDocument, website.Databases)

            return webConfigDocument

        except:
            raise


    def __GetSpacedStringFromList(self, list):
        filesStringList = []

        for file in list:

            if len(filesStringList) != 0:
                filesStringList.append(' ')

            filesStringList.append(file)

        return ''.join(filesStringList)         


    def __FindByName(self, entries, name):

        try:
            for entry in entries:
                if entry.Name.Equals(name):
                    return entry

        except:
            pass
            
        return None


    def __FindWebsiteByName(self, server, name):

        root = System.DirectoryServices.DirectoryEntry(System.String.Format("IIS://{0}/W3SVC", server))

        for entry in root.Children:

            if entry.Name.isdigit() and entry.Properties["ServerComment"].Value.Equals(name):
                return entry.Name

        raise Exception('Could not find %s' % (name))


    def DeleteApplication(self, website):
        print "Deleting '%s' IIS application on '%s'" % (website.ApplicationName, website.TargetServer)

        websiteName = self.__FindWebsiteByName(website.TargetServer, 'Default Web Site')

        root = System.DirectoryServices.DirectoryEntry(System.String.Format("IIS://{0}/W3SVC/{1}/ROOT", website.TargetServer, websiteName))

        application = self.__FindByName(root.Children, website.ApplicationName)
        
        if application is not None:
            application.Invoke("AppDelete")
            application = root.Invoke("Delete", "IISWebVirtualDir", website.ApplicationName)

        appPools = System.DirectoryServices.DirectoryEntry(System.String.Format("IIS://{0}/W3SVC/AppPools", website.TargetServer))

        if appPools is not None and appPools.Children is not None:

            appPool = self.__FindByName(appPools.Children, website.ApplicationName)

            if appPool is not None:
                print 'Deleting %s application pool on %s ...' % (website.ApplicationName, website.TargetServer)
                appPool.Invoke('Delete', 'IISApplicationPool', website.ApplicationName)
                    

    def RecycleAppPool(self, website):
        print "Recycling '%s' IIS app pool on '%s'" % (website.ApplicationName, website.TargetServer)

        appPools = System.DirectoryServices.DirectoryEntry(System.String.Format("IIS://{0}/W3SVC/AppPools", website.TargetServer))

        if appPools is not None and appPools.Children is not None:

            appPool = self.__FindByName(appPools.Children, website.ApplicationName)

            if appPool is not None:
                appPool.Invoke('Recycle')
                print 'Recycling %s app pool ...' % (website.ApplicationName)


    def CreateApplication(self, website):
        print "Creating '%s' as an IIS application on '%s' ..." % (website.ApplicationName, website.TargetServer)

        websiteName = self.__FindWebsiteByName(website.TargetServer, 'Default Web Site')

        root = System.DirectoryServices.DirectoryEntry(System.String.Format("IIS://{0}/W3SVC/{1}/ROOT", website.TargetServer, websiteName))

        application = self.__FindByName(root.Children, website.ApplicationName)
        
        if application is None:
            application = root.Invoke("Create", "IISWebVirtualDir", website.ApplicationName)
            application.Invoke("AppCreate3", 2, website.ApplicationName, True)

        application.InvokeSet("Path", "%s\\%s" % (website.TargetRoot, website.ApplicationName))
        application.Invoke("SetInfo")

        if len(website.ScriptMaps) > 0:

            for property in application.Properties:

                if property.PropertyName == 'ScriptMaps':

                    for scriptMap in website.ScriptMaps:

                        scriptMapValue = '%s,%s,%s,%s' % (scriptMap.Extension, scriptMap.ScriptProcessor, scriptMap.Flags, scriptMap.IncludedVerbs)

                        print 'Adding %s ...' % (scriptMapValue)

                        property.Add(scriptMapValue)

                        application.Invoke("SetInfo")

                    break




