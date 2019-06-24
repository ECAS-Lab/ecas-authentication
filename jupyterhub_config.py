import os,sys
import warnings
from oauthenticator.generic import LocalGenericOAuthenticator
from tornado import gen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import check_registration as cr
import json
import subprocess
import string
from random import *

class LocalEnvAuthenticator(LocalGenericOAuthenticator):

    ecas_user = None

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
            if self.ecas_user:
                characters = string.ascii_letters + string.digits + '+-_='
                password =  "".join(choice(characters) for x in range(randint(8, 16))) 
                                
                p = subprocess.Popen(["oph_manage_user -a add -u " +username+ " -p " +password+ " -c 20 -r no -d /home/" +username+ "-o "+username+" -e "+email],shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                out, err = p.communicate()

                if err:
                    print("Error in creating new user")
                    return
                else:
                    print("New ECAS user created")
                    return auth_state
            else:
                return


c.JupyterHub.authenticator_class = LocalEnvAuthenticator

LocalEnvAuthenticator.ecas_user = True

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
