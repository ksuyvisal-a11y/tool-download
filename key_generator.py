#!/usr/bin/env python3
"""
⚡ SKD TOOL - Admin License Key Generator (Enterprise RSA-2048 Edition)
Generates mathematically unforgeable RSA-2048 cryptographically signed activation keys.
"""

import sys
import os
from datetime import datetime
from licensing import generate_license_key, get_machine_hwid

def print_banner():
    print("=" * 70)
    print("   ⚡ SKD TOOL - ADMIN RSA-2048 KEY GENERATOR v7.0 ENTERPRISE        ")
    print("=" * 70)
    print(f" Admin Machine HWID: {get_machine_hwid()}")
    print(" Digital Signature: RSA-2048 PKCS1v15 + SHA256 (Zero-Forgery)")
    print("=" * 70)

def main():
    print_banner()
    while True:
        print("\n[ SELECT PLAN TYPE ]")
        print(" 1. 30 Days Plan (1 Month)")
        print(" 2. 90 Days Plan (3 Months)")
        print(" 3. 180 Days Plan (6 Months)")
        print(" 4. 365 Days Plan (1 Year)")
        print(" 5. Lifetime VIP License (No Expiration)")
        print(" 6. Custom Days Plan")
        print(" 7. Batch Generate Keys (Export to File)")
        print(" 0. Exit")
        
        choice = input("\nEnter choice [0-7]: ").strip()
        if choice == "0":
            print("\nExiting SKD Key Generator. Goodbye!")
            break

        plan_map = {
            "1": ("30D", 30),
            "2": ("90D", 90),
            "3": ("180D", 180),
            "4": ("365D", 365),
            "5": ("LIFETIME", 99999),
        }

        if choice in plan_map:
            plan_code, days = plan_map[choice]
            hwid_input = input("\nEnter Customer HWID (leave empty for Global key): ").strip()
            key = generate_license_key(plan_type=plan_code, hwid=hwid_input if hwid_input else "GLOBAL", days=days)
            
            print("\n" + "#" * 70)
            print(f" 🎉 GENERATED RSA-2048 KEY:\n{key}\n")
            print(f" 📋 Plan:          {plan_code} ({'Lifetime VIP' if plan_code == 'LIFETIME' else f'{days} Days'})")
            print(f" 🔒 Bound HWID:     {hwid_input if hwid_input else 'GLOBAL (Works on Any Machine)'}")
            print(f" 📅 Created At:     {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")
            print("#" * 70)
            
            # Save to keys log
            with open("generated_keys_log.txt", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Key: {key} | Plan: {plan_code} | HWID: {hwid_input or 'GLOBAL'}\n")
            print(" (Key saved to generated_keys_log.txt)")

        elif choice == "6":
            try:
                custom_days = int(input("\nEnter duration in days (e.g. 15, 60, 120): ").strip())
                if custom_days <= 0:
                    print("Invalid days!")
                    continue
                hwid_input = input("Enter Customer HWID (leave empty for Global key): ").strip()
                key = generate_license_key(plan_type=f"{custom_days}D", hwid=hwid_input if hwid_input else "GLOBAL", days=custom_days)
                
                print("\n" + "#" * 70)
                print(f" 🎉 GENERATED RSA-2048 KEY:\n{key}\n")
                print(f" 📋 Plan:          {custom_days} Days")
                print(f" 🔒 Bound HWID:     {hwid_input if hwid_input else 'GLOBAL'}")
                print("#" * 70)
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "7":
            try:
                count = int(input("\nHow many keys to generate? (e.g. 10, 50): ").strip())
                plan_code = input("Enter Plan Type (30D, 180D, 365D, LIFETIME): ").strip().upper() or "30D"
                filename = f"batch_keys_{plan_code}_{int(datetime.now().timestamp())}.txt"
                
                keys = []
                for _ in range(count):
                    k = generate_license_key(plan_type=plan_code, hwid="GLOBAL")
                    keys.append(k)

                with open(filename, "w", encoding="utf-8") as f:
                    f.write("\n".join(keys) + "\n")

                print(f"\n✅ Successfully generated {count} RSA-2048 keys into: {filename}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    main()
