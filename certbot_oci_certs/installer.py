"""Certbot Installer for OCI Certificates service."""
import logging
from distutils.command.config import config
from itertools import chain

from certbot import errors
from certbot import interfaces
from certbot.plugins import common

import oci

from certbot.errors import PluginError, Error
from pycparser.ply.yacc import resultlimit

#import oci.certificates_management.CertificatesManagementClient

logger = logging.getLogger(__name__)
import sys
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

class OCIInstaller(common.Plugin, interfaces.Installer):
    description = "OCI Certificates Service installer. Uploads the acquired certificate into the OCI Certificates Service - either as a new certificate or as a new certificate version."
    certificate_main_domain = None
    certificate_name = None
    certificate_id = None
    compartment_id = None

    # I will wind up refactoring this later but for now I'm copy/pasting this from the DNS plug-in. And it uses self.credentials". So so do I here
    credentials = None

    # later on I won't save the credentials / config and instead just hang on to the client handle
    certificates_client = None
    certificates_management_client = None

    @classmethod
    def add_parser_arguments(cls, add):
        add("compartment-id",help="Compartment OCID")
        add("certificate-id",help="Certificate OCID")
        add("certificate-name",help="Certificate Name")

        add('auth-mode', help='Authentication mode - one of "configfile", "instance", "cloudshell"',
            **{
                "default": "configfile",
                "choices": ['configfile', 'instance', 'cloudshell']
            }
        )

        add('configfile', help="OCI CLI Configuration file (for authmode=configfile).")
        add('profile', help="OCI configuration profile (in OCI configuration file)",**{"default":"DEFAULT"})


    def __init__(self, *args, **kwargs):
        super(OCIInstaller, self).__init__(*args, **kwargs)

        # then initialize the SDK
        match self.conf('auth-mode'):
            case "configfile":
                self.credentials = {
                    "config": oci.config.from_file(profile_name=self.conf('profile')),
                    "signer": None,
                }
            case "instance":
                self.credentials = {
                    "config": None,
                    "signer": oci.auth.signers.InstancePrincipalsSecurityTokenSigner(),
                }

            case "cloudshell":
                import os
                self.credentials = {
                    "config": oci.config.from_file(
                        file_location=os.getenv("OCI_CLI_CONFIG_FILE"),
                        profile_name="DEFAULT"
                        # I am fairly certain that DEFAULT is always the right profile for cloud shell
                        # if not then this is the relevant code
                        # profile_name=self.conf('profile')
                    ),
                    # "signer": oci.auth.signers.SecurityTokenSigner(),

                }

        # i may or may not need this
        identity_client = None

        if self.credentials["signer"]:
            signer = self.credentials["signer"]
            identity_client = oci.identity.IdentityClient(self.credentials["config"], signer=signer)
            self.certificates_client = oci.certificates.CertificatesClient(self.credentials["config"], signer=signer)
            self.certificates_management_client = oci.certificates_management.CertificatesManagementClient(self.credentials["config"], signer=signer)
        else:
            identity_client = oci.identity.IdentityClient(self.credentials["config"])
            self.certificates_management_client = oci.certificates_management.CertificatesManagementClient(self.credentials["config"])

        # since we bothered to create an identity client let's use it to check that we can even talk to OCI control plane
        # compartments are not subject to access control so just ask for the tenancy compartment
        try:
            identity_client.get_compartment(self.credentials["config"]["tenancy"])
        except Exception as e:
            logger.error("Failed to retrieve tenancy information. Check your configuration")
            logger(e)
            raise errors.PluginError(Exception("OCI configuration not valid"))

        # copy these for convenience
        compartment_id = self.conf("compartment-id")
        certificate_id = self.conf("certificate-id")
        certificate_name = self.conf("certificate-name")


        # before we try to do anything we need to figure out the current situation vis a vis the cert in certs service
        # possible cases:
        # 1. they provided the certificate OCID
        # 2. they provided the compartment OCID but no name for the certificate
        # 3. they provided the compartment OCID and a name for the certificate

        # Case by case
        # 1. they provided the certificate OCID
        if certificate_id:
            logger.info("Certificate ID {} provided".format(certificate_id))

            # if they provide a certificate ID then the other fields should be ignored
            # using assert here will wind up raising a fatal exception
            # TODO: decide if I want to do that
            assert compartment_id == None
            assert certificate_name == None

            # NOTE: this means that we need certbot to run with permission to get the existing certificate.
            #       This seems OK to me at this point. But I am willing to be convinced otherwise.
            #       If you are reading this and have an opinion you know how to find me.
            logger.debug("Looking for existing certificate with OCID {}".format(certificate_id))
            response = self.certificates_management_client.get_certificate(certificate_id)
            logger.debug("Returned from getting certificate.")

            if len(response.data.items) != 1:
                import json
                logger.error("Failed to locate certificate. Response data: {}".format(json.dumps(oci.util.to_dict(response.data))))
                raise PluginError(Exception("Failure attempting to locate certificate with specified OCID {}".format(certificate_id)))

            # NOTE: we don't set self.compartment_id or self.certificate_name because we're ***NOT***
            #       going to move the existing certificate or change its name.
            self.certificate_id = certificate_id

        # 2. they provided the compartment OCID (but no name for the certificate)
        #    in which case we're going to make one up
        # 3. they provided the compartment OCID and a name for the certificate
        #    in which case we have to go find the existing cert with that name.
        #    Q: should we scold them and tell them to use the OCID because that's more performant?
        if compartment_id:
            self.compartment_id = compartment_id
            if not certificate_name:
                # NOTE: I was going to let this fall through and list certificates in the compartment.
                #       But there exists a possibility, however remote, that someone might allow certbot to INSTALL
                #       a certificate, but not list existing ones in the compartment.
                logger.debug("NO certificate name provided as argument. One will be automatically generated for you.")


            else:
                logger.info("Certificate name '{}' provided".format(certificate_name))

                try:
                    # Try to find a certificate with that name
                    # NOTE: we may ot may find one with that name. A response with **EITHER** 0 or 1 items is A-OK
                    logger.info("Listing certificates in compartment {} with name '{}'".format(compartment_id,certificate_name))
                    response = self.certificates_management_client.list_certificates(compartment_id=compartment_id, name=certificate_name)
                    logger.debug("Returned from listing certificates")

                    # there had better be either zero or only one!
                    if len(response.data.items) == 0:
                        logger.info("Did not find certificate with name '{}'. The certificate will be uploaded as a new certificate to compartment {} with that name".format(certificate_name,compartment_id))

                    elif len(response.data.items) == 1:
                        logger.debug("Getting certificate OCID from response data")
                        self.certificate_id = response.data.items[0].id
                        logger.info("Existing certificate with name {} in compartment {} found. Certificate OCID is {}".format(certificate_name, compartment_id, certificate_id))

                    else:
                        # This should NOT happen because certificate names (OCI names, not domain name or whatever) are unique within a single compartment!
                        # But good programmers look both ways before crossing a one way street.
                        # So...
                        # also I could just do this with an assert. I should probably start doing that.
                        import json
                        raise PluginError(Exception("Expected one matching certificate but response data contained {}: {}".format(len(response.data.items), json.dumps(oci.util.to_dict(response.data)))))

                except Exception as e:
                    logger.error("Exception occurred attempting to list existing certificates in compartment {}".format(compartment_id))
                    raise PluginError(Exception("Exception encountered trying to locate certificate with name {} in compartment {}".format(certificate_name,compartment_id)))


        else:
            raise PluginError(Error("At a minimum you must provided either (A) the OCID for an existing certificate (via --oci-certificate-id) or (B) the OCID of a compartment"))

        logger.info("Plugin initialized")

    def prepare(self):
        pass

    def more_info(self):
        return "This plug-in installs the certificate into OCI Certificates Service"

    def get_all_names(self):
        # from the docs: "Returns all names that may be authenticated."
        # what does that mean?
        # ¯\_(ツ)_/¯
        return []

    def deploy_cert(self, domain, cert_path, key_path, chain_path, fullchain_path):
        """
        Actually upload Certificate to OCI Certificates service
        """

        def readFile(file):
            with open(file) as f:
                return (f.read())

        # this code is cribbed from the CLI
        # TODO: change this to use UpdateCertificateByImportingConfigDetails
        # i.e.:
        # from oci.certificates_management.models import UpdateCertificateByImportingConfigDetails

        _details = {}
        _details['certificateConfig'] = {}
        _details['certificateConfig']['configType'] = 'IMPORTED'
        _details['certificateConfig']['certChainPem'] = readFile(chain_path)
        _details['certificateConfig']['privateKeyPem'] = readFile(key_path)
        _details['certificateConfig']['certificatePem'] = readFile(cert_path)

        response = None

        if self.certificate_id:
            logger.info("Preparing certificate as new version of existing certificate with OCID {}".format(self.certificate_id))

            response = self.certificates_management_client.update_certificate(
                certificate_id=self.certificate_id,
                update_certificate_details=_details,
                **{}
            )

            logger.debug("Back from update call")

        else:
            # if there's no name then make one
            # NOTE: we waited until now (instead of doing it during the init) because you don't have the cert name then

            # the domain here is /probably/ a good name for the certificate in OCI Certs.

            # TODO: think about whether we should do another search to see if a cert with that name exists
            #       Reasons to do that: that's probably what they want
            #       Reasons to not: if that's what they wanted they would have told us that

            # this code tacks on a timestamp. I decided NOT to do that
            # I'm leaving the code here but commented out:
            #  (1) as a reminder that I changed my mind about this
            #  (2) as a warning to others that I changed my mind once about this already
            #  (3) in case I change my mind again
            from datetime import datetime
            name = "certbot-imported-cert-" + domain + datetime.now().strftime("-%Y%m%dT%H%M%S")

            # name = domain
            logger.debug("Automatically generated certificate name '{}'.".format(name))

            _details['name'] = name
            _details['compartmentId'] = self.compartment_id
            _details['description'] = "Certificate created via import using the certbot OCI Certificate Installer plugin"

            response = self.certificates_management_client.create_certificate(
                create_certificate_details=_details,
                **{}
            )
            logger.debug("Back from create certificate call")

        import json
        logger.debug("Response data: {}".format(json.dumps(oci.util.to_dict(response.data))))

    def enhance(self, domain, enhancement, options=None):  # pylint: disable=missing-docstring,no-self-use
        pass  # pragma: no cover

    def supported_enhancements(self):  # pylint: disable=missing-docstring,no-self-use
        return []  # pragma: no cover

    def get_all_certs_keys(self):  # pylint: disable=missing-docstring,no-self-use
        pass  # pragma: no cover


    def save(self, title=None, temporary=False):
        pass

    def rollback_checkpoints(self, rollback=1):
        pass

    def recovery_routine(self):
        pass

    def view_config_changes(self):
        pass

    def config_test(self):
        pass

    def restart(self):
        pass

    def renew_deploy(self, lineage, *args, **kwargs): # pylint: disable=missing-docstring,no-self-use
        """
        Renew certificates when calling `certbot renew`
        """

        # Run deploy_cert with the lineage params
        self.deploy_cert(lineage.names()[0], lineage.cert_path, lineage.key_path, lineage.chain_path, lineage.fullchain_path)

        return

interfaces.RenewDeployer.register(OCIInstaller)
