# 🎓 Secure Student Portal

A secure web application built with Python Flask where students can view their marks and admins can manage records, featuring login authentication, role-based access control, and protection against SQL Injection, XSS, CSRF, and Brute Force attacks.

## Features
- 🔐 Secure Login & Registration
- 👨‍🎓 Student Dashboard (View Marks)
- 👨‍💼 Admin Panel (Add/Delete Marks)
- 🔒 Brute Force Protection (Account Lockout)
- 🛡️ CSRF Protection
- 🚫 SQL Injection Prevention
- 🚫 XSS Prevention
- 📋 Security Logging

## Tech Stack
- Python Flask
- SQLite + SQLAlchemy
- Bootstrap 5
- bcrypt
- Flask-WTF

## How to Run
pip install flask flask-sqlalchemy flask-login bcrypt flask-wtf
py app.py

## Security Features
| Attack | Prevention Method |
|--------|------------------|
| SQL Injection | SQLAlchemy ORM prepared statements |
| XSS | Jinja2 auto-escaping |
| Brute Force | Account lockout after 5 attempts |
| CSRF | Flask-WTF token validation |
| Unauthorized Access | RBAC + Flask-Login |

## Project By
Ibraheem Ahmed — KIET
Secure Software Development Project
