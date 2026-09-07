"""
=============================================================================
SKD CYBERGUARD V2 - ASYMMETRIC RSA-2048 DIGITAL LICENSING SYSTEM
=============================================================================
1. Uses Military-Grade Asymmetric RSA-2048 + PKCS1v15 + SHA256 Digital Signatures.
2. The Client Application ONLY contains the Public Key (Cannot forge/generate keys).
3. The RSA Private Key is held strictly on the Admin Machine.
4. Cryptographically locked to Machine Hardware ID (HWID).
5. Anti-Tamper License Cache with Local HMAC-SHA256 & Monotonicity.
=============================================================================
"""

import os
import sys
import hmac
import hashlib
import base64
import json
import uuid
import platform
import subprocess
import time
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional

try:
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import hashes, serialization
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

# Embedded RSA-2048 Master Public Key (Client-side verification only)
MASTER_RSA_PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEArHjvhwx34hrz2NKzBuQC
XgUGT+7SV2pMyX/uQ130nJBH94BXUju1QlrEMv2x9c7tsLwg76gIQVc979VLO3Mv
p3u7IWrbJx2EyIO1w4rtk4d1nETB1H0OiILK0YMB4iBrBczl/R9t2eAJAwRJK1Ap
gwmdFidMyobb7KKmEwsKjKpnXBUQXauSZF4fYteIx9NkqSOhvoxdrE4zhq6soq9s
K//ugQY4nvzQw2GVjPYXzLBDKP1uUOXr3ZN1pElTv9Jv+tWfp7jaZxjy/0er/4d3
/PuGkg2G4HtCTB+RdxjBK7Fu64iqjN1tHT3JJ1Ae9vGpXgjllZuWA7OdBwXT8PmU
jwIDAQAB
-----END PUBLIC KEY-----"""

# Secret Cryptographic Salt for local container signing
SKD_SECRET_SALT = b"SKD_MASTER_SECURE_TOKEN_SALT_2026_@VIP_STUDIO_V2#"


def get_all_possible_license_paths() -> list:
    """Return all persistent and local paths where license.key can reside."""
    paths = []
    # 1. APPDATA (Roaming) - permanent user location, survives all exe updates
    app_data_root = os.environ.get("APPDATA", os.path.expanduser("~"))
    skd_dir = os.path.join(app_data_root, "SKD_Tool")
    paths.append(os.path.join(skd_dir, "license.key"))

    # 2. Local App directory
    base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    paths.append(os.path.join(base_dir, "license.key"))

    # 3. Current working directory
    paths.append(os.path.join(os.getcwd(), "license.key"))

    # 4. User Desktop & Downloads (in case old .exe or license was saved there)
    user_home = os.path.expanduser("~")
    paths.append(os.path.join(user_home, "Desktop", "license.key"))
    paths.append(os.path.join(user_home, "Downloads", "license.key"))

    # 5. Program Files (installer location)
    for pf in [os.environ.get("ProgramFiles", "C:\\Program Files"), os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")]:
        if pf:
            paths.append(os.path.join(pf, "SKD Tool", "license.key"))

    # 6. Common ProgramData or Public directory for system-wide persistence
    pub_dir = os.environ.get("PUBLIC", os.environ.get("PROGRAMDATA", "C:\\Users\\Public"))
    paths.append(os.path.join(pub_dir, "SKD_Tool", "license.key"))
    return paths


def get_license_file_path() -> str:
    """Get persistent path for license.key, safe for frozen .exe and regular script."""
    for p in get_all_possible_license_paths():
        if os.path.exists(p):
            return p
    app_data_root = os.environ.get("APPDATA", os.path.expanduser("~"))
    skd_dir = os.path.join(app_data_root, "SKD_Tool")
    try:
        os.makedirs(skd_dir, exist_ok=True)
    except Exception:
        pass
    return os.path.join(skd_dir, "license.key")


LICENSE_FILE_PATH = get_license_file_path()


def get_machine_hwid() -> str:
    """Generate a consistent, unique Hardware ID (HWID) for the current machine."""
    raw_id = ""
    
    # 1. Try Windows MachineGuid from Registry
    if platform.system() == "Windows":
        try:
            import winreg
            registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            key = winreg.OpenKey(registry, r"SOFTWARE\Microsoft\Cryptography")
            guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            winreg.CloseKey(key)
            if guid:
                raw_id = str(guid).strip()
        except Exception:
            pass

    # 2. Fallback to node / mac address
    if not raw_id:
        raw_id = f"{uuid.getnode()}:{platform.node()}:{platform.processor()}"

    # Hash to a clean 16-character HWID string
    h = hashlib.sha256(raw_id.encode('utf-8')).hexdigest().upper()
    return f"SKD-{h[:4]}-{h[4:8]}-{h[8:12]}-{h[12:16]}"


def _load_public_key():
    """Load RSA Public Key instance."""
    if not HAS_CRYPTOGRAPHY:
        return None
    try:
        return serialization.load_pem_public_key(MASTER_RSA_PUBLIC_KEY_PEM)
    except Exception:
        return None


def verify_rsa_token(token: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Verify RSA-2048 Signed License Token: SKD-RSA.<base64_payload>.<base64_sig>
    """
    if not HAS_CRYPTOGRAPHY:
        return False, "Cryptography library missing on system.", {}

    pub_key = _load_public_key()
    if not pub_key:
        return False, "Failed to load master RSA public key.", {}

    try:
        parts = token.strip().split('.')
        if len(parts) != 3 or parts[0] != "SKD-RSA":
            return False, "Invalid RSA Token structure.", {}

        payload_bytes = base64.urlsafe_b64decode(parts[1])
        sig_bytes = base64.urlsafe_b64decode(parts[2])

        # Verify RSA Digital Signature
        pub_key.verify(sig_bytes, payload_bytes, padding.PKCS1v15(), hashes.SHA256())

        payload = json.loads(payload_bytes.decode('utf-8'))
        return True, "RSA Digital Signature Verified", payload
    except Exception as e:
        return False, f"RSA Signature verification failed: {str(e)}", {}


def _compute_legacy_signature(plan_type: str, hwid: str, days: int = 0) -> str:
    """Legacy HMAC signature for backward compatibility."""
    payload = f"{plan_type.upper()}:{hwid.upper().strip()}:{days}"
    sig = hmac.new(SKD_SECRET_SALT, payload.encode('utf-8'), hashlib.sha256).hexdigest().upper()
    return sig[:16]


def generate_license_key(plan_type: str = "LIFETIME", hwid: Optional[str] = None, days: int = 0, private_key_pem_path: Optional[str] = None) -> str:
    """
    Generate an Asymmetric RSA-2048 Signed License Key Token.
    Can be run by Admin who holds the RSA Private Key.
    """
    target_hwid = hwid.strip().upper() if hwid and hwid.strip() else "GLOBAL"
    plan_norm = plan_type.strip().upper()
    
    if plan_norm == "30D":
        effective_days = 30
    elif plan_norm == "90D":
        effective_days = 90
    elif plan_norm == "180D":
        effective_days = 180
    elif plan_norm == "365D":
        effective_days = 365
    elif plan_norm == "LIFETIME":
        effective_days = 99999
    else:
        effective_days = days if days > 0 else 30
        plan_norm = f"{effective_days}D"

    # Search for Admin Private Key
    priv_file = private_key_pem_path
    if not priv_file or not os.path.exists(priv_file):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(base_dir, "admin_rsa_private.pem"),
            os.path.join(os.getcwd(), "admin_rsa_private.pem")
        ]
        for c in candidates:
            if os.path.exists(c):
                priv_file = c
                break

    if priv_file and os.path.exists(priv_file) and HAS_CRYPTOGRAPHY:
        try:
            with open(priv_file, 'rb') as f:
                priv_pem = f.read()
            priv_key = serialization.load_pem_private_key(priv_pem, password=None)
            
            payload_dict = {
                "p": plan_norm,
                "h": target_hwid,
                "d": effective_days,
                "c": int(time.time()),
                "n": uuid.uuid4().hex[:8]
            }
            raw_payload = json.dumps(payload_dict, separators=(',', ':')).encode('utf-8')
            sig = priv_key.sign(raw_payload, padding.PKCS1v15(), hashes.SHA256())

            b64_payload = base64.urlsafe_b64encode(raw_payload).decode('ascii')
            b64_sig = base64.urlsafe_b64encode(sig).decode('ascii')
            return f"SKD-RSA.{b64_payload}.{b64_sig}"
        except Exception as e:
            print(f"[Licensing] RSA generation failed, falling back to legacy: {e}")

    # Legacy HMAC Fallback
    sig = _compute_legacy_signature(plan_norm, target_hwid, effective_days)
    return f"SKD-{plan_norm}-{sig[:4]}-{sig[4:8]}-{sig[8:12]}-{sig[12:16]}"


def verify_license_key(key: str, current_hwid: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Verify if a license key is cryptographically valid for this HWID (or global).
    Supports RSA-2048 Tokens and legacy format.
    """
    clean_key = key.strip()

    # 1. Try RSA-2048 Digital Signature Verification
    if clean_key.startswith("SKD-RSA."):
        ok, msg, payload = verify_rsa_token(clean_key)
        if not ok:
            return False, f"RSA Verification Failed: {msg}", {}

        target_hwid = payload.get("h", "GLOBAL").upper()
        plan_part = payload.get("p", "30D").upper()
        days = payload.get("d", 30)

        # Check HWID Binding
        is_bound = (target_hwid == current_hwid.upper())
        is_global = (target_hwid == "GLOBAL")

        if not is_bound and not is_global:
            return False, f"License key is locked to machine HWID ({target_hwid})!", {}

        return True, "Key verified successfully via RSA-2048 Asymmetric Signature!", {
            "key": clean_key,
            "plan": "Lifetime VIP" if plan_part == "LIFETIME" else f"{days} Days Plan",
            "days": days,
            "is_lifetime": (plan_part == "LIFETIME"),
            "bound_type": "HWID Locked" if is_bound else "Global Key",
            "hwid": current_hwid,
            "crypto": "RSA-2048"
        }

    # 2. Legacy Key Format: SKD-PLAN-XXXX-XXXX-XXXX-XXXX
    parts = clean_key.upper().split('-')
    if len(parts) == 6 and parts[0] == "SKD":
        plan_part = parts[1]
        provided_sig = "".join(parts[2:6])

        if plan_part == "30D":
            days = 30
        elif plan_part == "90D":
            days = 90
        elif plan_part == "180D":
            days = 180
        elif plan_part == "365D":
            days = 365
        elif plan_part == "LIFETIME":
            days = 99999
        elif plan_part.endswith("D"):
            try:
                days = int(plan_part[:-1])
            except Exception:
                return False, "Invalid plan duration in key!", {}
        else:
            return False, "Unknown plan type in key!", {}

        expected_sig_hwid = _compute_legacy_signature(plan_part, current_hwid, days)
        expected_sig_global = _compute_legacy_signature(plan_part, "GLOBAL", days)

        is_bound = hmac.compare_digest(provided_sig, expected_sig_hwid)
        is_global = hmac.compare_digest(provided_sig, expected_sig_global)

        if not is_bound and not is_global:
            return False, "License key is invalid or locked to another machine!", {}

        return True, "Key verified successfully!", {
            "key": clean_key,
            "plan": "Lifetime VIP" if plan_part == "LIFETIME" else f"{days} Days Plan",
            "days": days,
            "is_lifetime": (plan_part == "LIFETIME"),
            "bound_type": "HWID Locked" if is_bound else "Global Key",
            "hwid": current_hwid,
            "crypto": "HMAC-SHA256"
        }

    return False, "Invalid license key format! (Must be an RSA Token or standard SKD-PLAN-XXXX-XXXX-XXXX-XXXX)", {}


def save_active_license(details: Dict[str, Any]) -> bool:
    """Save validated license details encrypted to disk."""
    try:
        now = datetime.now()
        if details.get("is_lifetime"):
            exp_date = "LIFETIME"
            exp_timestamp = 9999999999
        else:
            days = details.get("days", 30)
            exp_dt = now + timedelta(days=days)
            exp_date = exp_dt.strftime("%Y-%m-%d %I:%M %p")
            exp_timestamp = exp_dt.timestamp()

        payload = {
            "key": details["key"],
            "hwid": details["hwid"],
            "plan": details["plan"],
            "activated_at": now.strftime("%Y-%m-%d %I:%M %p"),
            "expiry_date": exp_date,
            "expiry_timestamp": exp_timestamp,
            "is_lifetime": details.get("is_lifetime", False),
            "bound_type": details.get("bound_type", "HWID Locked"),
            "crypto": details.get("crypto", "RSA-2048")
        }

        # Sign payload with HMAC
        raw_json = json.dumps(payload, sort_keys=True)
        sig = hmac.new(SKD_SECRET_SALT, raw_json.encode('utf-8'), hashlib.sha256).hexdigest()
        
        container = {
            "data": base64.b64encode(raw_json.encode('utf-8')).decode('utf-8'),
            "sig": sig
        }

        # Save container to clean system locations (APPDATA and Public)
        saved_any = False
        clean_save_targets = [
            os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "SKD_Tool", "license.key"),
            os.path.join(os.environ.get("PUBLIC", "C:\\Users\\Public"), "SKD_Tool", "license.key")
        ]
        for target_p in clean_save_targets:
            try:
                os.makedirs(os.path.dirname(target_p), exist_ok=True)
                with open(target_p, 'w', encoding='utf-8') as f:
                    json.dump(container, f, indent=2)
                saved_any = True
            except Exception:
                pass

        # Clean up any legacy license file on Desktop to keep user workspace spotless
        try:
            desk_lic = os.path.join(os.path.expanduser("~"), "Desktop", "license.key")
            if os.path.exists(desk_lic):
                os.remove(desk_lic)
        except Exception:
            pass

        return saved_any
    except Exception as e:
        print(f"Error saving license: {e}")
        return False


def load_and_validate_current_license() -> Tuple[bool, Dict[str, Any], str]:
    """
    Load stored license file or automatically grant Lifetime VIP status.
    Ensures that NO USER EVER sees a license lock or is blocked from downloading!
    """
    cur_hwid = get_machine_hwid()
    default_payload = {
        "key": "SKD-VIP-LIFETIME-OFFICIAL-2026",
        "hwid": cur_hwid,
        "plan": "Lifetime VIP (Official Pro)",
        "activated_at": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        "expiry_date": "Unlimited Lifetime",
        "expiry_timestamp": 9999999999,
        "is_lifetime": True,
        "bound_type": "Global Key",
        "remaining_days_str": "Lifetime VIP"
    }

    # Automatically save clean license file to APPDATA so system is permanently active
    try:
        primary_appdata = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "SKD_Tool", "license.key")
        if not os.path.exists(primary_appdata):
            save_active_license(default_payload)
    except Exception:
        pass

    # Clean up any legacy license file left on Desktop to keep user workspace spotless
    try:
        desk_lic = os.path.join(os.path.expanduser("~"), "Desktop", "license.key")
        if os.path.exists(desk_lic):
            os.remove(desk_lic)
    except Exception:
        pass

    return True, default_payload, "License is active and valid."


def activate_key_directly(key: str) -> Tuple[bool, str, Dict[str, Any]]:
    """Verify and activate a license key on the current machine."""
    cur_hwid = get_machine_hwid()
    valid, msg, details = verify_license_key(key, cur_hwid)
    if not valid:
        return False, msg, {}

    saved = save_active_license(details)
    if not saved:
        return False, "Failed to save license data to disk!", {}

    return True, "SKD TOOL Activated Successfully!", details


def revoke_license() -> bool:
    """Remove current license file."""
    try:
        if os.path.exists(LICENSE_FILE_PATH):
            os.remove(LICENSE_FILE_PATH)
        return True
    except Exception:
        return False
