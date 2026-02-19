# Business Management System  
## User Guide  

## Table of Contents  

1. [Introduction](#introduction)  
2. [Getting Started](#getting-started)  
   - [Login](#login)  
   - [Dashboard Overview](#dashboard-overview)  
3. [Sales Management](#sales-management)  
   - [Recording a Sale](#recording-a-sale)  
   - [Viewing Sales History](#viewing-sales-history)  
   - [Printing an Invoice](#printing-an-invoice)  
   - [Processing Returns](#processing-returns)  
4. [Purchasing & Inventory](#purchasing--inventory)  
   - [Creating a Purchase Order](#creating-a-purchase-order)  
   - [Receiving Stock](#receiving-stock)  
   - [Managing Products](#managing-products)  
   - [Low Stock Alerts](#low-stock-alerts)  
5. [Customer Relationship Management (CRM)](#customer-relationship-management-crm)  
   - [Adding a Customer](#adding-a-customer)  
   - [Viewing Customer History](#viewing-customer-history)  
   - [Loyalty Points](#loyalty-points)  
6. [Expenses](#expenses)  
   - [Recording an Expense](#recording-an-expense)  
   - [Expense Categories](#expense-categories)  
7. [Payroll](#payroll)  
   - [Managing Employees](#managing-employees)  
   - [Processing Payroll](#processing-payroll)  
8. [Reports](#reports)  
   - [Sales Reports](#sales-reports)  
   - [Profit & Loss](#profit--loss)  
   - [Exporting Data](#exporting-data)  
9. [Admin Functions](#admin-functions)  
   - [User Management](#user-management)  
   - [Audit Logs](#audit-logs)  
10. [Tips and Best Practices](#tips-and-best-practices)  
11. [Troubleshooting](#troubleshooting)  
12. [Support](#support)  

---

## Introduction  

Welcome to the **Business Management System** – a comprehensive tool designed to streamline your daily operations, from sales and inventory to customer management and payroll. Whether you run a retail store, a small business, or a multi‑branch enterprise, this system provides an integrated platform to help you stay organized, make informed decisions, and grow your business.

**Key Features**  
- **Sales & Invoicing** – Record sales, generate invoices, and handle returns.  
- **Inventory Control** – Track stock levels, set reorder alerts, and manage batches.  
- **Customer Management** – Maintain customer profiles, view purchase history, and award loyalty points.  
- **Purchasing** – Create purchase orders and receive stock seamlessly.  
- **Expense Tracking** – Log expenses by category and monitor cash flow.  
- **Payroll** – Manage employee salaries and process payroll periods.  
- **Reports** – Gain insights with sales summaries, profit/loss, and exportable data.  
- **Multi‑Branch & User Roles** – Support for multiple locations with role‑based access (Admin, Manager, Staff).  

This guide will walk you through the main functions of the system, helping you get the most out of it.

---

## Getting Started  

### Login  

1. Open your web browser and navigate to your company’s Business Management System URL.  
2. You will see the **Login** page.  
3. Enter your **Username** and **Password** (provided by your administrator).  
4. Check **Remember Me** if you want to stay logged in on that device.  
5. Click **Login**.  

![Login Screen](images/login.png) *(Illustrative)*  

> **First‑time users:** Your administrator will provide you with credentials. After logging in, you can change your password via the profile settings (if available).

### Dashboard Overview  

After logging in, you are taken to the **Dashboard**. The dashboard gives you a snapshot of key metrics:  

- **Today’s Sales** – Total sales amount for the current day.  
- **Today’s Expenses** – Total expenses recorded today.  
- **Low Stock Items** – Number of products that have fallen below their reorder level.  
- **Total Customers** – Number of active customers in the system.  
- **Recent Sales** – A list of the latest sales with links to invoices.  
- **Sales Chart** – A graphical view of daily sales for the last 7 days.  
- **Payment Methods** – Breakdown of sales by payment method over the last 30 days.  

From the dashboard, you can quickly access any module using the navigation menu at the top.

---

## Sales Management  

### Recording a Sale  

1. From the top menu, click **Sales** > **New Sale**.  
2. Fill in the sale form:  
   - **Customer** – Select a customer from the dropdown, or leave as "Walk‑in" for guests.  
   - **Payment Method** – Choose Cash, Card, or Mobile Money.  
   - **Items** – In the **Items** text area, you must enter a JSON array of products. For example:  
     ```json
     [{"product_id": 1, "quantity": 2}, {"product_id": 3, "quantity": 1}]
     ```  
     *(Tip: If you have many items, you can use the product search to build this JSON automatically – see section 10.)*  
3. Click **Submit**.  
4. The system will validate stock availability and create the sale. On success, you are redirected to the invoice page.

### Viewing Sales History  

- Go to **Sales** > **All Sales**.  
- You will see a paginated list of sales, showing invoice number, date, customer, total amount, and payment method.  
- Click on any sale to view its details or print the invoice.

### Printing an Invoice  

- From the sales list, click the **Invoice** link next to a sale, or go to **Sales** > **Invoice** after creating a sale.  
- The invoice page displays all details in a printable format. Use your browser’s print function (Ctrl+P) to print or save as PDF.

### Processing Returns  

1. Navigate to **Returns** > **New Return** and enter the sale invoice number, or go to the sale detail page and click **Process Return**.  
2. You will see the list of items from that sale. For each item you want to return, enter the quantity.  
3. Choose whether to **restock** the item (add back to inventory) and select the condition.  
4. Select the **refund method** (cash, card, etc.).  
5. Click **Process Return**.  
6. The system will update stock (if restocked) and adjust the sale status accordingly (returned or partially returned).

---

## Purchasing & Inventory  

### Creating a Purchase Order  

1. From the menu, go to **Purchasing** > **Purchase Orders** > **New PO**.  
2. Fill in the form:  
   - **PO Number** – A unique identifier for the order.  
   - **Supplier** – Select from the list of suppliers.  
   - **Order Date** – Defaults to today.  
   - **Expected Date** – When you anticipate receiving the goods.  
   - **Notes** – Any additional information.  
3. In the **Items** section, add products by selecting them from the dropdown, entering quantity and unit price. You can add multiple rows.  
4. Click **Create Purchase Order**.  
5. The PO is saved with status **draft**. You can later mark it as ordered or received.

### Receiving Stock  

When the goods arrive:  

1. Go to **Purchasing** > **Purchase Orders**.  
2. Find the PO and click **Receive**.  
3. The system will increase stock quantities for each item and record a stock movement.  
4. If the product tracks batches, you may be prompted to enter batch numbers and expiry dates.  

### Managing Products  

- To view all products, go to **Inventory** > **Products**.  
- Use the search bar to find a product by name, SKU, or barcode.  
- Click **Edit** to update product details (price, reorder level, etc.).  
- To add a new product, click **New Product** and fill in:  
  - **Name**, **SKU** (unique), **Barcode** (optional)  
  - **Cost** and **Price**  
  - **Current Stock** (initial quantity)  
  - **Reorder Level** – The minimum stock before alert  
  - **Category**, **Brand**  
  - **Track Batches** – Check if you need batch/lot tracking (e.g., for perishables).  
  - **Branch** – If you have multiple branches, assign the product to the correct one.  

### Low Stock Alerts  

- The dashboard shows a count of low‑stock items.  
- Managers receive notifications (email) when stock falls below reorder level (if configured).  
- You can also run the **Low Stock Report** from the Reports section.

---

## Customer Relationship Management (CRM)  

### Adding a Customer  

1. Go to **CRM** > **Customers** > **New Customer**.  
2. Fill in the customer’s details:  
   - Name (required)  
   - Email, Phone, Address  
   - Segment (Regular, VIP, Inactive)  
   - Birth Date (optional)  
3. Click **Save**.  

### Viewing Customer History  

- From the customer list, click on a customer’s name.  
- You will see:  
  - **Sales History** – All purchases made by this customer.  
  - **Communications** – Log of emails, calls, or meetings (you can add new communications).  
  - **Loyalty Points** – Current points balance and transaction history.  
  - **Total Spent** – Lifetime purchase amount.  

### Loyalty Points  

- For every $10 spent, the customer earns 1 loyalty point (configurable).  
- Points are automatically added when a sale is completed.  
- Currently, points are for tracking only; future versions may include point redemption.

---

## Expenses  

### Recording an Expense  

1. Go to **Expenses** > **New Expense**.  
2. Fill in:  
   - **Description** – What the expense is for.  
   - **Amount** – The cost.  
   - **Category** – Select from predefined categories (Rent, Utilities, etc.).  
   - **Date** – Defaults to today.  
3. Click **Save**.  

### Expense Categories  

- Categories are managed by administrators. If you need a new category, contact your admin.

---

## Payroll  

*This module is accessible to users with Manager or Admin role.*

### Managing Employees  

- Employee records are stored in the **Users** table (see Admin Functions).  
- To set up an employee for payroll, ensure they have a **Salary** and **Pay Cycle** (monthly, biweekly, weekly) defined.

### Processing Payroll  

1. Go to **Payroll** > **Payroll Periods**.  
2. Click **Create New Period** (if not already created). Set a name, start date, and end date.  
3. Once the period ends, go to the period and click **Process Payroll**.  
4. The system generates pay slips for all active employees with a salary.  
5. Pay slips are saved with status **draft**. You can review and then mark as paid.

---

## Reports  

### Sales Reports  

1. Navigate to **Reports** > **Reports Dashboard**.  
2. Select a date range (default is current month).  
3. The report shows:  
   - Total sales, number of transactions  
   - Total expenses  
   - Net profit/loss  
   - Best‑selling products (top 10 by quantity)  
4. You can export the report as CSV by clicking **Export CSV** for the specific report type (Sales, Expenses, etc.).

### Profit & Loss  

- The profit calculation is automatically derived from sales minus expenses for the selected period.

### Exporting Data  

- From the reports page, click on **Export CSV** next to the report you want. A CSV file will be downloaded with the data.

---

## Admin Functions  

*These functions are available only to users with Admin role.*

### User Management  

1. Go to **Admin** > **Users**.  
2. Here you can view all users, add new users, or edit existing ones.  
3. When adding/editing a user, you can set:  
   - Username, Email, Password  
   - Role (Admin, Manager, Staff)  
   - Branch assignment  
   - Salary and pay cycle (for payroll)  
   - Permissions (fine‑grained access to modules)  
   - Active status (deactivate users who leave)  

### Audit Logs  

- **Admin** > **Audit Logs** shows a chronological record of all changes made to important data (users, products, sales, etc.).  
- Each entry shows which user made the change, when, and what was changed (old vs new values).  

### Activity Logs  

- **Admin** > **Activity Logs** tracks user actions like login, logout, and failed login attempts. Useful for security monitoring.

---

## Tips and Best Practices  

- **Use the search** – Most lists (customers, products, sales) have a search bar to quickly find records.  
- **Batch numbers** – If you deal with expiry dates, enable batch tracking for relevant products. Always record batch numbers when receiving stock.  
- **Keyboard shortcuts** – After filling forms, you can often press **Ctrl+Enter** to submit (if supported by browser).  
- **Regular backups** – Your administrator should schedule regular database backups. The system includes a command‑line backup tool (`flask backup-db`).  
- **Review low stock daily** – Check the dashboard or run the low stock report to avoid running out of popular items.  
- **Customer communications** – Use the communication log in CRM to keep notes about interactions with customers – this helps build relationships.  
- **Permissions** – Assign the minimum necessary permissions to users to maintain data security.

---

## Troubleshooting  

| Issue | Possible Solution |
|-------|-------------------|
| **Cannot log in** | Verify username and password. If forgotten, contact your administrator to reset it. |
| **Sale won’t save – "Insufficient stock"** | Check the product’s current stock. You may need to receive a purchase order first or adjust stock manually. |
| **Low stock alert not received** | Ensure your email is configured in the system and that the notification settings are enabled (contact admin). |
| **Report shows incorrect data** | Verify the date range. If problem persists, check that all sales/expenses are correctly entered. |
| **Page not found (404)** | You may have followed an outdated link. Use the navigation menu instead. |
| **Internal server error (500)** | Something went wrong on the server. Try again later; if it persists, contact support. |

