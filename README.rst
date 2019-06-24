Integration of INDIGO IAM with JupterHub
=========================================

*IAM* (Identity and Access Management) service is one of EOSChub AAI solution, and provided by INDIGO-DataCloud project. The IAM service provides a layer where identities, enrolment, group membership, attributes and policies to access distributed resources and services can be managed in a homogeneous and interoperable way.

This package contains the extensions to enable IAM OAuth Token-based AuthN/AuthZ in the context of ECAS-Lab.

Prerequisites
--------------

You should have an ECAS-Lab instance (at least JupiterHub = 0.9 and Ophidia >= 1.5) running.

Dependencies
--------------

The following packages are needed:

**oauthenticator**

OAuth + JupyterHub Authenticator = OAuthenticator

It allows using your chosen OAuthenticator. Each authenticator, provided in a submodule of oauthenticator, will map OAuth usernames onto local system usernames.

To install the *oauthenticator* package run the following command:

.. code-block:: bash

 pip install oauthenticator

**cryptography**

It provides both high-level recipes and low-level interfaces to common cryptographic algorithms such as symmetric ciphers, message digests, and key derivation functions.

To install the *cryptography* package run the following command:

.. code-block:: bash

 pip install cryptography

**mysql-connector**

A self-contained Python driver for communicating with MySQL servers.

To install the *mysql-connector* package run the following command:

.. code-block:: bash
 
 pip install mysql-connector-python

**configparser**

It allows managing user-editable configuration files.

To install the *configparser* package run the following command:
 
.. code-block:: bash
 
 pip install configparser


Configuration
--------------

Quick setup
^^^^^^^^^^^

To make Jupyter working with IAM OAuth Token-based AuthN/AuthZ you can extend your JupyterHub configuration with the code from the *jupyterhub_config.py* file into this repository.

Then simply update the following options into the configuration file:

.. code-block:: python

   c.GenericOAuthenticator.userdata_url = '<USER DATA ENDPOINT>'
   c.GenericOAuthenticator.token_url = '<AUTH TOKEN ENDPOINT>'
   ...
   c.MyOAuthenticator.client_id = '<your-client-id>'
   c.MyOAuthenticator.client_secret = '<your-client-secret>'
   ...
   c.JupyterHub.template_paths = ['/path/to/your/templates/dir']

and export the following environmental variables:

.. code-block:: bash

   export JUPYTERHUB_CRYPT_KEY=$(openssl rand -hex 32)
   export OAUTH2_AUTHORIZE_URL=<AUTHORIZATION ENDPOINT>
   export OAUTH2_TOKEN_URL=<AUTH TOKEN ENDPOINT>

Then update the *config.ini* file accordingly to configure the connection to your OphidiaDB. 

Finally, copy the *error.html* under your template folder.


Setup in detail
^^^^^^^^^^^^^^^

To make Jupyter work with IAM OAuth Token-based AuthN/AuthZ you can extend your JupyterHub configuration file following the next steps.

**Set chosen OAuthenticator**

To enable the IAM OAuth token-based AuthN/AuthZ, in the JupyterHub front-end configuration file, *jupyterhub_config.py*, add the LocalGenericOAuthenticator plugin:

.. code-block:: python

   from oauthenticator.generic import LocalGenericOAuthenticator

**Override authenticate() method**

In order to successfully login using INDIGO IAM, an ECASLab account is also required.

The LocalGenericOAuthenticator class needs to be extended to override the authenticate() method to check if a user has an ECASLab account.

.. code-block:: python
   
   import check_registration as cr
   class LocalEnvAuthenticator(LocalGenericOAuthenticator):

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

where the *check_registration.py* script is used to read the (username, email) pair in the OphidiaDB instance. 

To this end, you may need to create a read-only user in the OphidiaDB in order to grant access to the USER table.

.. code-block:: sql

    CREATE USER 'user'@'hostname';
    GRANT SELECT ON ophidiadb.user TO 'user'@'hostname' IDENTIFIED BY 'password';

You can also configure the OphidiaDB connection by creating the config.ini file as follows:

.. code-block:: bash

   [ophidia]
   user=db_user
   pass=db_password
   host=db_host
   db=db_name
   port=db_port


**Propagate IAM token to the user environment**

In order to propagate the token received by IAM within the Ophidia/user environment, the JupyterHub front-end configuration file should be extended to perform a pre-spawner procedure, which intercepts the token and creates an environment variable:

.. code-block:: python
   
    @gen.coroutine
    def pre_spawn_start(self, user, spawner):
        auth_state = yield user.get_auth_state()
        if not auth_state:
            return
        spawner.environment['OPH_TOKEN'] = auth_state['access_token']
    
**Set client ID, client secret and other settings**

All OAuthenticators require setting a client ID and client secret. You will generally get these when you register your OAuth application with your OAuth provider.

You can set these values in your configuration file, *jupyterhub_config.py*:

.. code-block:: python

   c.MyOAuthenticator.client_id = '<your-client-id>'
   c.MyOAuthenticator.client_secret = '<your-client-secret>'

In addition, set the following settings in your *jupyterhub_config.py*:
 
.. code-block:: python

   c.LocalGenericOAuthenticator.enable_auth_state = True
   if 'JUPYTERHUB_CRYPT_KEY' not in os.environ:
    warnings.warn(
        "Need JUPYTERHUB_CRYPT_KEY env for persistent auth_state.\n"
        "    export JUPYTERHUB_CRYPT_KEY=$(openssl rand -hex 32)"
    )
   c.CryptKeeper.keys = [ os.urandom(32) ]
   c.GenericOAuthenticator.login_service = 'Indigo IAM'
   c.GenericOAuthenticator.userdata_url = '<USER DATA ENDPOINT>'
   c.GenericOAuthenticator.token_url = '<AUTH TOKEN ENDPOINT>'
   c.GenericOAuthenticator.userdata_method = 'GET'
   c.LocalGenericOAuthenticator.userdata_params = {"state": "state"}
   c.LocalGenericOAuthenticator.username_key = "preferred_username"
   c.LocalAuthenticator.create_system_users = False

Finally, set the following environmental variables:

.. code-block:: bash

   export JUPYTERHUB_CRYPT_KEY=$(openssl rand -hex 32)
   export OAUTH2_AUTHORIZE_URL=<AUTHORIZATION ENDPOINT>
   export OAUTH2_TOKEN_URL=<AUTH TOKEN ENDPOINT>

**Customize JupyterHub Error Messages**

If a user logged in using INDIGO IAM credentials has no ECASLab account, it will be redirected to a customized error page.

JupyterHub will look for custom templates in all of the paths in the JupyterHub.template_paths configuration option, falling back on the default templates if no custom template with that name is found. This fallback behavior is new in version 0.9; previous versions searched only those paths explicitly included in template_paths.

To customize the error messages create your templates directory, specify its path in your *jupyterhub_config.py*

.. code-block:: python
   
   # tell jupyterhub to find your template
   c.JupyterHub.template_paths = ['/path/to/your/templates/dir']

and create your customized *error.html* template, which will extend the base one.

.. code-block:: bash

    {% extends "templates/error.html" %}
    
    {% block h1_error %}
      <h1>
        {{status_code}} {{status_message}}
      </h1>
    {% endblock h1_error %}
    
    
    
    {% block error_detail %}
    <div class="error">
    <p>Your credentials are valid, but your account on ECASLab was not found</p>
    <p>Please, register at /your/registration/link/
    <p>If you already have an account, please contact us at ecas-support [at] cmcc [dot] it</p>
    </div>
    
    {% endblock error_detail %}

Additional information related to JupyterHub templates can be found `here <https://jupyterhub.readthedocs.io/en/stable/reference/templates.html>`_.


**Create automatically an ECASLab account**

It is possible to automatically create an ECASLab account for a user who has not an account yet by using its INDIGO IAM credentials.

*Quick way*

Set the following configuration option in the *jupyterhub_config.py* (starting from the file provided by this repository).

.. code-block:: python

   LocalEnvAuthenticator.ecas_user = True


*Detailed procedure*

In order to accomplish that:

- define a class attribute for the **LocalEnvAuthenticator** class:

.. code-block:: python

   class LocalEnvAuthenticator(LocalGenericOAuthenticator):
       ecas_user = None
     
- set the corresponding setting in your *jupyterhub_config.py*:

.. code-block:: python

   LocalEnvAuthenticator.ecas_user = True

If **True**, a new ECAS user will be automatically created using a randomly generated password.

- extend the **authenticate** method as follows:

.. code-block:: python

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

Note: if the server is deployed on a different machine than the one hosting the JupyterHub instance, please execute the command over ssh. For example:

 .. code-block:: python

   ssh = subprocess.Popen(["ssh", "%s" % HOST, COMMAND],shell=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   result = ssh.stdout.readlines()
   if result == []:
      print(ssh.stderr.readlines())
      return
   else:
      print("New ECAS user created")
      return auth_state

