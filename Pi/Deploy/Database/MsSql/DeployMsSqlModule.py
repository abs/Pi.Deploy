#
# (c) Peralta Informatics 2007
# $Id: DeployMsSqlModule.py 33 2007-12-10 18:42:18Z andrei $
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


from Deploy.DeployDatabaseModule import DeployDatabaseModule


class DeployMsSqlModule(DeployDatabaseModule):
    
    def __init__(self):
        pass


    def DatabaseExists(configuration):
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


    def DropDatabase(configuration):
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


    def BuildDatabase(configuration):
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


    def PopulateDatabase(configuration):
        connection = System.Data.SqlClient.SqlConnection()
        connection.ConnectionString = "Integrated Security=SSPI;Database=master;Server=%s" % (configuration.Server)

        try:
            connection.Open()

            for encodedScriptPath in configuration.Scripts:

                scriptPath = DeployUtilities.ExpandEnvironmentVariables(encodedScriptPath)

                print 'Running %s ...' % (scriptPath)

                try:
                    f = open(scriptPath)

                    sql = ('use %s\ngo\n' % (configuration.Name)) + f.read()

                    for sqlCommand in sql.split('\ngo\n'):
                        try:
                            # print 'DEBUG: %s' % (sqlCommand)
                            command = connection.CreateCommand()
                            command.CommandText = sqlCommand 
                            command.ExecuteNonQuery()

                        finally:
                            command.Dispose()

                finally:
                    f.close()

                connectionString = System.String.Format("\"Server={0};Database={1};Integrated Security='SSPI';\"", configuration.Server, configuration.Name)

                for hook in configuration.Hooks:

                    process = System.Diagnostics.Process()
                    process.StartInfo.FileName = hook.Executable
                    process.StartInfo.Arguments = hook.Arguments + ' ' + connectionString

                    process.Start()
                    process.WaitForExit()
                    process.Close()

                    print connectionString

            for module in configuration.Modules:
                module.PopulateDatabase(configuration)

        except Exception, detail:
            print detail
            raise

        else:
            print 'Populating database %s on %s' % (configuration.Name, configuration.Server)
            connection.Close()


