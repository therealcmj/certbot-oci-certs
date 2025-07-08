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


