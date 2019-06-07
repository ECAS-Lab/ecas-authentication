import os,sys
import warnings
from oauthenticator.generic import LocalGenericOAuthenticator
from tornado import gen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import check_registration as cr
import json


class LocalEnvAuthenticator(LocalGenericOAuthenticator):

    @gen.coroutine
    def pre_spawn_start(self, user, spawner):
        auth_state = yield user.get_auth_state()
        if not auth_state:
            return
        spawner.environment['OPH_TOKEN'] = auth_state['access_token']
        
     
    @gen.coroutine
    def authenticate(self, handler, data=None):
        for i in super().authenticate(handler,data):
            yield i
    
        auth_state = yield i
     
        email = auth_state['auth_state']['oauth_user']['email']
        username = auth_state['auth_state']['oauth_user']['preferred_username']
        status = cr.main(username,email)
        if status: 
            return auth_state
        else:
            return


c.JupyterHub.authenticator_class = LocalEnvAuthenticator

c.JupyterHub.template_paths = ['/path/to/your/templates/dir']

c.OAuthenticator.client_id = '<your-client-id>'
c.OAuthenticator.client_secret = '<your-client-secret>'

c.LocalGenericOAuthenticator.enable_auth_state = True

if 'JUPYTERHUB_CRYPT_KEY' not in os.environ:
        warnings.warn(
        "Need JUPYTERHUB_CRYPT_KEY env for persistent auth_state.\n"
        "    export JUPYTERHUB_CRYPT_KEY=$(openssl rand -hex 32)"
        )    
c.CryptKeeper.keys = [ os.urandom(32) ]

c.LocalGenericOAuthenticator.login_service = 'Indigo IAM'
c.LocalGenericOAuthenticator.token_url = '<AUTH TOKEN ENDPOINT>'
c.LocalGenericOAuthenticator.userdata_url = '<USER DATA ENDPOINT>'
c.LocalGenericOAuthenticator.userdata_method = 'GET'
c.LocalGenericOAuthenticator.userdata_params = {"state": "state"}
c.LocalGenericOAuthenticator.username_key = "preferred_username"
c.LocalAuthenticator.create_system_users = False
