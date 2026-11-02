# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT
import datetime
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

import vision_permanent_component_cloud as delivery


def archive(files):
    output=io.BytesIO()
    with tarfile.open(fileobj=output,mode='w:gz') as tar:
        for name,raw in files.items():
            info=tarfile.TarInfo(name);info.size=len(raw);tar.addfile(info,io.BytesIO(raw))
    return output.getvalue()


class PermanentComponentTests(unittest.TestCase):
    def test_only_two_accepted_fixed_component_envelopes(self):
        from aos_signer.cloud_common.schemas.v2.cloud_income import AosUploadMetaConfig
        for kind,version in delivery.VERSIONS.items():
            config=delivery.configuration(kind);AosUploadMetaConfig.model_validate(config)
            self.assertEqual(config['items'][0]['version'],version)
        with self.assertRaises(ValueError):delivery.configuration('main-rootfs')

    def test_services_packet_is_a_separate_exact_immutable_profile(self):
        from aos_signer.cloud_common.schemas.v2.cloud_income import AosUploadMetaConfig
        self.assertEqual(delivery.SERVICES_VERSIONS,{delivery.ROOTFS:'6.1.1-vision-camera.6',delivery.CAMERA:'0.1.2'})
        for kind,version in delivery.SERVICES_VERSIONS.items():
            new=delivery.configuration(kind,services_packet=True);AosUploadMetaConfig.model_validate(new)
            self.assertEqual(new['items'][0]['version'],version)
            self.assertEqual(delivery.configuration(kind)['items'][0]['version'],delivery.VERSIONS[kind])

    def test_streaming_rootfs_signature_and_payload_binding(self):
        import jwt
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes,serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives.serialization import pkcs12
        from cryptography.x509.oid import NameOID
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'unit-only-fixture')])
        now=datetime.datetime.now(datetime.timezone.utc)
        certificate=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(1).not_valid_before(now-datetime.timedelta(days=1)).not_valid_after(now+datetime.timedelta(days=1))
            .sign(key,hashes.SHA256()))
        payload=b'hsqs'+b'non-bootable unit fixture'
        config=json.dumps(delivery.configuration(delivery.ROOTFS)).encode()
        batch=archive({'config.yaml':config,'rootfs/image.squashfs':payload})
        claims=dict(data=[dict(name=n,size=len(raw),hash=hashlib.sha3_512(raw).hexdigest())
                          for n,raw in (('config.yaml',config),('batch.tar.gz',batch))])
        signed=jwt.encode(claims,key,algorithm='RS256').encode()
        raw=archive({'config.yaml':config,'batch.tar.gz':batch,'package.sign':signed})
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);credential=root/'unit.p12';bundle=root/'bundle.tar.gz'
            credential.write_bytes(pkcs12.serialize_key_and_certificates(b'unit',key,certificate,None,serialization.NoEncryption()))
            credential.chmod(0o600);bundle.write_bytes(raw)
            digest=hashlib.sha256(payload).hexdigest()
            observed=delivery.verify(bundle,credential,delivery.ROOTFS,digest,len(payload))
            self.assertEqual(observed['signatureVerification'],'VERIFIED_RS256')
            for expected,bytes_ in (('0'*64,len(payload)),(digest,len(payload)+1)):
                with self.assertRaisesRegex(ValueError,'PAYLOAD_CHANGED'):
                    delivery.verify(bundle,credential,delivery.ROOTFS,expected,bytes_)
            with self.assertRaisesRegex(ValueError,'SIGNED_DIGEST_CHANGED'):
                delivery.verify(bundle,credential,delivery.ROOTFS,digest,len(payload),'0'*64)


if __name__=='__main__':unittest.main()
