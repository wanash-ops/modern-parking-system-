# MMU Automated Smart Parking Management System

An auditable, full-stack smart parking solution built with Python, Flask, SQLite3, and Tailwind CSS. The system enforces dynamic management pricing, VAT compliance, and multi-channel payment reconciliation.

## Key Objectives & Implemented Features
* **Live Slot Availability Board**: Real-time entrance visualization displaying total capacity, available bays, and occupied bays alongside a dynamic 12-bay grid (A1–B6).
* **Automated Arrival & Exit Control**: Sequential first-fit bay allocation with gate lock/open barrier logic.
* **Dynamic Management Rates**: Pricing tiers are fetched and managed directly via the database, allowing management to update parking rates on the fly without changing source code.
* **Statutory 16% VAT Compliance**: Computes gross payable amounts, statutory 16% VAT account deductions, and net revenue automatically upon checkout.
* **Multi-Channel Payment Processing**: Supports **M-PESA**, **Card**, and **Cash** payment verification before lifting the exit barrier.
* **Audit & Financial Reconciliation**: Comprehensive transaction trail tracking entry/exit timestamps, vehicle plates, duration, payment method, and exact revenue splits.

## Tech Stack
* **Backend**: Python 3, Flask
* **Database**: SQLite3
* **Frontend**: HTML5, Tailwind CSS, JavaScript (Fetch API)
* **Version Control**: Git & GitHub

## Local Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone [https://github.com/wanash-ops/modern-parking-system-.git](https://github.com/wanash-ops/modern-parking-system-.git)
   cd modern-parking-system-