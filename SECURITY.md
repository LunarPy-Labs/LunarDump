# Security Policy 🔐

At **LunarDump**, security is a top priority. As a zero-trust database backup tool, we take data privacy, encryption integrity, and vulnerability management very seriously.

---

## 🛡️ Supported Versions

We release security patches for the following versions of LunarDump:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

---

## 🚨 Reporting a Vulnerability

**Please do NOT report security vulnerabilities via public GitHub issues.**

If you discover a security vulnerability or suspect a cryptographic issue in LunarDump, please disclose it responsibly by following these steps:

1. **Email Disclosure**: Send a detailed report to **indhifarhandika@gmail.com** (or use GitHub Private Vulnerability Reporting if enabled on the repository).
2. **Include Details**:
   - A clear description of the vulnerability and potential security impact.
   - Step-by-step instructions or proof-of-concept (PoC) code to reproduce the issue.
   - The version of LunarDump and Python environment where the issue was observed.
3. **Response Timeline**:
   - **Initial Acknowledgement**: Within **48 hours**.
   - **Assessment & Status Update**: Within **5 business days**.
   - **Patch Release**: High-severity vulnerabilities will receive a hotfix release promptly.

We ask that you give us reasonable time to address the issue before making any public disclosure.

---

## 🔒 Zero-Trust Security Architecture

LunarDump is designed with a **Zero-Trust** security philosophy:

- **Local AES-256-GCM Encryption**: Dumps are encrypted locally on-the-fly using authenticated AES-256-GCM mode before any bytes are transmitted to remote cloud storage.
- **Zero Raw Credential Storage**: Database passwords, encryption keys, and cloud credentials should be provided via environment variables (`.env`) or key files—never stored raw inside public version control.
- **Keyfile Permissions**: Generated key files (`secret.key`) are automatically assigned `0600` (read-write for owner only) permissions.

---

## 💡 Recommended Security Best Practices for Users

1. **Protect Your Encryption Key**:
   - If you lose your AES-256 encryption key, **your backup files (.enc) cannot be decrypted**.
   - Store backup encryption keys in a secure secrets manager (AWS Secrets Manager, GCP Secret Manager, Vault, or 1Password).

2. **Never Commit `.env` or `config.yaml` with Passwords**:
   - Ensure `.env`, `*.key`, and `*.enc` are listed in `.gitignore`.
   - Use `password_env`, `key_env`, and `bot_token_env` fields in `config.yaml` to reference environment variables.

3. **Cloud IAM Least Privilege**:
   - Grant your S3 / GCS service accounts the minimum permissions required (`s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`, `s3:ListBucket`).

---

Thank you for helping keep **LunarDump** and its users secure! 🚀
