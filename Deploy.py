#
# (c) Peralta Informatics 2007
# $Id: Deploy.py 133 2007-12-21 00:12:22Z andrei $
#

import clr
import sys
import os
import shutil
import imp
import new
import string

from os import path

clr.AddReference('System.Xml')

import System.Collections.Generic
import System.Text
import System.Xml

sys.path.append("Deploy")

import DeployUtilities
import DeployModule

from DeployAction import Action
from DeployConfiguration import Configuration


DeployNamespaceUri                      = 'http://schemas.peralta-informatics.com/Deploy/2007'

DepModulesElementName                   = 'Modules'
DepModuleElementName                    = 'Module'
DepNamespaceAttributeName               = 'Namespace'
DepImportAttributeName                  = 'Import'
DepHandlerAttributeName                 = 'Handler' 


def ReadModule(reader, modules):
    
    namespace = None
    handler = None

    if reader.MoveToAttribute(DepNamespaceAttributeName):
        namespace = reader.ReadContentAsString()

    if reader.MoveToAttribute(DepHandlerAttributeName):
        handler = reader.ReadContentAsString()

    if handler is not None and namespace is not None:

        if reader.MoveToAttribute(DepImportAttributeName):
            
            moduleName = reader.ReadContentAsString()
            moduleInfo = imp.find_module(moduleName)

            module = imp.load_module(moduleName, moduleInfo[0], moduleInfo[1], moduleInfo[2])

            deployModuleType = type('%sHandler' % (handler), (getattr(module, handler),), {})

            if issubclass(deployModuleType, DeployModule.DeployModule):

                modules[namespace] = deployModuleType()

            else:
                raise Exception('%s.%s does not implement DeployModule interface.' % (moduleName, handler))

    else:
        raise Exception('%s error: %s or %s were not specified' % (DepModuleElementName, DepNamespaceAttributeName, DepHandlerAttributeName))
    

def ReadModules(reader, modules):

    depth = reader.Depth

    while reader.Read() and reader.Depth > depth:

        if reader.NodeType == System.Xml.XmlNodeType.Element:

            if reader.LocalName == DepModuleElementName and reader.NamespaceURI == DeployNamespaceUri:
                ReadModule(reader, modules)
                

def ReadConfiguration(configurationFile):
    try:
        configuration = Configuration()

        reader = System.Xml.XmlReader.Create(configurationFile)

        depth = reader.Depth

        while reader.Read():

            if reader.NodeType == System.Xml.XmlNodeType.Element: 

                if reader.LocalName == DepModulesElementName and reader.NamespaceURI == DeployNamespaceUri:
                    ReadModules(reader, configuration.Modules)

                if reader.NamespaceURI in configuration.Modules:
                    configuration.Modules[reader.NamespaceURI].ReadConfiguration(reader, configuration)

    except Exception, e:
        raise e

    except System.Exception, e:
        raise e

    return configuration


def __PrintConfiguration(configuration):

    if len(configuration.Modules) > 0:
        print '>> Modules'

        for namespace, handler in configuration.Modules.iteritems():
            print '    Namespace:         ' + namespace
            print '    Handler:           ' + str(handler)

        for namespace, handler in configuration.Modules.iteritems():
            handler.PrintConfiguration(configuration)


def __PrintHelp(configuration = None):
    print ''
    print 'Command line options:'
    print 'ipy Deploy.py <configuration file> Deploy [--skip-database]'
    print 'ipy Deploy.py <configuration file> DeployDatabase'
    print 'ipy Deploy.py <configuration file> UpdateWebConfig'
    print 'ipy Deploy.py <configuration file> DeleteWebsite'
    print 'ipy Deploy.py <configuration file> PushFiles'
    print 'ipy Deploy.py <configuration file> BuildReleaseBundle <release label>'
    print 'ipy Deploy.py <configuration file> Info'
    print 'ipy Deploy.py <configuration file> Help'

    if configuration is not None:

        for handler in configuration.Modules.values():
            handler.PrintHelp()
        

def ParseArguments():
    action = Action.Empty

    actionString = None

    if len(sys.argv) < 2:
        raise System.Exception('Parameter missing: path to configuration file.')

    if len(sys.argv) >= 3:
        actionString = sys.argv[2]

        if len(actionString) == 0:
            action |= Action.Help

    for arg in sys.argv:
        if arg == '--skip-database':
            action |= Action.SkipDatabase

    if actionString == 'Help':
        action |= Action.Help

    if actionString == 'DeployDatabase' or actionString == 'Deploy':
        action |= Action.DeleteDatabase
        action |= Action.DeployDatabase

    if actionString == 'DeleteDatabase':
        action |= Action.DeleteDatabase

    if actionString == 'Deploy': 
        action |= Action.DeleteWebsite
        action |= Action.CreateWebsite
        action |= Action.PushFiles
        action |= Action.UpdateWebConfig

    if actionString == 'UpdateWebConfig':
        action |= Action.UpdateWebConfig

    if actionString == 'DeleteWebsite':
        action |= Action.DeleteWebsite

    if actionString == 'PushFiles':
        action |= Action.PushFiles
    
    if actionString == 'BuildReleaseBundle':
        action |= Action.BuildReleaseBundle

    if actionString == 'Info':
        action |= Action.Info


    return action


def main():
    try:
        action = ParseArguments()

        configuration = ReadConfiguration(sys.argv[1])

        if action == Action.Empty or action & Action.Help:
            __PrintHelp(configuration = configuration)
            return

        if action & Action.Info:
            __PrintConfiguration(configuration)

        if action & Action.BuildReleaseBundle:
            pass

        for namepsace, handler in configuration.Modules.iteritems():
            handler.Execute(configuration, action)

    except Exception, e:
        print e

        __PrintHelp()

        return 1

    except System.Exception, e:
        print e

        return 1

if __name__ == '__main__':
    sys.exit(main())

