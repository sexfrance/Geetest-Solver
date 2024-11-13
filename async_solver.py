import hashlib
import random
import secrets
import time
import uuid
import json
from typing import Dict, Optional
from dataclasses import dataclass
from io import BytesIO

import aiohttp
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

class AsyncGeetestSolver:
    """Async solver for Geetest v4 captcha challenges."""
    
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

        from sync_solver import GeetestSolver
        return GeetestSolver()._load_image_index()

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

    async def solve(self, sitekey: str) -> GeetestResult:
        """
        Solve the Geetest captcha challenge asynchronously.
        
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

            async with aiohttp.ClientSession() as session:

                if self.debug:
                    self.log.debug("Making initial load request...")
                    
                async with session.get(
                    "https://gcaptcha4.geetest.com/load",
                    params={
                        "captcha_id": sitekey,
                        "challenge": challenge_id,
                        "client_type": "web",
                        "lang": "pl",
                        "callback": callback_name
                    }
                ) as first_response:
                    if first_response.status != 200:
                        return GeetestResult(
                            response=None,
                            elapsed_time_seconds=time.time() - start_time,
                            status="failure",
                            reason=f"Load request failed with status {first_response.status}"
                        )


                    response_text = await first_response.text()
                    json_data = json.loads(response_text.split(f"{callback_name}(")[1][:-1])
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
                        
                    async with session.get("https://static.geetest.com/" + json_data['data']['bg']) as image_response:
                        image_data = await image_response.read()
                        image_hash = str(phash(Image.open(BytesIO(image_data))))
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


                    async with session.get(
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
                    ) as verify_response:
                        elapsed_time = round(time.time() - start_time, 3)

                        if verify_response.status == 200:
                            verify_text = await verify_response.text()
                            verify_data = json.loads(verify_text.split(f"{callback_name}(")[1][:-1])
                            payload = verify_data.get('data', {}).get('payload', '')
                            
                            if self.debug:
                                self.log.debug(f"Verification successful")
                                self.log.debug(f"Full response: {verify_text}")
                            
                            self.log.message(
                                "Geetest",
                                f"Successfully solved captcha: {payload[:65]}...",
                                start=start_time,
                                end=time.time()
                            )
                            
                            return GeetestResult(
                                response=verify_text,
                                elapsed_time_seconds=elapsed_time,
                                status="success"
                            )
                        else:
                            if self.debug:
                                self.log.debug(f"Verification failed with status {verify_response.status}")
                                verify_text = await verify_response.text()
                                self.log.debug(f"Response: {verify_text}")
                                
                            return GeetestResult(
                                response=None,
                                elapsed_time_seconds=elapsed_time,
                                status="failure",
                                reason=f"Verification failed with status {verify_response.status}"
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

async def solve_geetest(sitekey: str, debug: bool = False) -> Dict:
    """
    Legacy wrapper function for backward compatibility.
    
    Args:
        sitekey: The Geetest site key (required)
        debug: Enable debug logging (optional)
    """
    solver = AsyncGeetestSolver(debug=debug)
    result = await solver.solve(sitekey=sitekey)
    return result.__dict__

if __name__ == "__main__":
    import asyncio
    
    async def main():
        result = await solve_geetest(
            sitekey="e392e1d7fd421dc63325744d5a2b9c73",
            debug=True
        )
        print(result)

    asyncio.run(main()) 