import pyodbc

import logging
log = logging.getLogger(__name__)


class DbModel:
    def __init__(self,request):

        # creating cursor

        self.con_string = 'DSN=%s;UID=%s;PWD=%s;DATABASE=%s;' % (request.registry.settings.get('databse_datasource'), request.registry.settings.get('databse_user'), request.registry.settings.get('databse_password'), request.registry.settings.get('databse_name'))

        self.cnxn = pyodbc.connect(self.con_string)
        self.cursor = self.cnxn.cursor()

    # Function for getting all program name and id (return dictionary , program id as key and program name as value)
    def fetchPrograms(self):

        self.cursor.execute("select * from ProgramDetails")
        programs = {}
        rows = self.cursor.fetchall()

        if rows:
            for row in rows:
                programs[row.ProgramId] = row.ProgramName

        return programs

    # Function for getting all program details id, name ,organization Id, etc (return dictionary )
    def fetchProgramDetails(self):

        self.cursor.execute("select * from ProgramDetails")
        programs = {}
        rows = self.cursor.fetchall()

        if rows:
            for row in rows:
                programs[row.ProgramId] = {'programName':row.ProgramName, 'organizationId':row.OrganizationId, 'identityProgram':row.IdentityProgram}

        return programs

    # Function for getting all Carrier Details name and id (return dictionary , Carrier Details id as key and CarrierDetails name as value)
    def fetchCarrierGroups(self):

        self.cursor.execute("select * from CarrierDetails")
        carrierGroups = {}
        rows = self.cursor.fetchall()

        if rows:
            for row in rows:
                 carrierGroups[row.CarrierGroupId] = row.CarrierName

        return carrierGroups

