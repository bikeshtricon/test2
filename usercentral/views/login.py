from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from Crypto.Cipher import Blowfish
import urllib
import base64
import time
from xml.dom.minidom import parse, parseString
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

import logging
log = logging.getLogger(__name__)


'''
    User Login
'''
@view_config(route_name='validateLogin')
def validateLogin(request):
    session = request.session
    try:
        # Get user name and password
        userName = (request.params['username']).strip()
        password = (request.params['userpassword']).strip()
        
        # Get values from config
        applicationName = request.registry.settings.get('application_name')
        environmentName = request.registry.settings.get('environment_name')
        organizationId = request.registry.settings.get('organization_id')
        authRole = request.registry.settings.get('auth_role')
        
        # Get base64 encoded X-Auth string
        authStr = userName + ':' + password
        basic = 'Basic '
        binary_data = authStr.encode('ascii')
        XAuthorization = base64.b64encode(binary_data)
        XAuthorizationString = basic + XAuthorization.decode(encoding='ascii')
        # Call auth api
        url = request.registry.settings.get('auth_url') + '/api/rest/v2/identities/' + userName
        headers = {'X-Authorization':XAuthorizationString, 'x-crippled-client':'yes', 'x-rest-method':'GET'}
        req = urllib.request.Request(url=url, headers=headers)
        try:
            response = urllib.request.urlopen(req)
            log.info("response status: %s" % response.getheader('x-true-statuscode'))
        except urllib.error.HTTPError as e:
            log.info("response status: %s" % e.code)
            log.info("response Description: %s" % str(e))
            return HTTPFound(location='/?message=InvalidCredentials')
        
        # Get response headers
        status = int(response.getheader('x-true-statuscode'))
        
        if status == 200:
            # Convert the response into xml 
            response = parseString(response.read())
            xmlRes = response.toxml()
            log.info('xmlRes: %s' % xmlRes)
            # Parse xml string
            dom = parseString(xmlRes) 
              
            # Validate user authorization
            if len(dom.getElementsByTagName('ApplicationSettings')) != 0:
                for elt in dom.getElementsByTagName('ApplicationSettings'):
                    if elt.getAttribute("applicationName") == str(applicationName) and elt.getAttribute("environmentName") == str(environmentName) and elt.getAttribute("organizationId") == str(organizationId):
                        roleNodes = elt.getElementsByTagName('roles')
                        for role in roleNodes:
                            if role.childNodes[0].nodeValue == str(authRole):
                                session['user'] = userName
                                session['XAuthorizationString'] = XAuthorizationString
                                return HTTPFound(location='/addUser')
        elif status == 401:
            return HTTPFound(location='/?message=InvalidCredentials')
        else:
            return HTTPFound(location='/?message=InvalidCredentials')
        
    except Exception as e:
        raise Exception('Unable to Login this user: %s' % str(e))

'''
    Login user if not already logged in otherwise redirect it to addUser page
'''
@view_config(route_name='userLogin', renderer='userLogin.html')
def userLogin(request):
    user = checkAuth(request)
    if user:
        return HTTPFound(location='/addUser')
    else:
        return {'user': 'anonymous'}
    
'''
    User SignOut
'''
@view_config(route_name='signOut')
def signOut(request):
    session = request.session
    session.invalidate()
    return HTTPFound(location='/')

def checkAuth(request):
    session = request.session
    log.info('Session: %s' % session)
    
    if session.has_key('user') and session['user']:
        return True
    else:
        return False

'''
    Decrypts a password reset token. Returns user if
    the token is valid, else raise an exception
'''
def decryptPasswordResetToken(request, token, checkExpiration=True):
    try:
        user, expire = Blowfish.new('J3EBA32BEYVCEINK').decrypt(base64.b16decode(token)).decode("utf-8").rstrip('X').rsplit('@', 1)
        log.info('user %s' % user)
        log.info('expire %s' % expire)
        expire = int(expire)
        if checkExpiration and expire < time.time():
            log.info('Time duration for this request has expired.')
            return {'result':'fail', 'message':'Time duration expired'}
        return user, expire
    except Exception as e:
        log.info('invalid password reset token Exception[%s]' % str(e))
        return {'result':'fail', 'message':'Invalid token'}

