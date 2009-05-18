#
# (c) Peralta Informatics 2007
# $Id: Deploy.py 133 2007-12-21 00:12:22Z andrei $
#

import clr
import imp
import getopt
import new
import os
import shutil
import string
import sys
import traceback

from os import path

clr.AddReference('System.Xml')

import System.Collections.Generic
import System.Text
import System.Xml

PI_DEPLOY_HOME=os.environ.get('PI_DEPLOY_HOME')
sys.path.append(os.path.join('PI_DEPLOY_HOME', 'Pi'))

from Pi.Deploy import DeployUtilities
from Pi.Deploy import DeployModule

from Pi.Deploy.DeployAction import Action
from Pi.Deploy.DeployConfiguration import Configuration

DeployNamespaceUri                      = 'http://schemas.peralta-informatics.com/Deploy/2007'

DepModulesElementName                   = 'Modules'
DepModuleElementName                    = 'Module'
DepNamespaceAttributeName               = 'Namespace'
DepImportAttributeName                  = 'Import'
DepHandlerAttributeName                 = 'Handler' 
DepNameAttributeName                    = 'Name'

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
            components = moduleName.split('.')
            name = components[len(components) - 1]
            sep = moduleName.replace('.', '/').rfind('/')

            moduleInfo = imp.find_module(name, [os.path.join(PI_DEPLOY_HOME, moduleName.replace('.', '/')[0:sep]), '.'])

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
    configuration = Configuration()

    reader = System.Xml.XmlReader.Create(configurationFile)

    depth = reader.Depth

    while reader.Read():

        if reader.NodeType == System.Xml.XmlNodeType.Element: 

            if reader.LocalName == DepModulesElementName and reader.NamespaceURI == DeployNamespaceUri:
                ReadModules(reader, configuration.Modules)

            if reader.NamespaceURI in configuration.Modules:
                configuration.Modules[reader.NamespaceURI].ReadConfiguration(reader, configuration)

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
    print 'ipy Deploy.py <configuration file> Deploy [--skip-database] [--only-me={deployment name}]'
    print 'ipy Deploy.py <configuration file> DeployDatabase'
    print 'ipy Deploy.py <configuration file> UpdateWebConfig'
    print 'ipy Deploy.py <configuration file> DeleteWebsite'
    print 'ipy Deploy.py <configuration file> PushFiles'
    print 'ipy Deploy.py <configuration file> BuildReleaseBundle <--release-label={your label (e.g. use svn revision number)}>'
    print 'ipy Deploy.py <configuration file> Info'
    print 'ipy Deploy.py <configuration file> Help'

    if configuration is not None:

        for handler in configuration.Modules.values():
            handler.PrintHelp()
    
    sys.exit(2)


def ParseArguments():
    action = Action()

    action.Workflow = Action.Empty

    actionString = None

    if len(sys.argv) < 2:
        raise System.Exception('Parameter missing: path to configuration file.')

    if len(sys.argv) >= 3:
        actionString = sys.argv[2]

        if len(actionString) == 0:
            action.Workflow |= Action.Help

    if len(sys.argv) >= 4:

        try:
            options, theirValues = getopt.getopt(sys.argv[3:], 'h', ['skip-database', 'only-me=', 'help', 'release-label='])

            for o, a in options:
                
                if o in ('-h', '--help'):
                    __PrintHelp()

                elif o == '--skip-database':
                    action.Workflow |= Action.SkipDatabase

                elif o == '--only-me':
                    action.Workflow |= Action.OnlyMe
                    action.Name = a

                elif o == '--release-label':
                    action.ReleaseLabel = a

        except getopt.GetoptError, error:
            print str(error)
            __PrintHelp()

    if actionString == 'Help':
        action.Workflow |= Action.Help

    if actionString == 'DeployDatabase' or actionString == 'Deploy':
        action.Workflow |= Action.DeleteDatabase
        action.Workflow |= Action.DeployDatabase

    if actionString == 'DeleteDatabase':
        action.Workflow |= Action.DeleteDatabase

    if actionString == 'Deploy': 
        action.Workflow |= Action.DeleteWebsite
        action.Workflow |= Action.CreateWebsite
        action.Workflow |= Action.PushFiles
        action.Workflow |= Action.UpdateWebConfig

    if actionString == 'UpdateWebConfig':
        action.Workflow |= Action.UpdateWebConfig

    if actionString == 'DeleteWebsite':
        action.Workflow |= Action.DeleteWebsite

    if actionString == 'PushFiles':
        action.Workflow |= Action.PushFiles
    
    if actionString == 'BuildReleaseBundle':
        action.Workflow |= Action.BuildReleaseBundle

        if not hasattr(action, 'ReleaseLabel'):
            print 'Parameter missing: --release-label.'
            __PrintHelp()

    if actionString == 'Info':
        action.Workflow |= Action.Info

    return action


def main():
    try:
        action = ParseArguments()

        configuration = ReadConfiguration(sys.argv[1])

        if action.Workflow == Action.Empty or action.Workflow & Action.Help:
            __PrintHelp(configuration)
            return

        if action.Workflow & Action.Info:
            __PrintConfiguration(configuration)

        if action.Workflow & Action.BuildReleaseBundle:
            configuration.ReleaseLabel = action.ReleaseLabel

        for namepsace, handler in configuration.Modules.iteritems():
            handler.Execute(configuration, action)

    except Exception, e:
        print 'python exception:'
    
        exception = traceback.format_exc()

        print exception
    
        return 1

    except System.Exception, e:
        print 'System.Exception'

        return 1

if __name__ == '__main__':
    sys.exit(main())

