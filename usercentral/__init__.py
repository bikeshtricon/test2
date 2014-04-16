from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    
    # Mako settings for file extension .html  
    config.include('pyramid_mako')
    config.add_mako_renderer('.html')
    
    # Add support for beaker
    config.include('pyramid_beaker')
    
    session_factory = session_factory_from_settings(settings)
    config.set_session_factory(session_factory)   
    
	# Add support for mailer
    config.include('pyramid_mailer')

    config.add_static_view('static', 'static', cache_max_age=3600)
    
    # Routes
    config.add_route('home', '/home')
    config.add_route('validateLogin', '/validate/login')
    config.add_route('signOut', '/signout')
    config.add_route('resetPassword', '/reset/password')
    config.add_route('userCentralMaster','/userCentralMaster')
    config.add_route('userLogin','/')
    config.add_route('forgotPassword','/forgotPassword')
    config.add_route('addUser','/addUser')
    config.add_route('addUserSubmit','/addUserSubmit')
    
    config.scan()
    
    return config.make_wsgi_app()
