#
# (c) Peralta Informatics 2007
# $Id: DeployUtilities.py 227 2008-01-01 00:13:21Z andrei $
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


def RunExternalCommand(command, arguments, environmentVariables = None):

    print 'Running %s %s' % (command, arguments)

    process = System.Diagnostics.Process()
    process.StartInfo.FileName = command
    process.StartInfo.Arguments = arguments

    if environmentVariables is not None:
        process.StartInfo.UseShellExecute = False

        for name, value in environmentVariables.iteritems():
            process.StartInfo.EnvironmentVariables[name] = value

    process.StartInfo.WindowStyle = System.Diagnostics.ProcessWindowStyle.Hidden

    process.Start()
    process.WaitForExit()
    process.Close()


def ExpandEnvironmentVariables(encodedString):

    for environmentVariable in encodedString.split('%'):
        
        environmentVariableValue = os.environ.get(environmentVariable)

        if environmentVariableValue is not None:
            encodedString = encodedString.replace('%%%s%%' % (environmentVariable), environmentVariableValue)
    
    return encodedString.replace('\\', '/')

