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

    print 'Starting external program: [%s] [%s]' % (command, arguments)

    startInfo = System.Diagnostics.ProcessStartInfo()
    startInfo.FileName = command
    startInfo.Arguments = arguments
    startInfo.UseShellExecute = False
    startInfo.ErrorDialog = False
    startInfo.CreateNoWindow = True
    startInfo.RedirectStandardOutput = True
    startInfo.RedirectStandardError = True

    if environmentVariables is not None:

        for name, value in environmentVariables.iteritems():
            startInfo.EnvironmentVariables[name] = value

    process = System.Diagnostics.Process.Start(startInfo)

    stdoutCharacterAsInteger = process.StandardOutput.Read()

    while stdoutCharacterAsInteger != -1:
        sys.stdout.write(chr(stdoutCharacterAsInteger))
        stdoutCharacterAsInteger = process.StandardOutput.Read()

    errorOutputReader = process.StandardError
    errorOutput = errorOutputReader.ReadToEnd()

    process.WaitForExit()
    process.Close()

    if len(errorOutput) != 0:
        print errorOutput


def ExpandEnvironmentVariables(encodedString):

    for environmentVariable in encodedString.split('%'):
        
        environmentVariableValue = os.environ.get(environmentVariable)

        if environmentVariableValue is not None:
            encodedString = encodedString.replace('%%%s%%' % (environmentVariable), environmentVariableValue)
    
    return encodedString.replace('\\', '/')
