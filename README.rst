certbot-oci-certs
=================

Oracle Cloud Infrastructure (OCI) Installer plugin for Certbot.

This plugin automates the process of installing a certificate acquired by certbot
into OCI Certificates Management Service.

For more information on the OCI Certificates service pleae see the official documentation at
https://docs.oracle.com/en-us/iaas/Content/certificates/home.htm

Configuration:
--------------

Install and configure the OCI CLI. See https://docs.cloud.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm
for details.

To use this installer you will need:

* an OCI account with adequate permission to Create / Update / Delete certificates stored in the Certificates Management Service

Installation
------------

I haven't published this in PyPI yet. So for the time being you need to install from source.

::

    git clone git@github.com:therealcmj/certbot-oci-certs.git
    cd certbot-oci-certs
    pip install .


or

::

    git clone git@github.com:therealcmj/certbot-oci-certs.git
    pip install ./certbot-oci-certs


Development
-----------

If you want to work on the code you should create a virtual environment and install it there:

::

    git clone git@github.com:therealcmj/certbot-oci-certs.git
    cd certbot-oci-certs
    virtualenv dev
    . ./dev/bin/activate
    pip install -e .

You can then use your IDE as normal on the live code.

To use the debugger be sure to choose the correct virtual environment. For PyCharm go to Debug, Edit Configurations
and then update the Interpreter to point to the newly created Virtual Environment.

Arguments
---------

As of this writing this plug-in supports the following arguments on certbot's command line:

::

  --oci-certificate-id OCI_CERTIFICATE_ID
                        Certificate OCID (default: None)
  --oci-certificate-name OCI_CERTIFICATE_NAME
                        Certificate Name (default: None)
  --oci-compartment-id OCI_COMPARTMENT_ID
                        Compartment OCID (default: None)
  --oci-auth-mode {configfile,instance,cloudshell}
                        Authentication mode - one of "configfile", "instance", "cloudshell" (default: configfile)
  --oci-configfile OCI_CONFIGFILE
                        OCI CLI Configuration file (for authmode=configfile). (default: None)
  --oci-profile OCI_PROFILE
                        OCI configuration profile (in OCI configuration file) (default: DEFAULT)


You can always get a list of the available arguments by running

::

  certbot installer -h oci

Examples
--------

Assuming you have previously acquired a certificate for demosite.ociateam.com
(perhaps using the certbot-dns-oci plug-in)
you can install it via:


::

    certbot install \
     --logs-dir logs --work-dir work --config-dir config \
     --installer oci \
     --oci-compartment $MYOCICOMPARTMENT \
     --cert-path demosite.ociateam.com/cert.pem \
     --key-path demosite.ociateam.com/privkey.pem \
     --chain-path demosite.ociateam.com/chain.pem \
     -d demosite.ociateam.com



If you want to acquire a certificate AND install it in one go using both of my plug-ins you can do that too...

::
    CERTNAME=demo$$.ociateam.com ; \
    certbot run \
     --test-cert \
     --logs-dir logs --work-dir work --config-dir config \
     --authenticator dns-oci \
     --installer oci \
     --oci-compartment $MYOCICOMPARTMENT \
     --oci-certificate-name $CERTNAME \
     --debug \
     -d $CERTNAME


And to renew (just that one certificate) later it's just:

::

    CERTNAME=demo$$.ociateam.com ; \
    certbot renew \
     --test-cert \
     --logs-dir logs --work-dir work --config-dir config \
     --debug \
     --cert-name $CERTNAME


CAUTION:
--------

Please do remember tat "certbot renew" tries to renew all certs nearing expiration. If you use the
--oci-certificate-name command line argument when running "certbot renew" you're going to make a mess of things.
So be cautious and renew certs one by one OR remember to leave that command line argument off!

YOU HAVE BEEN WARNED.

