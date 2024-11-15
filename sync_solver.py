import hashlib
import random
import secrets
import time
import uuid
import json
from typing import Dict, Optional
from dataclasses import dataclass
from io import BytesIO

import requests
import rsa
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.PublicKey.RSA import construct
from PIL import Image
from imagehash import phash
from logmagix import Logger, Loader

@dataclass
class GeetestResult:
    """Data class to store Geetest solving results."""
    response: Optional[str]
    elapsed_time_seconds: float
    status: str
    reason: Optional[str] = None

class GeetestSolver:
    """Solver for Geetest v4 captcha challenges."""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.log = Logger()
        self.loader = Loader(desc="Solving Captcha...", timeout=0.05)
        self.e = int("10001", 16)
        self.n = int("00C1E3934D1614465B33053E7F48EE4EC87B14B95EF88947713D25EECBFF7E74C7977D02DC1D9451F79DD5D1C10C29ACB6A9B4D6FB7D0A0279B6719E1772565F09AF627715919221AEF91899CAE08C0D686D748B20A3603BE2318CA6BC2B59706592A9219D0BF05C9F65023A21D2330807252AE0066D59CEEFA5F2748EA80BAB81".lower(), 16)
        self.pubkey = construct((self.n, self.e))

        self.image_index = self._load_image_index()

    def _load_image_index(self) -> Dict[str, int]:
        """Load the image hash to position index mapping."""
        if self.debug:
            self.log.debug("Loading image index mapping...")
        return {'818056cdeef639e8': 221, 'cad27205bda50f72': 263, 'e7989e883927706b': 226, 'd06a2dad76c258e5': 256, '894936b61673497b': 223, 'eb659525dcf0c41a': 210, 'b23946e9dd9d1a11': 231, '8a5a95a50aeb55b5': 205, '8081758ecaf7b1f8': 245, 'd8d3526a4195f32d': 231, 'c984b669f296694b': 218, 'fb9a84b34b4a3895': 231, 'e8d22734ca5abca5': 246, '817f96d26139588f': 207, 'd8935a6a551af2a5': 247, 'ad16d62d32d509b6': 207, '868721da7750afa9': 245, 'e0e1161e2d2d3eb6': 207, 'cfb678688b95e0c1': 213, 'd2c2a5a5b5ad525a': 254, 'd02e1dcb62a559e5': 237, 'e05a5bb48d35a44f': 254, 'cba0b44bcb5ab435': 224, 'cded16e9c9129649': 218, 'e9d23724c25aace5': 201, '9931f7e9f0b04907': 220, 'ed96906cb5949369': 215, 'ca2a7d348fb5e0c1': 243, '8b4ad4a535d24b7a': 236, '8a5a95a42eca55bd': 221, '868fa1975352b789': 257, '894b36362969cf96': 217, 'db393696616c6c61': 206, 'eab590489d997366': 255, 'c9b6724db2820f73': 207, '896bd49436d5093f': 226, 'ad1665e99069b6d8': 211, 'ac06b6c56d3b92e8': 196, '817fb4d66139580f': 225, 'caa135d24a37b55a': 242, 'ca2ed925e78338f0': 253, 'c961b596d64a6935': 216, 'c5b8126ff8c230b7': 202, 'e5db52a0cd10b26f': 207, '8a5a95a42acb55bd': 238, 'f925a4b57a4a4936': 237, 'ea359c4ab5534ba4': 239, 'e896996eb548932d': 247, '818252ede6f239ec': 203, 'ebb6928c49493736': 222, '8a5af5a52ada0ab5': 243, 'cab6756a0bb5e0c1': 235, 'ef2f9021678339f0': 201, 'cb2f902bc38739f0': 230, 'cb7ab5254c519566': 250, 'ea36d28d95996362': 243, 'c821b757cd4ab235': 205, 'e0e1051e0b3f3ebc': 245, 'db3132866d6c6c93': 201, 'e5cb52b0cd28b24f': 204, '8a4d35625ab58d5b': 258, 'cfb632680b97f0c1': 212, 'aa06b5c5493bb5e8': 239, '894b34b43672c9bb': 227, '868ea1b5675a8f89': 247, 'd0261dca76b558e5': 246, 'ed169469b6336994': 222, '80c245ade5f539f8': 261, 'ba3eb5b0725233a1': 258, '81c94696d6f639e8': 217, 'eab4da489d4b3526': 242, '8f8fb097435ab688': 229, 'db3926a4656c6c69': 225, '9686a1b7675a9689': 268, 'cae316b4354b4b5a': 236, 'd8935a6a451bf2a5': 255, 'cd7ab46d4a5115a6': 214, '8f8f219617d2b788': 224, '8a5af5a525d64a3a': 252, 'da85b54ab3b54a4a': 248, 'cb548529da8a75d5': 246, 'c97ab5254a5b95a4': 258, 'f86ab5d36965b402': 242, 'cbb67e680b95e0c1': 218, '817e92cf65b2980f': 196, '818074ceeaf6b1e9': 235, 'a78721bf5368a788': 200, 'ed499494b673694c': 220, '8dc5b6966d699292': 209, 'eab690ad985b5326': 252, '817ebccba432588f': 234, 'c9b6734db4830e72': 219, 'cb85b54ab5896ab4': 240, 'c9ec1669db16c949': 222, 'cd7bb4064a5995a6': 221, '8a06a5c75a3ba7e8': 263, 'c972b46f5a5115a6': 219, 'ab3fb4b06170b293': 217, 'c7b8144bf8c630b7': 234, 'db31b66c6964c469': 215, 'f9daccb5a492384a': 235, 'e9da9124b548db69': 227, 'ed96926e69489669': 220, '868721da275ab7a9': 251, 'c16a1f9236a569e5': 213, 'ea15954a26b76b4c': 243, '818256cde6f239ec': 205, 'e6319d4aa5b34aa5': 264, 'f92524b6f2664963': 219, 'eba7d2849c9b6162': 219, 'e9de5369d610a04f': 217, 'c8d352ea4d1bb2a5': 206, 'f9a4242bb6e64936': 233, 'ea65b535da70841b': 256, 'eb659535da70c41a': 234, 'eba5d28c949b6562': 216, 'aaf5926ab5628933': 251, 'ae7a912599724ab3': 261, 'cb2a7d348fc5e0c1': 233, 'f82525ad7a668d32': 253, 'e7989e823867684f': 205, 'cb2b74368fc5e0c1': 228, 'c16a1f896fb610e5': 213, 'cd72b46d5a5115a6': 218, 'd06a3d9972ca59a5': 250, 'caa5b55ac60ee835': 243, '868721da6752b7a9': 251, 'cded1292d969c949': 211, 'ea5b95a5b45a4b84': 242, 'babd7c52215273a1': 262, 'ea13954a6ab7a54c': 243, 'ad7b923698694933': 215, 'cd72b50e5a4995ac': 216, 'b23967c3cd8d5215': 260, '9a31f5ea58b5c04b': 249, 'ad0cb6d209696fd8': 204, 'ab54852bda8375c9': 243, 'f924a5ad7a429936': 241, 'ad7a926d69329263': 204, 'e7989f8ab4636047': 238, '9931f7ea68b4c04b': 232, 'ab0b75c494336be8': 229, 'c9e42b6996699655': 225, 'cba6357a0b95e4c1': 237, 'e9d23734c05a99e5': 232, 'c9a096e36992967b': 215, 'caa5144b4bb6b64b': 232, '827eb5c5613258af': 251, '8a74b58a7ad5853a': 253, 'ed129669b69269cc': 217, '9a1bf7e578524087': 257, 'f9a624a972f64932': 217, '817cbccba43b188f': 236, 'e99a84b6476b6992': 225, 'ab3db4b260696393': 213, 'f825a5ad7a428d36': 249, 'ebb6d2499c996126': 224, 'ad7a926d49b2c865': 202, 'e8da9964b5949369': 237, 'e9c26716c21abce5': 205, 'db393626696c6c92': 221, 'cbaa3504fbc20db5': 239, 'adf69269943649b2': 215, 'cdf412699233e955': 215, 'caa5797a0f95e0c1': 249, 'e94ccd939692384f': 206, '9b39f7e478694007': 236, 'ea5b94b4664b6994': 234, 'cbae3444fbc20c75': 234, 'e9549629cd8376c9': 218, 'c992256d964abd35': 207, 'e8dd516a871868e7': 236, 'ca85b54ab5b54ab1': 237, 'cb2e902bc78739f0': 233, 'b53946e1cdcd9215': 205, 'c8d352e24d19f3a5': 223, 'b939f6e469719007': 209, 'e9d23734c24a99e5': 227, '8a5895a62caf55b5': 253, '8b35d28b354a957a': 240, 'e2df05b0ca35a44f': 257, '8a4a35b5347a4b9b': 241, 'e9d23716c04aade5': 205, 'c9c5b6966949b692': 220, 'f9a42ca9b6628d36': 224, 'c9b6764db9920e61': 221, 'da568521d68a7dc5': 256, 'ca4aa5b5954ab935': 239, 'daca2da53568723c': 256, '8a5a95a46aae55b9': 235, 'd2c2e4a5b5a5a55a': 255, 'aa4a75a595b17ac8': 242, '817eb8cba43b188f': 232, 'b13946e2dccd9a15': 207, 'a94c9632d48b6dd3': 204, 'cb2ed023c78769f0': 229, 'db548529da8375d1': 242, 'ed6a9659a965e412': 206, 'c8d3526a551ee9a5': 219, 'c8d35a6a551be1a5': 201, 'ad12776d92296f90': 206, 'cb8c16c32934737d': 213, 'ad16366d90336fd0': 208, '8d42366d39b2c9b9': 211, '817fb6d2e231482f': 206, 'da30672d6d664c69': 263, 'cdec1669c916e949': 214, 'c16a1e9867e958b5': 219, 'db3966a465646c69': 229, 'e7989ecc3823684f': 207, 'e0e1161e0d6d3eb6': 217, '817e96d26d31988f': 207, 'e2cd4572cf34604f': 246, 'ab0bb486947b6b68': 222, 'cbb679688f95e0c0': 226, 'ad163669903b6f94': 209, 'db3926a4616e6c69': 234, 'edb6da4d98892532': 202, 'db30666d27646cb1': 218, '8a8d357235724abd': 262, 'b23946c38ddf9215': 254, '9930f7e9b4714887': 225, 'ca61b596c64ae935': 218, 'cdec1269cb12ed49': 209, 'e0e1161e2d3736bc': 215, 'ab3ef4b434b06343': 232, '8a52d4ad2de5897a': 262, 'cb84b44bb4956b96': 233, 'db8e2cc31269733c': 207, 'c9a63644e9c31e76': 222, 'c7982165f9c21ab7': 255, 'ef2fd003c28739e1': 219, '8976d62969d6096b': 218, 'c8ed25da5a31b549': 259, 'f96a945ba965d212': 242, '8b4b34604bf685bb': 233, 'ed252c9ab2969d62': 203, 'cb7ab5254a591566': 249, 'cc21b396cd4ab935': 203, 'e99a84b6c74a781b': 230, 'ed969366b7488169': 206, 'eda5d2989c496566': 209, '9932f7e99669c007': 220, 'cb2fd027c78339e0': 230, 'cb2b7d340fc5e0c1': 229, 'cd7ab5064a5b95a4': 233, 'c5324f8936ed58a5': 210, 'cfb67a6c0b91e4c0': 200, 'cab5255a954ab535': 246, 'ea5b95adb4524a8c': 250, 'cab4b54b964a6935': 228, 'ebb692849c4b6b62': 230, 'f92524ae6b629c36': 222, 'e19ace616592396d': 198, 'ed969366254c9369': 207, 'e896916e53ad9368': 248, 'c598026ffac238b7': 202, 'eb659535cdf0841a': 206, 'ab6595359ef0c41a': 208, 'c97bb50e4a5195a6': 241, '9931f7e970b2410f': 212, 'ca75b54a4c5b95a4': 251, '8a5a95a46acb55b5': 217, 'b23946e39dcb9215': 250, 'd8d352ea491cb5a5': 233, 'cb2d79729295e4c1': 212, 'ba3eadb07230a393': 269, '8d4d12322d658fbb': 200, 'c9a5234b954bda55': 236, 'c9b6724db4830f72': 218, 'e19cce93c764381b': 201, 'ebb6da4994492536': 227, 'cbea7414b5920b73': 237, 'c9b416691396697b': 216, 'e0e1151e0f4b3ebc': 234, 'c06a1f9d36a558e5': 234, 'c9ed34cb4b359449': 235, 'cbc1b4b46b4bb494': 228, 'c7b8254afac230b7': 252, 'ea35984ab55b69a4': 243, 'b33946e1c99d9615': 226, '878621fb5752af84': 219, 'da38672565646c6b': 244, 'eae5b5349d71441a': 248, 'd893526a5519eba5': 234, 'e0e30d1d0f5a1ebc': 253, 'eda5d29898c96566': 207, 'caba3505bdd20a73': 260, '896dd69269e909b6': 213, 'eb27d294949b6962': 220, 'ab06b44b19b36be8': 230, 'c9925669967b6952': 215, 'ed92936cb5988369': 205, 'e0cb53b4cf10a46f': 231, 'f9a4b4a96b969462': 223, 'c56a1f9867a51a95': 201, '8080759dca73b1fd': 244, 'e0e1161f2d933eac': 206, 'dace2da12568723e': 256, 'ea1bb5a44a5b25a5': 241, 'eda6b22d6b928962': 207, 'f9a5240bb6e64936': 239, 'da31252d696e6c35': 251, 'f96a94d2a925d24b': 217, 'da31256d6b666c61': 246, 'cf2f9023438735f1': 235, '80c27595e67339f8': 241, '817e96cb6933980f': 210, 'abb67c7032712393': 223, 'c9b6724db2920f71': 206, 'c9e925b59535ca49': 237, 'cb5ab5a54e511566': 251, 'b13a46e9dc8d5a15': 214, 'e7989fca3c236846': 239, 'fa67945aa965d403': 249, '9a06a5c25a3bb7d8': 262, 'b23946e39dcd9215': 249, 'e0e1171e0b3b3eb4': 237, 'e8d553629758a0e7': 233, '827eb5c5627218af': 248, 'f9a4a4ab6bb48962': 227, 'cb14ce6bd40a75c9': 241, 'cb2b74760fc5e0c1': 226, 'e2cf05b2ca35a44f': 252, 'ef2f900367c730f0': 200, 'eae5b5349d70441b': 257, 'cb5ab5254cd195a6': 250, '8e8fa1b7434ab788': 235, 'da31256e6b246c6b': 251, '8a02a5e55a7bb7a4': 255, 'e99684636bb6381b': 222, 'e91396496db2334d': 221, '8a4a35b53572ca9b': 243, '8d4932b23969cd9b': 204, '9a3bf5e44a7ac007': 241, 'e992372ec25a98e5': 228, 'e0e1161e0bb73eac': 230, 'e0e1161e093f3ebc': 223, 'e9cb16b4cb49a04f': 226, 'cd92466d926dd2d2': 200, 'cde91296d229ed49': 214, 'db313664696c6cb1': 216, '817e96cd61b2582f': 201, 'edb692894d89b332': 201, 'ed929266b5498b69': 217, 'aa7e95655a24a533': 251, 'da30672d656e4c69': 255, '8f86a1db4750af89': 231, 'af3df09270616393': 200, 'ad52d62d32d50db2': 205, 'b33b46a1dd8d9a11': 229, 'cded1292d329ec49': 200, 'ce2ed921e78358f0': 258, 'cb9e16c1163a653e': 204, 'cb2fd821e78539e0': 236, 'c9e4364bdb34c949': 222, 'cded1692c9699649': 212, 'eb2792849ccb6366': 221, 'ab3f7cb034b03343': 229, '8916d42936ed93b6': 219, '8a0ab5a5997b5ae8': 253, 'c5b81247f9c232b7': 206, 'b13b46e9cd9e1a05': 214, 'e9da9964b4949369': 226, 'fa6a94d1a965d24a': 244, 'caa6756a0bb5e4c1': 239, '8949743416f2cdbd': 220, '8d49743612f2cdb9': 213, 'a97b9234c969c9b2': 223, 'cd7ab62d4a5315a4': 205, '8b36d40b36d6493e': 227, 'aa0ab5a5917b5ae8': 245, 'e7989e823863685f': 206, '827dbccaa532588f': 247, 'f96a965ba9a5d202': 227, 'c16a5f9836b459c5': 214, 'aa7d956a5aa5c922': 245, 'cb2fb123c38539f0': 244, 'ed96926c65c89369': 200, 'ad12766d92396f90': 209, 'c1361fc966b449e5': 221, 'c598036fda4638b7': 203, '8081658ecaf3b5fc': 245, 'abbef07060927369': 205, 'ab3eb47860b2b349': 226, 'ebe795259671841a': 208, 'd06a1d996aa33da5': 237, '89c5b6966949b696': 215, 'd8d352e2d51af225': 253, '8a5a95a52e9a55b5': 203, '817e92cf6532982f': 199, '808165cecaf7b1f8': 249, 'e7989f8239636067': 260, 'cde156929292677a': 207, '8a35d60a25da953f': 253, 'ab3f7cb434b03303': 230, 'e7989f84386b604f': 230, 'ef2fd803c28339e1': 202, 'c16a1e996fa712a5': 212, 'c16a1e9a67e958a5': 214, '8d4b12342d7393bb': 203, 'caa114b44b5ba7b3': 237, 'f966945ba965d602': 220, 'ba7a9125d8724ab3': 254, '8a5a95a56a8a55bd': 219, 'f96a94d1a965d243': 239, 'cb2f9123c38739f0': 240, 'aab5f47a30b06393': 240, 'b23946e1ddcd9215': 234, 'adf6926d9260c9b2': 209, '9a31f7cab4b14887': 245, 'e0cb55b4cf18a06f': 237, 'ad69923696b6c863': 215, 'da31666e256c4cb5': 238, 'e5da5224cf12a46f': 198, 'b931f7ec6892900f': 198, '9939f7e46869c087': 228, '9939f6e46961d407': 218, 'e0e1161e2d2f1ebc': 201, 'da3927a4696e6c29': 240, 'b23b65a1cdcb9215': 249, 'ad7b923698614973': 223, 'd0261dda37a55aa5': 247, 'e0f20e1d0e2d3eb6': 211, 'b939f6e668619087': 201, 'cd7ab20f4a5395a4': 205, 'd285a5865aada5da': 254, 'e9568c69d62974d1': 206, 'c921b616cd4bb635': 209, 'cf2fd023c68739e0': 229, '81c15696e66d39f2': 213, 'd2c2b5a5f34a4a96': 245, 'e0e10f1e0d371ebc': 265, 'adf2926d98b249b2': 208, 'c9e436699635c955': 229, 'c9b6794db2c11e61': 209, 'e0f30f1c0b2d3e96': 199, 'da31676e65646c31': 246, 'f9a5a40b73b44972': 237, 'ad06b6ed49b23668': 211, 'ab3eb4b06272b391': 232, 'cbb679688b95e0d0': 219, 'c984b469f394e54b': 225, 'ebe5952d9c71441a': 232, 'eb54846bd48369d5': 233, 'cd79b5165a59152c': 214, 'cbc3b4b4b6496a4a': 235, 'ad0db6d219696dc8': 207, 'e9d2372dc01a99e5': 210, 'f92725b573424972': 234, 'cdad7352b2920e65': 203, 'a78721bf5348b788': 202, 'cb2d79769295e0c1': 213, 'ea13946c6a33b5cc': 235, 'f96a94d1a965d24a': 235, 'c8935aea5519e3a5': 205, 'f96a94d0a965d24b': 232, 'c9b6724db4c30e72': 220, 'c984b469b6896bb6': 226, 'e8dd556acd14604f': 232, 'e2cd4572cd34624f': 248, 'c9b61669161b6b72': 218, 'ad06b6cd4933b6c8': 223, '9a1bf7e4b4b1404b': 245, 'caa5b54aca1ea935': 238, 'e0e1171e0d4b7eac': 234, 'e94accb296b6384b': 223, 'ed929b6cb5988169': 208, 'eb6595359c71c41a': 231, 'd8d350e24b1bb5a5': 239, 'd8d352e2555ae2a5': 244, 'e5da49a0da69a44f': 203, '817e96cd61b2588f': 207, 'c8e925b5cb5ad249': 249, 'abf5946a9cb44a32': 238, '8a4b35255a728dbd': 258, 'c5b8124ff9c230b7': 214, 'db30366d61a66c69': 210, 'cb7db54a4e5115a4': 237, 'fa262cadb5a58d42': 253, 'c9b416691796697a': 217, 'cf2d79728a95e0c1': 203, '8a5a95a52cab55b9': 243, 'f9a5a48b7ab48962': 234, 'db54852bd28375d1': 248, 'd8d3526a551ae3a5': 218, 'cde91296d269e949': 214, 'c9ab7254b4960f63': 227, 'cba116966b4bb692': 224, 'cb2fd823c68731e1': 229, 'cd7ab60e4a5995a4': 207, 'eb5c9435d48b69c1': 237, 'ba3cb57072b1b303': 249, 'ad02b66d49b376c8': 203, 'eb54846bd48b7cc1': 234, 'd205ce7af5026dd1': 267, 'ebb690c94999b562': 228, 'e99cce924769291b': 207, '81815696eb6b39f4': 223, 'c9ab3614b9cb0b72': 225, 'e98ccc9296626d6d': 204, 'ad84b62d6992b669': 207, 'c9af3216edc10e72': 214, 'abb6f47832306393': 217, 'c46e1f9a76a148e5': 198, 'e8cb55b4cb48a4c7': 227, '8a5995a4ad4a95bd': 252, '818056c9f6f339f4': 222, 'e9cb6736821a98e5': 213, 'f2dacdb5a512584a': 251, 'cbb636680b95f4c1': 217, 'a9569469d6836dd1': 213, 'cb27d003e7cb38f0': 237, 'f9a424ab7bb48962': 227, '81c17494e66b39fc': 234, 'cb9e0cc11639673e': 208, 'b33946e9dc8d1a15': 225, 'f0a52d8b72e48d72': 263, 'ab3fb4b460636391': 227, '8a5a95a46aab559d': 255, '8a5a95a56a8e55b9': 231, 'db30666d336c6c91': 210, 'a96dd69232d6096d': 210, 'c8d352e2951beb29': 222, '9913f7ed70b26007': 214, 'fa64965aa965f442': 246, 'da31676e65644ca5': 256, 'ea65b535da70c41a': 236, 'f962945ba965d292': 229, '8a5995a62dca55b5': 255, 'db55856ad4837ac1': 254, 'a916b66949b27e68': 215, 'e0e1251f0b5b3eb4': 249, '8687219b375ab789': 244, 'ebb69288c9c93726': 216, 'e996cc61966b389a': 216, 'e91b96946d6b2394': 224, 'abb6f46832926393': 211, 'eb16d949b46b6584': 229, 'b33946e1dc9d9215': 227, 'e5cb52b0cd18b44f': 208, 'cac206b5b5374b5a': 243, 'a96dd69232e5092f': 208, 'ef2f9023638730f1': 220, 'e7989f84bd276043': 257, 'f0a52c8ab1569d37': 265, 'c7b82547dac230b7': 250, 'aa7a90a59562cb73': 241, 'ef2f9023638734e1': 226, '8986366916f649bb': 219, 'c9a0166b6996967b': 223, 'e9db52b0c910b46f': 218, 'c7b81256fcc2382f': 223, 'd0261dca76a55ae5': 248, 'ed929366b5488b69': 221, 'd893526a553de2a5': 244, 'cd7ab6064a5995a6': 220, 'ef2ed021c3836df0': 202, 'da55857ad4837ac1': 252, '8d42326d38f2cdb9': 207, 'cd92126d139a6dd3': 201, 'eab590489d996b66': 247, 'ab659535dc71c41a': 215, 'e94d9632d6826dc9': 208, 'a9569669d4926dc9': 206, 'e4da4ba0de69a447': 203, 'c861b796d24ae935': 204, 'a9d23734c95a98e5': 215, '8687a1b7435ab789': 245, '9b31fbe0b46a844b': 237, 'aa0ab5a5197b5ae8': 241, 'e0e1161f0d173ebc': 210, 'e9568d29d60976c9': 209, 'f9a5a58a7ab48962': 239, 'cb9e16e11638653e': 206, 'eda4b4ad69929962': 209, 'c8a1b35fcd4ab035': 204, 'a956d62932d649b6': 209, 'cded12d3c9319649': 202, 'c9ad2b5aa55a944d': 248, 'af8f90966749a788': 211, 'ca40b5b5d64ae935': 240, 'ad65d2926ced09b2': 197, '8a5a95a40aeb55bd': 216, '9b39f5ec4a31a407': 243, 'c9af7616b9c10972': 213, 'dbac2cc33469633c': 234, 'cafa7505b5920a7a': 255, 'c9ad12d22d69723e': 210, 'e192cc61d267399b': 201, '8a35f54a35d44ab5': 243, 'f96a94d36965d203': 229, 'cb2fd023c3cb69e0': 225, 'c861b796d64a6935': 207, 'da31256e6d246c79': 248, 'db31366c6966c469': 219, 'f92625ad73425837': 246, 'a956d6292bd6093e': 212, 'aa14754b947b6ab4': 234, 'ebb69284994b6336': 224, 'cdfa026d9229e559': 208, '896dd69232d68d2d': 210, 'ab3d7cb032b233c1': 216, 'ad6dd69232d6092d': 202, 'ad7b9236d861c932': 218, 'c986b469b696695a': 217, 'aa7a95255a628db3': 251, 'e9252d9eb2969c32': 211, '8976d40b6bf4097a': 231, 'c8d352e2551aeba5': 237, 'e896773e845a98a5': 238, '817eb4cb61b4588f': 232, '81c95496f6f33968': 227, 'e992673cc24a9ce5': 224, 'c9b63444fb921c73': 233, 'fa6ab55a2925d213': 256, 'e5da5321cf10e44f': 204, 'd06a1d9d37a15ac5': 251, 'ab3df49232716383': 202, 'e5cb52b0cd10b26f': 210, 'caa034b54b5a67b5': 241, 'e0e1071a0db73eae': 237, 'ed92936c35929369': 207, 'ab6595359af0c41b': 207, 'e5da5324da38a44f': 200, 'ad0db6d290696de8': 200, '9a3bf5e55852c087': 253, 'e235da4aa5526d8d': 258, 'e94d8c32d6827dc9': 209, 'e7989e8639636057': 207, '8687219b675ab789': 248, 'e8da3734c05ab8e5': 239, 'ed969346354c9369': 198, 'e9549632dd8b74d0': 214, 'eab6908d9d4b6362': 246, '9939f6e66869d086': 220, 'aa02b5e5497bb6a4': 239, '9b31f7e848b4a44b': 229, '808165cecaf5b1fa': 245, 'b23b46a5dd8d5a11': 232, 'dace2da12568725e': 256, 'aafd906a9d244ab6': 244, '81c95696d67339e8': 208, 'daa5a55ac20bf835': 254, 'caba3505bbd20a75': 255, 'c598036ffa4a30b7': 210, 'fd6a96d26965d202': 207, '818565cae4f53bf0': 243, '9a39f5e45a70a507': 249, 'e0e10f1e1e933eac': 207, 'ca2fd903e78338f0': 256, 'e7989ec8bc236847': 221, 'ea65b534dcb1c41a': 256, 'abf4906b94344bb6': 233, 'edb6924d989b6522': 199, 'ed12c96db66b218c': 212, '818445cae4f73bf4': 238, 'f8a52d8a73a55872': 259, '81c97494e67339f8': 230, 'c7bc034afdc230b5': 256, 'da31252d696e6ca9': 257, 'ea6795359db1841a': 259, '8a5a95a52cab15bd': 261, 'e8d227b5c05ad8e5': 249, 'ce2fb12142cb39f1': 252, 'abb4b47870b073c3': 234, 'ed13926d6592694d': 203, 'f96a965ba925d212': 222, '8d4932b63969cd9a': 208, '8d86b66db2926d4a': 205, 'c06a1f9536a359e5': 235, 'da31676e65646c61': 241, 'ea65b535da71841a': 248, 'cda65252ade50e72': 196, 'e0e10e1e0db73eac': 229, 'cbad0cd29629673c': 211, 'db568521d58378da': 254, 'daca0cd1b52d631e': 242, 'c8d352e25519e9ad': 218, 'ca2a7d340fd7e0c1': 241, 'cb2f70760be5e0c1': 221, 'c3980677fcc2383b': 236, 'daa1a55ada0ba535': 254, 'fd6a9659a925e412': 210, 'cab23545fac22d35': 251, 'e99ace616592391b': 204, 'e992372ec21a99e5': 229, 'ad92f46d92696c92': 200, 'ed13926d6d92314d': 214, 'cb7db54a4a5117a4': 248, '9939f7e4b4b4c00b': 232, 'caba7505b5d20a73': 248, 'ef2f9003c3cb29f0': 217, 'e8d54b629558a4e7': 233, 'cab4b54b964aa935': 224, 'cd92466d926d6792': 205, 'e0e10f1e0db53eac': 229, '827db5ca61b5580f': 253, '827dbccaa572188f': 244, '8a4a742535b5cd9b': 258, 'e7989e8439637057': 217, '8a02b5e54a7bb7e0': 248, '8a02b5e54a3bb7e4': 247, 'a9d2772cc24ab8e5': 205, 'eb54846ad48b69d5': 240, '817f92d2613558af': 202, 'd8935a6a453df2a4': 257, 'cab63548fa852d72': 254, 'c9b6724db9920f61': 205, 'cded1292cb69c549': 204, '818444cdf6f339f4': 221, 'daa1a556da4aa535': 259, '81cb4494f4f739e8': 232, 'db312624696e6cb5': 236, '868ea1b5675ab689': 256, 'e996cc6b8632391b': 224, 'e996cc6986b26996': 214, 'a9d26734c24abce5': 203, 'edb6924d8c9b3164': 198, '896dd69236e5092f': 209, '89867961366b86bb': 224, 'c9e925b5c94bca49': 236, 'eb659535d871c41a': 228, 'ebb6928c99496966': 221, '81c97494e6733be8': 230, 'b939f7d292b2400f': 201, 'e9db3734825a88e5': 221, 'd8935a6a5519f2a5': 253, 'caa114b45b5a67b5': 240, 'c9ac16d22d69763c': 212, 'fa6a955aa965d203': 259, 'aa3eb5b062b0b393': 243, '8081658ecaf7b9f8': 253, 'ad52d2a96dd2923a': 201, 'daad2dc23568633c': 248, 'f92724b4b7664962': 232, 'f9daccb5a492380b': 231, 'b23965e3c99d9215': 241, 'c5b81252f84f38b7': 208, 'c9ad254a9535da55': 242, 'c8ad255a8d35da4d': 251, 'f29a8db14a5a3c95': 251, 'f25accb1a5b4385a': 250, 'c1361dc966b459e5': 232, 'ed13926d36926d4c': 209, 'c7b8254af8c630b7': 254, 'ef26d029c6cb29f0': 217, '9a39f5e44a72a487': 244, 'c9b63444fbc21e74': 233, 'b23b65e1c8cf9215': 241, '8180568cedf7b2ec': 215, '8b4b34b4307b4b9b': 230, 'caae3d740bd1e4c1': 242, '8a5a95a46ce955b5': 205, 'ca61b596964ae935': 218, '9a4935721ab58d9b': 262, 'fda62cadb2648d12': 196, '817eb6cb6932980f': 221, 'cd7ab40f4a5395a4': 215, '8a35f50a3ef50a3a': 248, 'c9b6704db6c30e72': 216, 'db30666d33646cb2': 205, 'e998cc92c66b691b': 219, 'd8935a6a551ae3a5': 237, 'e9d2372cca1a98e5': 223, 'ca21b537ca4ab535': 236, 'e0e1161b0db73eac': 228, 'e7989e8c3823686f': 208, '8976d4896bd4953a': 222, 'e992372ec29a89e5': 228, '9930ffe9b469c007': 220, 'edb6d24d98896532': 208, 'e2cd4bb28d58a44f': 253, 'f96a94d2a965d243': 223, 'c97eb54b4e5115a4': 229, 'ebe795259279841a': 211, 'db960dc31669633c': 210, '868fa1b7634ab784': 237, 'd893526a551ceba5': 233, 'eab79448d8993762': 245, '817e3ccde225982f': 199, 'ab3df4b232316361': 205, 'e1e10e1e0e373eac': 216, 'daa5a55a954a7835': 245, 'a90bb6c6496977c8': 215, '807eb495e533584f': 238, 'e0e10f1a2d1b3ebc': 248, 'e7989e84386b684f': 225, 'ab3db4b060697393': 216, 'abf4906b94244bb7': 237, 'e7989f84386b6057': 234, 'c0361dcb76b549a5': 235, '827eb585e5325a0f': 250, 'ea1bb5a5625a6585': 244, 'e99e84634bb6384b': 226, 'fd6a94d2a925d443': 200, '8a52b5ad7a5289b5': 255, 'c99e16c12d32673d': 213, 'c9b67249b4920f75': 225, 'e9da6734821a99e5': 224, 'c598126dfac238b7': 203, 'edb592989c496566': 204, 'c8ca25b5ad35d24b': 251, 'c9c5b6a46909b6da': 218, 'e2cd43728d58a0ef': 252, 'e996916e71949369': 228, 'f86ab5d16965d403': 255, 'e9da9924b58c9369': 237, '9931f7e868b4c44b': 219, 'daad25d2182d735a': 249, 'ba3eb5b430527293': 248, 'af8690bb6352b689': 212, 'ea35954ab5b34b84': 248, '9b31f7ea68b4404b': 236, '9a31f7caf4b54007': 241, 'c7980365fdc63833': 248, 'ca2ed921e78738f0': 255, 'cab6356a0bb5e4c1': 236, 'e7d89e84b4a76047': 241, 'cab23505fad20e75': 250, 'e8d22534ca1abde5': 258, 'aab5f47a34b06391': 239, 'ca2f9125c3cb38f1': 250, '817dbcd2e2b2182f': 205, 'c9ed16d349399649': 218, 'd06a3d9d66ca58a5': 247, 'cded1292d96de448': 198, 'caaa7505b5960b6b': 243, 'cded1292d229ed49': 200, 'c99e16c12d3a673c': 212, '817eb4cb6ab4184f': 236, 'a8d27724c25abce5': 199, 'e7989f823c636067': 245, 'ebb592949c496566': 214, 'eda5da88989b2566': 200, 'd06a0f9d37a558c5': 246, 'f96a95db6925d202': 239, 'c1321f8966b659e5': 217, 'e7989ec83827684f': 221, 'cab62505fad20e75': 264, 'c9b6724db6830e72': 214, 'a97b9424496bcdb2': 229, '8a0ab5a5957b5ad8': 254, '8dca72651273cd9a': 193, 'caa47d7a0bb5e0c1': 257, '8a52f5a52dd25a3a': 249, 'cd92126d13926d7b': 201, 'aa3eb4b062b2b393': 237, '818074caebf5b1ea': 233, 'cb2f902343cb39f1': 233, 'ad167569926976c8': 209, 'e9569629cd8276c9': 211, 'ea13b52d5a52a5a5': 255, '8180748eeaf3b5f8': 234, 'cb2d79728a95e4c1': 215, 'caa5a55ac60be935': 248, 'f2daccb5a592384a': 243, '81c94496f6f639e8': 207, 'c9e936969239e949': 218, 'ab3df0b260617393': 196, '8f8f21b63750a789': 225, 'c0361dcb76b449e5': 232, 'e7989e84bd27604b': 254, 'e7989e843923706f': 208, 'e896994ab5cc532d': 252, 'a976d2896dd4923a': 207, 'da31676e65244c79': 257, '8f8621db575aa788': 228, 'fa6ab5d16945d023': 253, 'eb179449b4736994': 229, '8b74f40b2cf40b7a': 237, 'cb2f9103e78578f0': 240, 'abb67c303261b393': 210, 'ed13924c6d3393cc': 203, 'aa7a91a59d624a73': 250, 'cbb4164b37b44b92': 225, 'cde5569292926d6a': 200, 'cbad16d22969723c': 215, 'ca2fd903e78318f1': 255, 'e8d22536ca1abce5': 250, 'f8a52c8ab5529d72': 256, 'e992772cc24ab8e5': 214, '8a5a95a52aea55b5': 206, 'c9a52b4b954b9555': 229, 'ea13952c6a5bb594': 239, 'fa9a8db5c54a5819': 243, 'caae3d740bd3e0c1': 242, 'b33846e9dc8d5a15': 225, '8a857262357a8dbb': 241, 'e19cce92656d3992': 204, 'c97eb44f4ad115a4': 224, 'db30666d636c6c13': 204, 'ed969b6cb448932c': 217, 'b939f3e66c619083': 200, 'a78fb0966749a788': 217, 'dbb604c31669633e': 216, 'c16b1f9236a159e5': 218, 'ab06b6c949b3b6c8': 221, 'd8d352ea451ae3a5': 211, 'e0cb53b4cf18e04f': 238, 'db393664696c6c31': 220, 'ebb69249989b6166': 218, 'ed12986d966b6994': 206, 'ec929925b55a9369': 261, 'f92625b5f3424972': 241, 'ad69923692b6c963': 214, 'a9d23716c24aade5': 207, 'cfb679688ba5e0c0': 211, 'ad769269c8b6c923': 219, 'eae595349d70c41b': 251, 'da85e4cab54ab495': 243, 'b939f3f26c65c003': 194, '8a5a95a42aeb55b5': 213, 'b23946e3dd8d1a15': 245, 'c2a54652b55aa7b3': 252, 'e0e1161e0d6b7eac': 225, 'cfae72720be5e0c0': 202, 'db31266c6964e479': 233, 'b33946e0cdcd9a15': 223, 'ea5b95a5b4134b4c': 240, 'ea5b95a5365a4b84': 245, 'b23946e3dd8d5215': 243, 'b33b46e1c9cd9215': 230, 'eb54846bd48379d1': 239, 'da31674e6d644ca5': 264, 'e2b5da489d5b2526': 261, '868ea1b5675ab788': 244, 'e2dd5562cd34604f': 243, '8f8621db375aaf80': 230, 'e9568c69d60b74c9': 222, 'f8262dadb3465872': 264, 'ed13964c6d93968c': 214, 'd8935aea551ab1a5': 258, 'c865b592d24aed35': 201, 'aaf5926ab562c833': 245, 'c9e4264b943bcb55': 226, 'fa6a95d1a965d242': 249, '8b4b34b4307b49bb': 236, 'c9a116f2691a967b': 215, 'c9f41669d236c94d': 221, 'e7989e883927606f': 219, 'cab5424ab55b26b6': 238, 'e8da3734c05ad8e5': 235, '8916d62936d749b6': 214, 'cab4a54b964ae935': 229, 'c5b90256fcc238b7': 226, '9931f7e9b0b44907': 226, 'fa5accb5a5b4380a': 245, 'f9a4248bb666c936': 234, '8d4d12b22d6dcd9a': 199, 'a9f6926b942449b7': 228, '8a5895a66aad55b5': 253, 'b23b65a1d9cb9215': 252, 'ea65b534daf1841a': 258, 'f86a95db6965d402': 240, 'e9d21734c95a98e5': 204, 'e0e1161e0b373ebc': 236, 'f96a96d26965d203': 211, 'ea13b56c5a52a58d': 251, '8e8e21b5675aaf88': 240, 'daca25b53568623e': 245, 'ebe5b52d9471441a': 234, '8a02b5a5587b7eac': 253, '9913f7ed78b2400b': 208, 'a78790976752b788': 206, 'e0f30f1d0b253e96': 201, 'cab67d6a0bb5e0c0': 244, 'c9e934b44b4bb455': 234, '8b847b60347b85bb': 237, 'cab63544fac22d65': 248, 'c16a1f9c76e94985': 225, 'cc90b36dd25a2d35': 197, 'e8966736c04abce5': 234, 'b13a47e1dccd9215': 219, 'c16a1e896fb618e5': 216, 'da38666d65246c79': 256, 'ea17954a62b7694c': 241, 'ab3df4b232716341': 219, 'c9b0b66dca1aa935': 217, 'e9de5369d6106847': 214, 'eb13940c6b5bb594': 225, 'ebe5952d9479841a': 226, '80c265b5ea7239f5': 246, 'f96a94d2a965d04b': 220, 'aa35b57262b1334b': 242, 'c9ed244bd135ca55': 236, 'ebe595259671c41a': 213, 'e896916e5a8c9769': 245, 'ca2a7d348fd5e0c1': 246, 'da058c7ab5827dc5': 262, 'cded1296c9699649': 211, 'da85b54ab3a54a5a': 244, 'e7989f84bd23604b': 251, 'e0e30f1c2d371e2e': 242, 'c7b4024bfcc238b7': 224, 'eb4b9494b43369cc': 228, '968d70703d528dbb': 263, 'cb74b50a4e5b95a4': 234, 'fb9684434bb6381b': 229, 'ad7f9227496492b2': 209, 'f925a4b4736a4936': 227, 'fa2625ad7252d872': 252, 'cd7bb4164a5915a6': 223, 'cb85b4864b95b55a': 241, '8a35f50a6af50b3a': 237, '8a5af5a52aca0b3e': 245, '8d4932b62969cf9a': 209, '817eb4c46b329c8f': 231, 'c9e146929696676b': 211, 'aa7a94a59d624a73': 242, 'f966945ba965d212': 231, 'cdb67244ed831a72': 203, 'fa6a94d9a965d242': 260, 'e7989e843963704f': 213, '8687219b774ab789': 239, 'e8cb54b4cb58a44f': 224, 'db54a529d28a75c5': 257, 'cded1292c9699659': 211, 'e94d8c32d69275c9': 218, 'caa5344a1bb56b5a': 238, 'f9a42da9b6699432': 227, 'a916b66990b36fc8': 213, 'da31256c6b246c7b': 260, 'cd79b5164a5935a4': 211, 'cdb67244ed821a73': 203, 'ca3a79748fb5e0c0': 251, '8dc5b696696da292': 209, '808565cae6f53af8': 253, '9939f7f4b460484b': 230, 'ea6395359d71c41a': 248, 'eda6242d72964d72': 210, 'b23947c3dd8d5215': 250, '808565dae5f33ae4': 254, 'f925a5a96a669532': 236, 'c7b80256fcc238b7': 225, 'e7989ec8b8236857': 216, 'befdd262ad428522': 261, '868ea1b5475a97a9': 254, 'f99e84736bb23049': 226, '8f8f21963790b789': 227, 'c2a125d25a3fa57a': 254, 'e2cd49728d18e0ef': 263, 'c7bc024bf8c238b7': 237, 'aa7a95a59d624a72': 253, '8d4936b612714dbb': 210, 'ca69b596964aa935': 226, 'aab57c7034723393': 235, '896dd49236d6913e': 206, 'caae357a0b95e4c1': 237, 'c9ed1669c9369649': 223, '9a39f5e45a72c407': 249, 'c97bb5064e5195a6': 229, 'c97ab5244e51956e': 233, 'cab23505bdd20e75': 256, '8a5a95a5689a55bd': 203, 'f9a52c8ab5429d36': 247, 'aa3eb4b06272b393': 237, '8f8621fb5658af88': 222, 'bab57c7234523391': 255, 'c6b82567f84238b7': 254, 'db8b24d63469633a': 229, 'cb85b54ab5896ad2': 235, 'c1324fc936e95995': 210, '923b65a1cdcf5215': 253, '8a5a95a52cca55bd': 252, '894936b62969cf9a': 217, 'c7b8124bf8c238b7': 224, 'cac207b5b57a4a5a': 245, 'da85b5825aa5b55a': 249, 'db30666d676c4c31': 218, '8f87a19b43d0b789': 234, 'cb2f902343cb35f1': 229, 'cab47d6a0bb5e0c1': 240, 'dbac34c30b69353c': 235, 'ce2ed921e7831af0': 255, '8a35b50a6af50b7a': 251, 'd0255f9a27c239e5': 254, 'cab5144a1bb56b5a': 237, 'abb4f47a30b06393': 237, '8d92366d1271c9bb': 215, '808546dee57239fc': 256, 'c53a1f89679258e5': 209, 'c5b81256f84b38b7': 222, 'c9ab3614b9cb0b74': 223, 'fa6ab55aa925d203': 255, '8a5a95a5689e55b9': 222, '817fb6d26035492f': 206, '8a05754a957b7ab4': 244, 'cbb678688f95e0c1': 216, 'c9924e699669b6d2': 214, '8a5a95a568ca55bd': 216, '817fb6d66131580f': 218, 'ad7a926d49b29265': 201, '8a8d727235528dbd': 255, 'da31256c6b64ec69': 247, '81815696ef6939f4': 218, 'daad25d21c2d631e': 252, 'a954963bcd8b74d0': 209, 'db3926a6696c6c61': 217, 'e44d4bb2db12a44f': 197, '8180748ecaf7b5f8': 233, 'a78621fd535aa788': 203, 'caae3d780bd5e4c0': 244, 'd06e2d9a76a519c5': 252, 'cdec126dda12e951': 208, 'c7bc024efd4230b7': 258, 'c7b81647f8c230b7': 230, 'c5b0036bfa4b30b7': 218, 'c8d352ea491eb2ad': 222, 'c5b81252f94e38b7': 204, 'cdb42b6992699659': 217, '817fbcd4e430584f': 233, 'ebb6924989993566': 220, 'cac205b5b57b4a5a': 247, 'b23946e9dd8d9215': 236, 'caa63d7a0bb5e4c0': 258, '9a31f7cab4b54087': 248, 'cab63544fa822d75': 246, 'ed252492b2f64d63': 207, 'cded1292c96de449': 197, 'ea65b535de70441a': 254, 'c969b596964aa935': 214, '818056cde6f639e9': 214, 'dbac34c30a2c773c': 234, 'ed1b929a6d6b2194': 202, 'db31366c6964e469': 220}

    def _aes_encrypt(self, text: str, sec_key: str, iv: bytes, style: str = 'pkcs7') -> bytes:
        """Encrypt text using AES encryption."""
        encryptor = AES.new(sec_key.encode('utf-8'), AES.MODE_CBC, iv)
        pad_pkcs7 = pad(text.encode('utf-8'), AES.block_size, style=style)
        return encryptor.encrypt(pad_pkcs7)

    def _get_guid(self) -> str:
        """Generate a GUID for the request."""
        return ''.join(secrets.token_hex(2) for _ in range(4))

    def _encrypt_payload(self, data: str) -> str:
        """Encrypt the payload using RSA and AES encryption."""
        if self.debug:
            self.log.debug("Encrypting payload...")
            
        guid = self._get_guid()
        ciphertext = rsa.encrypt(guid.encode(), rsa.PublicKey(self.n, self.e)).hex()
        encrypted = self._aes_encrypt(data, guid, b"0000000000000000").hex()
        return encrypted + ciphertext

    def _get_random(self) -> int:
        """Generate a random number for the callback."""
        return round(random.uniform(0, 1) * 10000) + round(time.time() * 1000)

    def solve(self, sitekey: str) -> GeetestResult:
        """
        Solve the Geetest captcha challenge.
        
        Args:
            sitekey: The Geetest site key (required)
            
        Returns:
            GeetestResult object containing the solution details
        """
        self.loader.start()
        start_time = time.time()

        try:

            challenge_id = uuid.uuid4()
            callback_name = f"geetest_{self._get_random()}"

            if self.debug:
                self.log.debug(f"Starting captcha solve with sitekey: {sitekey}")
                self.log.debug(f"Challenge ID: {challenge_id}")
                self.log.debug(f"Callback name: {callback_name}")


            if self.debug:
                self.log.debug("Making initial load request...")
                
            first_response = requests.get(
                "https://gcaptcha4.geetest.com/load",
                params={
                    "captcha_id": sitekey,
                    "challenge": challenge_id,
                    "client_type": "web",
                    "lang": "pl",
                    "callback": callback_name
                }
            )

            if first_response.status_code != 200:
                return GeetestResult(
                    response=None,
                    elapsed_time_seconds=time.time() - start_time,
                    status="failure",
                    reason=f"Load request failed with status {first_response.status_code}"
                )


            json_data = json.loads(first_response.text.split(f"{callback_name}(")[1][:-1])
            lot_num = json_data['data']['lot_number']
            
            if self.debug:
                self.log.debug(f"Lot number: {lot_num}")
                self.log.debug(f"Process token: {json_data['data']['process_token']}")
            

            guid = self._get_guid()
            pow_msg = f"1|0|md5|{json_data['data']['pow_detail']['datetime']}|{sitekey}|{lot_num}||{guid}"
            pow_sign = hashlib.md5(pow_msg.encode()).hexdigest()
            device_id = hashlib.md5(str(random.uniform(0, 1)).encode()).hexdigest()

            if self.debug:
                self.log.debug(f"Generated GUID: {guid}")
                self.log.debug(f"POW message: {pow_msg}")
                self.log.debug(f"POW sign: {pow_sign}")
                self.log.debug(f"Device ID: {device_id}")


            if self.debug:
                self.log.debug("Downloading and processing challenge image...")
                
            image_response = requests.get("https://static.geetest.com/" + json_data['data']['bg'])
            image_hash = str(phash(Image.open(BytesIO(image_response.content))))
            set_left = self.image_index.get(image_hash, 0) - 41

            if self.debug:
                self.log.debug(f"Image hash: {image_hash}")
                self.log.debug(f"Calculated set_left: {set_left}")


            passtime = random.randint(500, 700)
            userresponse = set_left + random.uniform(0, 1)
            
            if self.debug:
                self.log.debug(f"Generated passtime: {passtime}")
                self.log.debug(f"Generated userresponse: {userresponse}")

            w_data = {
                "device_id": device_id,
                "em": {"ph": 0, "cp": 0, "ek": "11", "wd": 1, "nt": 0, "si": 0, "sc": 0},
                "ep": "123",
                "gee_guard": None,
                "geetest": "captcha",
                "lang": "zh",
                "lot_number": lot_num,
                "passtime": passtime,
                "pow_msg": pow_msg,
                "pow_sign": pow_sign,
                "setLeft": set_left,
                "userresponse": userresponse,
                "yeg6": "d6w9"
            }

            if self.debug:
                self.log.debug("Encrypting payload...")
                
            encrypted_w = self._encrypt_payload(json.dumps(w_data))

            if self.debug:
                self.log.debug("Making verification request...")


            verify_response = requests.get(
                "https://gcaptcha4.geetest.com/verify",
                params={
                    "callback": callback_name,
                    "captcha_id": sitekey,
                    "client_type": "web",
                    "lot_number": lot_num,
                    "payload": json_data['data']['payload'],
                    "process_token": json_data['data']['process_token'],
                    "payload_protocol": "1",
                    "pt": "1",
                    "w": encrypted_w
                }
            )

            elapsed_time = round(time.time() - start_time, 3)

            if verify_response.status_code == 200:
                verify_data = json.loads(verify_response.text.split(f"{callback_name}(")[1][:-1])
                payload = verify_data.get('data', {}).get('payload', '')
                self.loader.stop()
                
                if self.debug:
                    self.log.debug(f"Verification successful")
                    self.log.debug(f"Full response: {verify_response.text}")
                
                self.log.message(
                    "Geetest",
                    f"Successfully solved captcha: {payload[:50]}...",
                    start=start_time,
                    end=time.time()
                )
           
                
                return GeetestResult(
                    response=verify_response.text,
                    elapsed_time_seconds=elapsed_time,
                    status="success"
                )
            else:
                self.loader.stop()
                if self.debug:
                    self.log.debug(f"Verification failed with status {verify_response.status_code}")
                    self.log.debug(f"Response: {verify_response.text}")
                    
                return GeetestResult(
                    response=None,
                    elapsed_time_seconds=elapsed_time,
                    status="failure",
                    reason=f"Verification failed with status {verify_response.status_code}"
                )

        except Exception as e:
            elapsed_time = round(time.time() - start_time, 3)
            if self.debug:
                self.log.debug(f"Error during solve: {str(e)}")
            self.log.failure(f"Failed to solve captcha: {str(e)}")
            return GeetestResult(
                response=None,
                elapsed_time_seconds=elapsed_time,
                status="failure",
                reason=str(e)
            )

        finally:
            self.loader.stop()
            if self.debug:
                self.log.debug(f"Solve attempt completed in {elapsed_time} seconds")

def solve_geetest(sitekey: str, debug: bool = False) -> Dict:
    """
    Legacy wrapper function for backward compatibility.
    
    Args:
        sitekey: The Geetest site key (required)
        debug: Enable debug logging (optional)
    """
    solver = GeetestSolver(debug=debug)
    result = solver.solve(sitekey=sitekey)
    return result.__dict__

if __name__ == "__main__":
    result = solve_geetest(
        sitekey="e392e1d7fd421dc63325744d5a2b9c73"
    )
    print(result)

