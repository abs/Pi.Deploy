#
# (c) Peralta Informatics 2007
# $Id: DeployMsSqlModule.py 33 2007-12-10 18:42:18Z andrei $
#

import clr
import sys
import os
import shutil
import re

clr.AddReference("System.Data")
clr.AddReference("System.Xml")

import System.Data
import System.Data.SqlClient
import System.Diagnostics
import System.Text
import System.Xml

from Pi.Deploy.Database.DeployDatabaseModule import DeployDatabaseModule
from Pi.Deploy import DeployUtilities


class DeployMsSqlModule(DeployDatabaseModule):
    
    def __init__(self):
        pass


    def __GetNamespaceUri(self):
        return 'http://schemas.peralta-informatics.com/Deploy/Sql/MsSql/2007'

    
    NamespaceUri = property(__GetNamespaceUri)


    def CreateConnectionString(self, configuration):
        connectionString = System.String.Format("Server={0};Database={1}", configuration.Server, configuration.Name)

        if hasattr(configuration, 'IntegratedSecurity'):
            connectionString = System.String.Format("{0};Integrated Security='{1}'", connectionString, configuration.IntegratedSecurity)

        if hasattr(configuration, 'TrustedConnection'):
            connectionString = System.String.Format("{0};Trusted_Connection={1}", connectionString, configuration.TrustedConnection)
        
        if hasattr(configuration, 'ApplicationName'):
            connectionString = System.String.Format("{0};Application Name={1}", connectionString, configuration.ApplicationName)

        connectionString = System.String.Format("{0};", connectionString)

        return connectionString


    def DatabaseExists(self, configuration):
        exists = False

        connection = System.Data.SqlClient.SqlConnection()
        connection.ConnectionString = "Integrated Security=SSPI;Database=master;Server=%s" % (configuration.Server)

        try:
            connection.Open()

            try:
                command = connection.CreateCommand()

                command.CommandText = "select * from sys.databases where name = N'%s'" % (configuration.Name)

                exists = command.ExecuteScalar()

                if exists != None:
                    exists = True

            except Exception, detail:
                print detail
                command.Dispose()
                raise
            
            else:
                command.Dispose()
            
        except:
            raise

        else:
            connection.Close()

        return exists


    def DropDatabase(self, configuration):

        for hook in configuration.Hooks:

            if hook.BeforeDrop is True:

                try:
                    arguments = '%s "%s"' % (hook.Arguments, configuration.ConnectionString)
                    DeployUtilities.RunExternalCommand(hook.Executable, arguments)

                except System.ComponentModel.Win32Exception:
                    print 'Could not open "%s".' % (hook.Executable)
                    raise

                else:
                    print 'Ran hook [%s %s "%s"]' % (hook.Executable, hook.Arguments, configuration.ConnectionString)
        
        connection = System.Data.SqlClient.SqlConnection()
        connection.ConnectionString = "Integrated Security=SSPI;Database=master;Server=%s" % (configuration.Server)

        try:
            connection.Open()

            try:
                command = connection.CreateCommand()

                commandText = []
                commandText.append("if exists (select * from sys.databases where name = N'%s') " % (configuration.Name))
                commandText.append("drop database %s" % (configuration.Name))

                command.CommandText = ''.join(commandText)

                command.ExecuteNonQuery()

                print 'Dropping database %s on %s' % (configuration.Name, configuration.Server)

            except Exception, detail:
                print detail
                command.Dispose()
                raise
            
            else:
                command.Dispose()
            
        except System.Exception, e:
            print e
            raise

        else:
            connection.Close()


    def BuildDatabase(self, configuration):
        connection = System.Data.SqlClient.SqlConnection()
        connection.ConnectionString = "Integrated Security=SSPI;Database=master;Server=%s" % (configuration.Server)

        commands = []
        command = []

        command.append("if not exists (select * from sys.databases where name = N'%s') " % (configuration.Name))
        command.append("create database [%s]" % (configuration.Name))
        commands.append(''.join(command))
        command[:] = [] 

        command.append("use [%s]" % (configuration.Name))
        commands.append(''.join(command))
        command[:] = []


        builder = System.Text.StringBuilder()
    #
    #    builder.AppendFormat("if not exists (select * from sys.server_principals where name = N'{0}')", configuration.Database.UserName)
    #    builder.AppendFormat("create login [{0}] with password = N'{1}' else alter login [{0}] with password = N'{1}'", configuration.Database.UserName, configuration.Database.Password)
    #    commands.append(builder.ToString())
    #
    #    builder.Length = 0
    #
    #    builder.AppendFormat("if not exists (select * from [{0}].sys.database_principals where name = N'{1}')", configuration.Database.Name, configuration.Database.UserName)
    #    builder.AppendFormat("create user [{0}] for login [{0}]", configuration.Database.UserName)
    #    commands.append(builder.ToString())
    #

        builder.Length = 0

        # builder.AppendFormat("execute sp_addrolemember N'db_owner', N'{0}'", configuration.Database.UserName)
        builder.AppendFormat("execute sp_addrolemember N'db_owner', N'{0}'", 'NT AUTHORITY\NETWORK SERVICE')
        commands.append(builder.ToString())

        try:
            connection.Open()

            for command in commands:
                try:
                    dbCommand = connection.CreateCommand()
                    dbCommand.CommandText = command
                    dbCommand.ExecuteNonQuery()

                except Exception, detail:
                    dbCommand.Dispose()
                    raise
                    
                else:
                    dbCommand.Dispose()

        except:
            raise

        else:
            print 'Creating database %s on %s' % (configuration.Name, configuration.Server)
            connection.Close()


    def PopulateDatabase(self, configuration):
        connection = System.Data.SqlClient.SqlConnection()
        connection.ConnectionString = "Integrated Security=SSPI;Database=master;Server=%s" % (configuration.Server)

        try:
            connection.Open()

            goRegexp = re.compile(r'^go[ \t]*\n', re.IGNORECASE | re.MULTILINE | re.UNICODE)            

            for encodedScriptPath in configuration.Scripts:

                scriptPath = DeployUtilities.ExpandEnvironmentVariables(encodedScriptPath)

                print 'Running %s ...' % (scriptPath)

                f = open(scriptPath)

                try:
                    normalizedText = goRegexp.sub('go\n', f.read())

                    sql = 'use %s\ngo\n%s' % (configuration.Name, normalizedText)

                    for sqlCommand in goRegexp.split(sql):

                        if len(sqlCommand.strip()) != 0:

                            try:
                                # print 'DEBUG: %s' % (sqlCommand)
                                command = connection.CreateCommand()
                                command.CommandText = sqlCommand 
                                command.ExecuteNonQuery()

                            finally:
                                command.Dispose()

                finally:
                    f.close()

            for hook in configuration.Hooks:

                if hook.BeforeDrop is False:

                    try:
                        arguments = '%s "%s"' % (hook.Arguments, configuration.ConnectionString)
                        DeployUtilities.RunExternalCommand(hook.Executable, arguments)

                    except System.ComponentModel.Win32Exception:
                        print 'Could not open "%s".' % (hook.Executable)
                        raise

                    else:
                        print 'Ran hook "%s %s %s"' % (hook.Executable, configuration.ConnectionString, hook.Arguments)

            for module in configuration.Modules.values():
                module.PopulateDatabase(configuration)

        except Exception, detail:
            print detail
            raise

        else:
            print 'Populated database %s on %s' % (configuration.Name, configuration.Server)
            connection.Close()
