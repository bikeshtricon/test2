from pyramid.view import view_config
import urllib,json,random,string
from Crypto.Cipher import Blowfish
import base64
from pyramid.response import Response
from usercentral.models.db import DbModel
from xml.dom.minidom import parse, parseString
from pyramid.httpexceptions import HTTPFound
from usercentral.views import login
import time
import xmltodict

from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

import logging
log = logging.getLogger(__name__)

@view_config(route_name='home', renderer='home.mako')
def home(request):
    return {'project': 'UserCentral'}

@view_config(route_name='userCentralMaster', renderer='userCentralMaster.html')
def userCentralMaster(request):
    return {'user': 'anonymous'}

"""
    Generates an encrypted token to be used in password reset URL
"""
def encryptPasswordResetToken(request, user, expire):
    data = '%s@%s' % (user, int(time.time()) + int(expire * 60 * 60 * 24))
    if len(data) % 8:
        # data block length must be multiple of eight
        data += 'X' * (8 - (len(data) % 8))
    return base64.b16encode(Blowfish.new('J3EBA32BEYVCEINK').encrypt(data)).decode("utf-8")

'''
    Forgot Password
'''
@view_config(route_name='forgotPassword', renderer='forgotPassword.html')
def forgotPassword(request):
    user = login.checkAuth(request)
    if user:
        return HTTPFound(location='/addUser')
    elif request.params.get('username'):
        # Get user name
        userName = (request.params['username']).strip()
        stageUrl = request.registry.settings.get('stage_url')
        validateUrl = stageUrl + '/' + userName

        authUserName = request.registry.settings.get('application_auth_username')
        authPassword = request.registry.settings.get('application_auth_password')
        # Get base64 encoded X-Auth string
        authStr = authUserName + ':' + authPassword
        basic = 'Basic '
        binary_data = authStr.encode('ascii')
        XAuthorization = base64.b64encode(binary_data)
        XAuthorizationString = basic + XAuthorization.decode(encoding='ascii')
        req = urllib.request.Request(url=validateUrl)
        req.add_header("Authorization", XAuthorizationString)
        try:
            result = urllib.request.urlopen(req)
        except urllib.request.HTTPError as e:
            if e.code == 401 or e.code == 403:
                log.info('not authorized..........')
                return {'user': 'anonymous', 'result':'fail', 'message':'The username/email or password were incorrect.'}
            elif e.code == 404:
                log.info('not found.............')
                return {'user': 'anonymous', 'result':'fail', 'message':'The username/email provided could not be found. Please check your entry and try again.'}
            else:
                log.info('Error: %s' % e.code)
                log.info('unknown error:......... ')
                return {'user': 'anonymous', 'result':'fail', 'message':'We are unable to process your request at this time. Please contact the <a href="mailto:desk@icg360.com">help desk</a> for support.'}
        else:
            # Get token
            token = encryptPasswordResetToken(request, userName, 1)
            # SEND MAIL
            mailer = get_mailer(request)
            fromAdr = request.registry.settings.get('email_from')
            subject = request.registry.settings.get('reset_email_subject')
            resetLink = request.registry.settings.get('base_url') + "/reset/password" + "?t=%s" % token
            messageBody = '<div class="container"><div class="mail_header_container" style="background-color: #074375; color: #FFFFFF; font-size: 24px; padding: 15px;"><div class="mail_header_container"><b>Policy Central Password Reset</b></div></div><div class="mail_body" style="font-size: 17px; padding: 15px;">We recently recieved a request to reset the password for <b>'+ userName +'</b>. To reset your password, click on the link below:<br><br><div class="link_body" style="background-color: #D9EAF8; border: 1px solid #89BCE8; color: #032B56; padding: 9px;"><b><a href="'+ resetLink +'">'+ resetLink +'</a></b></div><br>If you have any issues with your account, please contact our Insight Help Desk at <b>1-866-315-4866, option #6</b> or at <a href="mailto:helpdesk@icg360.com?Subject=Issues%20regarding%20account">helpdesk@icg360.com</a>.<br><br>Thank you,<br><br>Insight Help Desk</div></div>'
            message = Message(subject=subject, sender=fromAdr, recipients=[userName], body=messageBody, html=messageBody)
            mailer.send_immediately(message, fail_silently=False)
            log.info('email sent successfully......... ')
            return {'user': 'anonymous', 'result': 'success', 'message':'The reset password link has been sent to your email id.'}
    else:
        return {'user': 'anonymous'}

@view_config(route_name='addUser', renderer='addUser.html')
def addUser(request):
    session = request.session
    if session.has_key('user') and session['user']:
        user = session['user']
        model = DbModel(request)
        userProgram = model.fetchPrograms()
        carrierGroup = model.fetchCarrierGroups()
        return {'user': 'user', 'userProgram':list(userProgram.items()), 'carrierGroup':list(carrierGroup.items())}
    else:
        return HTTPFound(location='/')

@view_config(route_name='addUserSubmit')
def addUserSubmit(request):
    session = request.session
    output = {}
    if session.has_key('user') and session['user']:
        url = request.registry.settings.get('auth_url') + '/api/rest/v2/identities/'
        model = DbModel(request)
        userProgramDetails = model.fetchProgramDetails()
        programDetails = userProgramDetails.get(request.params['userprogram']);
        userId = (request.params['useremail']).strip()
        randomPassword = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(6))
        #Adding a numeric and uppercase letter to the random password
        AlphaNumericPassword = random.choice(string.ascii_uppercase) + random.choice(string.digits) + randomPassword
        userName = (request.params['username']).strip()
        emailAddress = (request.params['useremail']).strip()
        userType = (request.params['usertype']).strip()
        targetName = programDetails.get('programName').strip()
        targetProgramId = (request.params['userprogram']).strip()
        targetProgram = programDetails.get('organizationId').strip()
        targetProgramCode = programDetails.get('identityProgram').strip()
        log.debug("userType: %s" % userType)
        if userType == 'underwriter':
            params = '<Identity id="'+ userId +'" version="0" archived="false" password="'+ AlphaNumericPassword +'" apiVersion="2"> <Name>'+ userName +'</Name> <Email>'+ emailAddress +'</Email> <Affiliation target="'+ targetProgramId +'" type="employee_company" side="employee" targetName="'+ targetName +'" primary="1"/> <Affiliation target="'+ targetProgramCode +'" type="identity_program" side="identity"/> <ApplicationSettings applicationName="agentportal" organizationId="'+ targetProgram +'" environmentName="production"> <roles>backoffice</roles> </ApplicationSettings> <ApplicationSettings applicationName="ixadmin" organizationId="ics" environmentName="production"> <DashboardPreferences controlPanelOpen="true" helpDrawerOpen="false"/> <PoliciesModule> <Rights> <Right>MANAGE_ASSIGNEES</Right> <Right>ARCHIVE_POLICY</Right> <Right>UNBIND_POLICY</Right> <Right>ENTER_UW_TASK</Right> <Right>RESOLVE_UW_TASK</Right> <Right>REMOVE_FLAG</Right> <Right>SHOW_REPLY_BUTTON</Right> <Right>VIEW_ADVANCED</Right> </Rights> </PoliciesModule> <tentacleLink path="production-'+ targetProgramId +'-agenciesV2"/> <tentacleLink path="production-'+ targetProgramId +'-policies_'+ targetProgramId +'"/> <tentacleLink path="staging-'+ targetProgramId +'-policies_'+ targetProgramId +'"/> <tentacleLink path="production-'+ targetProgramId +'-reports"/> </ApplicationSettings> <ApplicationSettings applicationName="ixdirectory" organizationId="ics" environmentName="production"> <roles>admin</roles> </ApplicationSettings> <ApplicationSettings applicationName="ixlibrary" organizationId="ics" environmentName="production"> <roles> <role>Admin</role> </roles> </ApplicationSettings> <ApplicationSettings applicationName="pxcentral-api" organizationId="'+ targetProgram +'" environmentName="production"> <roles>admin</roles> </ApplicationSettings> </Identity>'
        elif userType == 'costumerservice':
            params = '<Identity id="'+ userId +'" version="0" archived="false" password="'+ AlphaNumericPassword +'" apiVersion="2"> <Name>'+ userName +'</Name> <Email>'+ emailAddress +'</Email> <Affiliation target="'+ targetProgramId +'" type="employee_company" side="employee" targetName="'+ targetName +'" primary="1"/> <Affiliation target="'+ targetProgramCode +'" type="identity_program" side="identity"/> <ApplicationSettings applicationName="agentportal" organizationId="'+ targetProgram +'" environmentName="production"> <roles>backoffice</roles> </ApplicationSettings> <ApplicationSettings applicationName="ixadmin" organizationId="ics" environmentName="production"> <DashboardPreferences controlPanelOpen="true" helpDrawerOpen="false"/> <PoliciesModule> <Rights> <Right>ARCHIVE_POLICY</Right> <Right>UNBIND_POLICY</Right> <Right>ENTER_UW_TASK</Right> <Right>RESOLVE_UW_TASK</Right> <Right>REMOVE_FLAG</Right> <Right>SHOW_REPLY_BUTTON</Right> </Rights> </PoliciesModule> <tentacleLink path="production-'+ targetProgramId +'-agenciesV2"/> <tentacleLink path="production-'+ targetProgramId +'-policies_'+ targetProgramId +'"/> <tentacleLink path="staging-'+ targetProgramId +'-policies_'+ targetProgramId +'"/> <tentacleLink path="production-'+ targetProgramId +'-reports"/> </ApplicationSettings> <ApplicationSettings applicationName="ixdirectory" organizationId="ics" environmentName="production"> <roles>admin</roles> </ApplicationSettings> <ApplicationSettings applicationName="ixlibrary" organizationId="ics" environmentName="production"> <roles> <role>Admin</role> </roles> </ApplicationSettings> <ApplicationSettings applicationName="pxcentral-api" organizationId="'+ targetProgram +'" environmentName="production"> <roles>admin</roles> </ApplicationSettings> </Identity>'
        elif userType == 'carrieruser':
            carrierGroup = (request.params['usergroup']).strip()
            params = '<Identity id="'+ userId +'" version="0" archived="false" password="'+ AlphaNumericPassword +'" apiVersion="2"> <Name>'+ userName +'</Name> <Email>'+ emailAddress +'</Email> <Affiliation target="'+ targetProgramId +'" type="employee_company" side="employee" targetName="'+ targetName +'" primary="1"/> <Affiliation target="'+ carrierGroup +'" type="employee_carriergroup" side="employee" targetName="'+ targetName +'" primary="0"/> <Affiliation target="'+ targetProgramCode +'" type="identity_program" side="identity"/> <ApplicationSettings applicationName="agentportal" organizationId="'+ targetProgram +'" environmentName="production"> <roles>backoffice</roles> </ApplicationSettings> <ApplicationSettings applicationName="ixadmin" organizationId="ics" environmentName="production"> <DashboardPreferences controlPanelOpen="true" helpDrawerOpen="false"/> <PoliciesModule> <Rights> <Right>ARCHIVE_POLICY</Right> <Right>UNBIND_POLICY</Right> <Right>ENTER_UW_TASK</Right> <Right>RESOLVE_UW_TASK</Right> <Right>REMOVE_FLAG</Right> <Right>SHOW_REPLY_BUTTON</Right> </Rights> </PoliciesModule> <tentacleLink path="production-'+ targetProgramId +'-agenciesV2"/> <tentacleLink path="production-'+ targetProgramId +'-policies_'+ targetProgramId +'"/> <tentacleLink path="staging-'+ targetProgramId +'-policies_'+ targetProgramId +'"/> <tentacleLink path="production-'+ targetProgramId +'-reports"/> </ApplicationSettings> <ApplicationSettings applicationName="ixdirectory" organizationId="ics" environmentName="production"> <roles>admin</roles> </ApplicationSettings> <ApplicationSettings applicationName="ixlibrary" organizationId="ics" environmentName="production"> <roles> <role>Admin</role> </roles> </ApplicationSettings> <ApplicationSettings applicationName="pxcentral-api" organizationId="'+ targetProgram +'" environmentName="production"> <roles>admin</roles> </ApplicationSettings> </Identity>'
        log.debug("params: %s" % params)
        binary_data = params.encode('utf-8')

        authUserName = request.registry.settings.get('application_auth_username')
        password = request.registry.settings.get('application_auth_password')
        password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, url, authUserName, password)
        handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
        try:
            opener = urllib.request.build_opener(handler)
            urllib.request.install_opener(opener)
            req = urllib.request.Request(url, binary_data)
            req.add_header('Content-Type', 'application/xml; charset=utf-8')
            req.add_header('Content-Length', len(binary_data))
            response = opener.open(req)
            #response = urllib.request.urlopen(req)
            log.info("response status: %s" % response.status)
            log.info("response headers: %s" % response.getheaders())
            log.info("response body: %s" % response.read())
            if response.status == 201:
                log.debug("response: %s" % response.read())
                # Get token
                token = encryptPasswordResetToken(request, emailAddress, 1)
                # SEND MAIL
                mailer = get_mailer(request)
                fromAdr = request.registry.settings.get('email_from')
                subject = request.registry.settings.get('welcome_email_subject')
                resetLink = request.registry.settings.get('base_url') + "/reset/password" + "?t=%s" % token
                messageBody = '<div class="container"><div class="mail_header_container" style="background-color: #074375; color: #FFFFFF; font-size: 24px; padding: 15px;"><b>Welcome to Policy Central</b></div><div class="mail_body" style="font-size: 17px; padding: 15px;">We have created an account for <b>'+ userName +'</b>.<br><br>The username for this account is '+ emailAddress +'. To set your password, click on the link below:<br><br><div class="link_body" style="background-color: #D9EAF8; border: 1px solid #89BCE8; color: #032B56; padding: 9px;"><b>'+ resetLink +'</b></div><br>If you have any issues with your account or are not the intended recipient please contact our Insight Help Desk at <b>1-866-315-4866, option #6</b> or at <a href="mailto:helpdesk@icg360.com?Subject=Issues%20regarding%20account">helpdesk@icg360.com</a>.<br><br>Thank you,<br><br>Insight Help Desk</div></div>'
                message = Message(subject=subject, sender=fromAdr, recipients=[emailAddress], body=messageBody, html=messageBody)
                mailer.send_immediately(message, fail_silently=False)
                log.info('email sent successfully......... ')

                output['result'] = 'success'
                output['username'] = userName
                output['message'] = 'User has been added successfully'
                response =  Response(json.dumps(output, sort_keys=True))
                response.content_type = 'application/json; charset=utf-8'
        except urllib.error.HTTPError as e:
            log.info("response status: %s" % e.code)
            log.info("response Description: %s" % str(e))
            if e.code == 409:
                output['result'] = 'fail'
                output['message'] = 'The username/email entered is already in use, please try another.'
            elif e.code == 401 or e.code == 403:
                output['result'] = 'fail'
                output['message'] = 'The username/email or password were incorrect.'
            else:
                output['result'] = 'fail'
                output['message'] = 'The user was unable to be created at this time. Please contact the <a href="mailto:desk@icg360.com">help desk</a> for support.'
            #raise Exception('HTTP Error in login: %s' % str(e))

        response =  Response(json.dumps(output, sort_keys=True))
        response.content_type = 'application/json; charset=utf-8'

        return response
    else:
        return HTTPFound(location='/')

@view_config(route_name='resetPassword', renderer='resetPassword.html')
def resetPassword(request):
    user = login.checkAuth(request)
    if user:
        return HTTPFound(location='/addUser')
    elif request.params.get('password'):
        token = request.params['t']
        log.info('Token: %s' % token)
        userName, expire = login.decryptPasswordResetToken(request, token)
        log.info('userName:%s, expire:%s' %(userName, expire))

        stageUrl = request.registry.settings.get('stage_url')
        validateUrl = stageUrl + '/' + userName

        authUserName = request.registry.settings.get('application_auth_username')
        authPassword = request.registry.settings.get('application_auth_password')
        # Get base64 encoded X-Auth string
        authStr = authUserName + ':' + authPassword
        basic = 'Basic '
        binary_data = authStr.encode('ascii')
        XAuthorization = base64.b64encode(binary_data)
        XAuthorizationString = basic + XAuthorization.decode(encoding='ascii')
        req = urllib.request.Request(url=validateUrl)
        log.info('validateUrl: %s ' % validateUrl)
        req.add_header("Authorization", XAuthorizationString)
        try:
            result = urllib.request.urlopen(req)
        except urllib.request.HTTPError as e:
            if e.code == 401:
                log.info('not authorized..........')
                return {'user': 'anonymous', 'result':'fail', 'message':'not authorized'}
            elif e.code == 404:
                log.info('not found.............')
                return {'user': 'anonymous', 'result':'fail', 'message':'not found'}
            elif e.code == 503:
                log.info('service unavailable..............')
                return {'user': 'anonymous', 'result':'fail', 'message':'service unavailable'}
            else:
                log.info('unknown error:......... ')
                return {'user': 'anonymous', 'result':'fail', 'message':'unknown error'}
        else:
            # Get token
            log.info('Success..................')
            response = parse(result)
            xmlString = response.toxml()

            log.info('xmlString: %s' % xmlString)

            xmlDict = xmltodict.parse(xmlString)
            xmlVersion = xmlDict['Identity']['@version']
            newXmlVersion= int(xmlVersion) + 1
            xmlDict['Identity']['@version'] = str(newXmlVersion)
            xmlDict['Identity'].update({'@password': request.params['password']})
            log.info("json %s" % xmlDict)
            xmlConverted = xmltodict.unparse(xmlDict)
            log.info("xmlConverted %s" % xmlConverted)
            binary_data = xmlConverted.encode('utf-8')

            username = request.registry.settings.get('application_auth_username')
            password = request.registry.settings.get('application_auth_password')
            password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, validateUrl, username, password)
            handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
            try:
                opener = urllib.request.build_opener(handler)
                urllib.request.install_opener(opener)
                updateRequest = urllib.request.Request(validateUrl, binary_data, method='PUT')
                updateRequest.add_header('Content-Type', 'application/xml; charset=utf-8')
                updateRequest.add_header('Content-Length', len(binary_data))
                log.info('Request.method:......... %s ' % updateRequest.method)
                response = opener.open(updateRequest)
                #response = urllib.request.urlopen(updateRequest)
                log.info("response status: %s" % response.status)
                log.info("response headers: %s" % response.getheaders())
                log.info("response body: %s" % response.read())
                if response.status == 200:
                    log.debug("response: %s" % response.read())
                    log.info('Xml success:......... ')
                    return {'user': 'anonymous', 'result':'success', 'message':'Password updated successfully'}
            except urllib.request.HTTPError as e:
                if e.code == 401:
                    log.info('Xml not authorized..........')
                    return {'user': 'anonymous', 'result':'fail', 'message':'not authorized'}
                elif e.code == 404:
                    log.info('Xml not found.............')
                    return {'user': 'anonymous', 'result':'fail', 'message':'not found'}
                elif e.code == 503:
                    log.info('Xml service unavailable..............')
                    return {'user': 'anonymous', 'result':'fail', 'message':'service unavailable'}
                else:
                    log.info('Xml unknown error:......... %s ' % str(e))
                    return {'user': 'anonymous', 'result':'fail', 'message':'unknown error'}
    else:
        return {'user': 'anonymous'}
