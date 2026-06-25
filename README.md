# 💸 SplitWise Backend Clone (Django + DRF + MySQL)

> **"Managing shared expenses shouldn't be complicated."**

A backend implementation of a SplitWise-inspired expense management system built using **Python, Django, Django REST Framework, and MySQL**. This project focuses on solving real-world expense sharing with optimized debt calculation, wallet management, settlement tracking, and ledger-based auditing.

---

# 📖 The Story

Imagine three friends go on a weekend trip.

* One pays for the hotel.
* Another pays for fuel.
* Someone else pays for dinner.

By the end of the trip, nobody remembers who owes whom.

That's where this project begins.

Most expense-sharing applications simply record transactions.

I wanted to go one step further.

Instead of only storing expenses, I designed a backend that continuously calculates who owes whom, automatically simplifies debts, supports partial settlements, maintains complete payment history, and minimizes unnecessary money transfers.

The goal wasn't just to build REST APIs.

The goal was to design a backend system that applies real software engineering concepts such as transaction management, database normalization, concurrency control, ledger architecture, and debt optimization.

---

# 🚀 Features

## 👤 User Management

* Create Users
* Wallet Creation
* Add Money to Wallet
* Wallet Balance Management

---

## 💰 Expense Splitting

Currently supports **Equal Split**.

Example:

```text
Restaurant Bill = ₹3000

User A pays

Members:
A
B
C

Each owes ₹1000
```

The creator's wallet is immediately debited because they initially paid the entire expense.

---

## 📊 Net Balance Optimization

Instead of storing duplicate debts,

```text
A owes B ₹1000
B owes A ₹700
```

the system automatically simplifies it into

```text
A owes B ₹300
```

This significantly reduces unnecessary settlements.

---

## ⚖️ Settlement Management

Every pending payment generates a Settlement record.

Settlement Status:

* PENDING
* PAID

Settlement amounts are automatically updated whenever debt offsets occur.

---

## 📒 Settlement Ledger

Every modification made to a settlement is permanently recorded in the Settlement Ledger.

Supported Ledger Events:

```text
SPLIT_CREATED
PARTIAL_OFFSET
NET_OFFSET
PAYMENT
```

Nothing is overwritten.

Everything remains traceable and auditable.

---

## 💳 Wallet Management

Every successful payment performs an atomic wallet transfer.

```text
Debtor Wallet
      │
      ▼
Money Transfer
      │
      ▼
Creditor Wallet
```

Money is never duplicated or lost.

---

## 💵 Payment System

Supports

### ✅ Single Split Payment

```http
POST /split_payment/
```

### ✅ Bulk Split Payment

```http
POST /pay_multiple_splits/
```

Multiple pending settlements can be paid with a single API request.

---

## 📈 Debt Simplification Logic

The backend automatically handles three scenarios.

### Case 1

```text
Reverse Debt > Current Debt
```

The existing reverse debt is reduced.

---

### Case 2

```text
Reverse Debt == Current Debt
```

Both debts completely cancel each other.

---

### Case 3

```text
Current Debt > Reverse Debt
```

The reverse debt is fully consumed and only the remaining balance is stored.

---

# 🏗️ Database Design

Core Tables

```text
User

Wallet

Split

Split Members

Settlement

Settlement Ledger

Transactions

Net Balance
```

Each table has a single responsibility, resulting in a clean and normalized database structure.

---

# 🔄 Project Workflow

```text
Create User
      │
      ▼
Add Money
      │
      ▼
Create Split
      │
      ▼
Generate Settlements
      │
      ▼
Update Net Balance
      │
      ▼
Create Ledger Entry
      │
      ▼
User Pays
      │
      ▼
Wallet Updated
      │
      ▼
Settlement Closed
      │
      ▼
Ledger Updated
      │
      ▼
Split Automatically Closed
```

---

# 🧠 Engineering Concepts Used

* Django ORM
* Django REST Framework
* MySQL
* Transaction Management
* Atomic Operations
* Row-Level Locking (`select_for_update`)
* Foreign Keys
* Query Optimization
* Settlement Ledger Pattern
* Debt Netting Algorithm
* REST API Design
* Exception Handling
* Database Normalization
* Business Logic Design

---

# ⚡ Interesting Challenges Solved

## Reverse Debt Cancellation

```text
User A owes User B

Later,

User B owes User A
```

Instead of creating two separate debts, the backend automatically offsets them and stores only the remaining balance.

---

## Settlement History

Instead of modifying historical data, every change is recorded inside a Settlement Ledger.

This provides a complete audit trail.

---

## Wallet Consistency

Every wallet transfer is wrapped inside a database transaction.

Either

```text
Both wallets update successfully.
```

or

```text
Nothing is updated.
```

No partial transactions are possible.

---

# 📌 Current Limitations

This project is intentionally focused on backend business logic.

Current limitations include:

* Equal Split only
* No authentication (planned)
* No recurring expenses
* No notifications
* Designed for moderate-scale usage
* Multi-split settlement optimization can be further enhanced

These trade-offs helped keep the project focused on correctness, maintainability, and financial logic.

---

# 📚 What I Learned

Building this project taught me that backend development goes far beyond creating CRUD APIs.

It involves designing systems that preserve data integrity, simplify complex financial workflows, and remain consistent even when multiple users interact with the application simultaneously.

Through this project, I strengthened my understanding of:

* Database Design
* Transaction Management
* Backend Architecture
* Financial System Design
* Business Logic Implementation
* Audit Logging
* Clean Code Practices

---

# 🛠️ Tech Stack

* Python
* Django
* Django REST Framework (DRF)
* MySQL
* JSON APIs
* Postman

---

# 👨‍💻 Author

## Deepak Harish T M

**Backend Developer | Python | Django | DRF | MySQL**

📧 Email: **[harishdeepak35@gmail.com](mailto:harishdeepak35@gmail.com)**

📱 Mobile: **+91 8778658798**

🌐 Portfolio: **https://deepakharish-murali-portfolio.vercel.app**

💼 LinkedIn: **https://linkedin.com/in/deepak-harish-t-m**

---

> *"Every project is another opportunity to solve a real-world problem through code."*
