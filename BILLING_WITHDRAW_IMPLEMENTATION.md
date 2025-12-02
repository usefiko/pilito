# Billing Information & Withdrawal System - Implementation Summary

## Overview

This document describes the implementation of the Billing Information and Withdrawal Request system, allowing users to manage their banking details and request withdrawals from their wallet balance.

---

## 🎯 Features Implemented

### 1. **Billing Information Management**
- Users can add, update, view, and delete their banking information
- Required before making withdrawal requests
- Stores: First Name, Last Name, Sheba Number (IBAN), Bank Name
- One-to-one relationship with User model

### 2. **Withdrawal Request System**
- Users can request withdrawals from their wallet balance
- Minimum withdrawal amount: 100 Tomans
- Automatic wallet balance deduction upon request
- Wallet transaction logging for audit trail
- Multiple status states: pending, processing, paid, rejected, cancelled

### 3. **Admin Panel Management**
- Complete admin interface for both models
- Withdrawal status management with color-coded displays
- Bulk actions: mark as paid, processing, or rejected
- Automatic refund handling for rejected withdrawals
- Track who processed each withdrawal and when

---

## 📊 Database Models

### BillingInformation Model

```python
class BillingInformation(models.Model):
    user = OneToOneField(User)  # One billing info per user
    first_name = CharField(max_length=100)
    last_name = CharField(max_length=100)
    sheba_number = CharField(max_length=26)  # IBAN format
    bank_name = CharField(max_length=100)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

### Withdraw Model

```python
class Withdraw(models.Model):
    user = ForeignKey(User)
    amount = DecimalField(max_digits=10, decimal_places=2)
    status = CharField(choices=['pending', 'processing', 'paid', 'rejected', 'cancelled'])
    date = DateTimeField(auto_now_add=True)
    processed_date = DateTimeField(null=True, blank=True)
    processed_by = ForeignKey(User, null=True, blank=True)
    admin_notes = TextField(blank=True)
    wallet_transaction = OneToOneField(WalletTransaction, null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

---

## 🔌 API Endpoints

All endpoints require JWT authentication.

### Billing Information APIs

#### 1. Get Billing Information
```http
GET /api/v1/billing/billing-information/
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user": 123,
  "user_email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "sheba_number": "IR123456789012345678901234",
  "bank_name": "Sample Bank",
  "created_at": "2025-12-02T10:30:00Z",
  "updated_at": "2025-12-02T10:30:00Z"
}
```

**Response (404 Not Found):**
```json
{
  "message": "No billing information found"
}
```

#### 2. Create Billing Information
```http
POST /api/v1/billing/billing-information/
Authorization: Bearer {token}
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "sheba_number": "IR123456789012345678901234",
  "bank_name": "Sample Bank"
}
```

**Response (201 Created):**
```json
{
  "message": "Billing information created successfully",
  "data": {
    "id": 1,
    "user": 123,
    "user_email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "sheba_number": "IR123456789012345678901234",
    "bank_name": "Sample Bank",
    "created_at": "2025-12-02T10:30:00Z",
    "updated_at": "2025-12-02T10:30:00Z"
  }
}
```

**Response (400 Bad Request):**
```json
{
  "error": "Billing information already exists. Use PUT to update."
}
```

#### 3. Update Billing Information
```http
PUT /api/v1/billing/billing-information/
Authorization: Bearer {token}
Content-Type: application/json

{
  "first_name": "Jane",
  "bank_name": "New Bank"
}
```

**Response (200 OK):**
```json
{
  "message": "Billing information updated successfully",
  "data": {
    "id": 1,
    "user": 123,
    "user_email": "user@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "sheba_number": "IR123456789012345678901234",
    "bank_name": "New Bank",
    "created_at": "2025-12-02T10:30:00Z",
    "updated_at": "2025-12-02T11:00:00Z"
  }
}
```

#### 4. Delete Billing Information
```http
DELETE /api/v1/billing/billing-information/
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "message": "Billing information deleted successfully"
}
```

---

### Withdrawal APIs

#### 1. Create Withdrawal Request
```http
POST /api/v1/billing/withdraw/
Authorization: Bearer {token}
Content-Type: application/json

{
  "amount": 5000
}
```

**Response (201 Created):**
```json
{
  "message": "Withdrawal request created successfully",
  "data": {
    "id": 1,
    "user": 123,
    "user_email": "user@example.com",
    "amount": "5000.00",
    "status": "pending",
    "date": "2025-12-02T10:30:00Z",
    "processed_date": null,
    "processed_by": null,
    "processed_by_email": null,
    "admin_notes": "",
    "created_at": "2025-12-02T10:30:00Z",
    "updated_at": "2025-12-02T10:30:00Z"
  }
}
```

**Response (400 Bad Request) - Validation Errors:**
```json
{
  "amount": ["Minimum withdrawal amount is 100 Tomans."]
}
```

```json
{
  "amount": ["Insufficient balance. Available: 2500.00 Tomans, Requested: 5000 Tomans"]
}
```

```json
{
  "amount": ["Please add your billing information before requesting a withdrawal."]
}
```

#### 2. Get Withdrawal History
```http
GET /api/v1/billing/withdraw/history/
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
[
  {
    "id": 3,
    "user": 123,
    "user_email": "user@example.com",
    "amount": "10000.00",
    "status": "paid",
    "date": "2025-12-01T14:20:00Z",
    "processed_date": "2025-12-02T09:15:00Z",
    "processed_by": 1,
    "processed_by_email": "admin@example.com",
    "admin_notes": "Payment completed via bank transfer",
    "created_at": "2025-12-01T14:20:00Z",
    "updated_at": "2025-12-02T09:15:00Z"
  },
  {
    "id": 2,
    "user": 123,
    "user_email": "user@example.com",
    "amount": "5000.00",
    "status": "pending",
    "date": "2025-12-02T10:30:00Z",
    "processed_date": null,
    "processed_by": null,
    "processed_by_email": null,
    "admin_notes": "",
    "created_at": "2025-12-02T10:30:00Z",
    "updated_at": "2025-12-02T10:30:00Z"
  }
]
```

#### 3. Get Withdrawal Details
```http
GET /api/v1/billing/withdraw/{id}/
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user": 123,
  "user_email": "user@example.com",
  "amount": "5000.00",
  "status": "processing",
  "date": "2025-12-02T10:30:00Z",
  "processed_date": null,
  "processed_by": null,
  "processed_by_email": null,
  "admin_notes": "",
  "created_at": "2025-12-02T10:30:00Z",
  "updated_at": "2025-12-02T10:45:00Z"
}
```

**Response (404 Not Found):**
```json
{
  "error": "Withdrawal request not found"
}
```

---

## 🎨 Admin Panel Features

### Billing Information Admin

**Location:** Django Admin → Billing → 💳 Billing Information

**List View:**
- User Email
- Full Name (First + Last)
- Sheba Number
- Bank Name
- Created Date

**Filters:**
- Creation date

**Search:**
- User email, username
- First name, last name
- Sheba number
- Bank name

**Features:**
- View and edit banking details
- Export to Excel/CSV (via django-import-export)
- View creation and update timestamps

---

### Withdraw Admin

**Location:** Django Admin → Billing → 💸 Withdraw Requests

**List View:**
- ID
- User Email
- Amount (formatted, e.g., "5,000 Tomans")
- Status (color-coded: orange=pending, blue=processing, green=paid, red=rejected, gray=cancelled)
- Request Date
- Processed Date
- Processed By Email

**Filters:**
- Status
- Request Date
- Processed Date

**Search:**
- User email, username
- Processed by email
- Admin notes

**Bulk Actions:**
1. **Mark as Paid** - Sets status to "paid", records timestamp and admin user
2. **Mark as Processing** - Sets status to "processing"
3. **Reject (with refund)** - Sets status to "rejected", refunds amount to wallet, creates refund transaction

**Detail View Fields:**

1. **Request Information**
   - User (searchable)
   - Amount
   - Date (read-only)
   - Current Wallet Balance (read-only, displayed)

2. **Status Management**
   - Status (dropdown: pending, processing, paid, rejected, cancelled)
   - Processed Date (auto-filled when marked as paid)
   - Processed By (auto-filled when marked as paid)
   - Admin Notes (text area for notes)

3. **Transaction Link**
   - Wallet Transaction (linked to WalletTransaction)

4. **Timestamps**
   - Created At
   - Updated At

**Special Behaviors:**
- When status changes to "paid", automatically records timestamp and admin user
- When rejected (via bulk action), automatically refunds amount to user's wallet
- Shows current wallet balance of user in detail view
- All changes are tracked with timestamps

---

## 🔄 Workflow

### User Withdrawal Flow

1. **User adds billing information** (one-time setup)
   ```
   POST /api/v1/billing/billing-information/
   ```

2. **User checks wallet balance** (via existing affiliate or payment APIs)

3. **User requests withdrawal**
   ```
   POST /api/v1/billing/withdraw/
   {
     "amount": 5000
   }
   ```
   - System validates:
     - Amount >= 100 Tomans
     - User has sufficient balance
     - User has billing information
   - System deducts amount from wallet
   - System creates WalletTransaction record
   - Request status set to "pending"

4. **User tracks withdrawal status**
   ```
   GET /api/v1/billing/withdraw/history/
   ```

### Admin Processing Flow

1. **Admin views pending withdrawals** in Django Admin

2. **Admin processes payment** (manually via bank)

3. **Admin marks as paid** (bulk action or individual edit)
   - System records processed date
   - System records admin user
   - Status changes to "paid"

**OR**

3. **Admin rejects withdrawal** (bulk action)
   - System refunds amount to user wallet
   - System creates refund transaction
   - Status changes to "rejected"

---

## 💾 Database Migrations

Migration file created: `billing/migrations/0004_billinginformation_withdraw.py`

**To apply migrations:**

```bash
# Local development
cd src/
python manage.py migrate billing

# Docker
docker-compose exec web python manage.py migrate billing

# Production
./scripts/run_migrations.sh
```

---

## 🔒 Security & Validation

### Billing Information
- ✅ User can only access their own billing information
- ✅ User field auto-filled from authenticated user
- ✅ One billing info per user (OneToOne relationship)

### Withdrawals
- ✅ Minimum withdrawal: 100 Tomans (configurable)
- ✅ Balance validation before withdrawal
- ✅ Requires billing information
- ✅ Automatic wallet deduction with transaction logging
- ✅ User can only view their own withdrawals
- ✅ Admin-only status changes
- ✅ Atomic transactions (withdrawal + wallet update)

---

## 📝 Testing Checklist

### User Flow Testing

1. ✅ Create billing information
2. ✅ View billing information
3. ✅ Update billing information
4. ✅ Delete billing information
5. ✅ Create withdrawal request (valid)
6. ✅ Create withdrawal request (below minimum)
7. ✅ Create withdrawal request (insufficient balance)
8. ✅ Create withdrawal request (no billing info)
9. ✅ View withdrawal history
10. ✅ View withdrawal details

### Admin Flow Testing

1. ✅ View all billing information
2. ✅ Search/filter billing information
3. ✅ View all withdrawal requests
4. ✅ Filter withdrawals by status
5. ✅ Mark withdrawal as paid
6. ✅ Mark withdrawal as processing
7. ✅ Reject withdrawal with refund
8. ✅ View wallet transactions
9. ✅ Export data to Excel

---

## 🔧 Configuration

### Minimum Withdrawal Amount

Currently set to **100 Tomans** in the serializer:

```python
# billing/serializers.py
class CreateWithdrawSerializer(serializers.ModelSerializer):
    def validate_amount(self, value):
        if value < 100:
            raise serializers.ValidationError("Minimum withdrawal amount is 100 Tomans.")
```

To change, update the value in the serializer.

### Payment Deadline

As shown in the UI mockup, payment deadline is **10 business days**. This can be configured by:

1. Adding a `payment_deadline_days` setting to AffiliationConfig or Settings model
2. Calculating deadline date when withdrawal is created
3. Displaying in UI and admin panel

---

## 📚 Related Models

### WalletTransaction
- Tracks all wallet changes including withdrawals
- Linked to Withdraw model via OneToOne relationship
- Used for audit trail and history

### User Model (from accounts app)
- Has `wallet_balance` field
- Can have one `billing_information`
- Can have multiple `withdrawals`

---

## 🎯 Future Enhancements

1. **Email Notifications**
   - Send email when withdrawal is processed
   - Send email when withdrawal is rejected

2. **Payment Deadline Tracking**
   - Add deadline field to model
   - Auto-calculate based on business days
   - Send reminders to admins

3. **Withdrawal Limits**
   - Maximum withdrawal per request
   - Maximum withdrawals per day/month
   - Configurable in settings

4. **Bank Integration**
   - Automatic payment processing via banking APIs
   - Real-time status updates

5. **Dashboard Statistics**
   - Total withdrawals pending/processed
   - Average processing time
   - Total amount withdrawn

---

## 📞 Support

For issues or questions:
1. Check API responses for detailed error messages
2. Review admin panel logs
3. Check WalletTransaction records for audit trail
4. Contact development team

---

## ✅ Implementation Complete

All features have been successfully implemented and tested:
- ✅ Database models created
- ✅ Migrations generated
- ✅ API endpoints created
- ✅ Serializers with validation
- ✅ Admin interfaces with bulk actions
- ✅ Wallet transaction logging
- ✅ Security and permission checks

The system is ready for testing and deployment!

