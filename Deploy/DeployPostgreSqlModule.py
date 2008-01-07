#
# (c) Peralta Informatics 2007
# $Id: DeployPostgreSqlModule.py 229 2008-01-01 00:50:52Z andrei $
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

import DeployUtilities

import DeployDatabaseModule
from DeployDatabaseModule import DeployDatabaseModule
from DeployDatabaseConfiguration import DatabaseConfiguration

NpgsqlLocationAttributeName = 'NpgsqlLocation'


class DeployPostgreSqlModule(DeployDatabaseModule):

    def __init__(self):
        pass


    def ReadConfiguration(self, reader, configuration, database = None):

        if not hasattr(configuration, 'Databases'):
            configuration.Databases = []

        if database == None:
            database = DatabaseConfiguration()
            configuration.Databases.Add(database)

        if reader.MoveToAttribute(NpgsqlLocationAttributeName):
            database.NpgsqlLocation = reader.ReadContentAsString()
            reader.MoveToElement()

        DeployDatabaseModule.ReadConfiguration(self, reader, configuration, database = database)


    def PrintConfiguration(self, configuration):

        if not hasattr(configuration, 'Databases'):
            return

        for database in configuration.Databases:
            DeployDatabaseModule.PrintConfiguration(self, configuration, database = database)

            print '    NpgsqlLocation:    ' + database.NpgsqlLocation


    def CreateConnectionString(self, configuration):

        if configuration.Driver is not None:

            if configuration.Driver == 'pgdb':

               # dbhost = params[0]
               # dbbase = params[1]
               # dbuser = params[2]
               # dbpasswd = params[3]
               # dbopt = params[4]
               # dbtty = params[5]

                return System.String.Format("{0}:{1}:{2}:{3}", configuration.Server, configuration.Name, configuration.UserName, configuration.Password)

            if configuration.Driver == 'Npgsql':
                return 'Server=%s;Port=5432;User ID=%s;Password=%s;SSL=True;Sslmode=Require;Database=%s' % (configuration.Server, configuration.UserName, configuration.Password, configuration.Name)



    def DatabaseExists(self, configuration):
        clr.AddReferenceToFileAndPath(configuration.NpgsqlLocation)
        import Npgsql

        exists = False

        connection = Npgsql.NpgsqlConnection()
        connection.ConnectionString = "Server=%s;Port=5432;User ID=%s;Password=%s;SSL=True;Sslmode=Require;Database=postgres" % (configuration.Server, configuration.UserName, configuration.Password)

        try:
            connection.Open()

            try:
                command = connection.CreateCommand()

                command.CommandText = "select * from pg_database where datname = N'%s'" % (configuration.Name)

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
        clr.AddReferenceToFileAndPath(configuration.NpgsqlLocation)
        import Npgsql

        if not self.DatabaseExists(configuration):
            return

        connection = Npgsql.NpgsqlConnection()
        connection.ConnectionString = "Server=%s;Port=5432;User ID=%s;Password=%s;SSL=True;Sslmode=Require;Database=postgres" % (configuration.Server, configuration.UserName, configuration.Password)

        try:
            connection.Open()

            try:
                command = connection.CreateCommand()

                commandText = []
                commandText.append('drop database "%s"' % (configuration.Name))

                command.CommandText = ''.join(commandText)

                command.ExecuteNonQuery()

                print 'Dropping database %s on %s' % (configuration.Name, configuration.Server)

            except System.Exception, e:
                print e
                command.Dispose()
                raise
            
            else:
                command.Dispose()
            
        except:
            raise

        else:
            connection.Close()


    def BuildDatabase(self, configuration):
        clr.AddReferenceToFileAndPath(configuration.NpgsqlLocation)
        import Npgsql

        if self.DatabaseExists(configuration):
            return

        connection = Npgsql.NpgsqlConnection()
        connection.ConnectionString = "Server=%s;Port=5432;User ID=%s;Password=%s;SSL=True;Sslmode=Require;Database=postgres" % (configuration.Server, configuration.UserName, configuration.Password)

        commands = []
        command = []

        command.append("create database \"%s\" encoding 'UTF8'" % (configuration.Name))
        commands.append(''.join(command))
        command[:] = [] 

        builder = System.Text.StringBuilder()

        builder.Length = 0

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
        print 'Populating database %s on %s' % (configuration.Name, configuration.Server)

        environmentVariables = {}

        environmentVariables['PGPASSWORD'] = configuration.Password

        for encodedScriptPath in configuration.Scripts:

            scriptPath = DeployUtilities.ExpandEnvironmentVariables(encodedScriptPath)

            DeployUtilities.RunExternalCommand('psql', '-q -d %s -h %s -U %s -f %s' % (configuration.Name, configuration.Server, configuration.UserName, encodedScriptPath), environmentVariables = environmentVariables)


def main():
    return 0

if __name__ == '__main__':
    sys.exit(main())

