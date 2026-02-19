# ENVIRONMENTAL CLEANING AND WASTE MANAGEMENT SYSTEM  
## User Guide  

Version 1.0  
February 2026  

---

## Table of Contents  

1. [Introduction](#introduction)  
2. [Getting Started](#getting-started)  
   - [Login](#login)  
   - [Dashboard Overview](#dashboard-overview)  
3. **Service Orders (Job Management)**  
   - [Creating a Service Order](#creating-a-service-order)  
   - [Viewing Service History](#viewing-service-history)  
   - [Printing a Work Order / Invoice](#printing-a-work-order--invoice)  
   - [Processing Returns / Adjustments](#processing-returns--adjustments)  
4. **Procurement & Inventory (Supplies & Equipment)**  
   - [Creating a Purchase Order](#creating-a-purchase-order)  
   - [Receiving Stock (Supplies)](#receiving-stock-supplies)  
   - [Managing Equipment & Consumables](#managing-equipment--consumables)  
   - [Low Stock Alerts](#low-stock-alerts)  
5. **Client Relationship Management (CRM)**  
   - [Adding a Client](#adding-a-client)  
   - [Viewing Client History](#viewing-client-history)  
   - [Loyalty / Contract Points](#loyalty--contract-points)  
6. **Expenses**  
   - [Recording an Expense](#recording-an-expense)  
   - [Expense Categories](#expense-categories)  
7. **Payroll (Staff Management)**  
   - [Managing Employees](#managing-employees)  
   - [Processing Payroll](#processing-payroll)  
8. **Reports**  
   - [Service Reports](#service-reports)  
   - [Profit & Loss](#profit--loss)  
   - [Exporting Data](#exporting-data)  
9. **Admin Functions**  
   - [User Management](#user-management)  
   - [Audit Logs](#audit-logs)  
10. **Tips and Best Practices**  
11. **Troubleshooting**  
12. **Support**  

---

## Introduction  

Welcome to the **ENVIRONMENTAL CLEANING AND WASTE MANAGEMENT SYSTEM** – a comprehensive platform designed to streamline your daily operations in the environmental services industry. Whether you manage residential cleaning, industrial waste collection, recycling programs, or hazardous material handling, this system provides an integrated solution to help you stay organized, make informed decisions, and grow your business sustainably.

**Key Features**  
- **Service Orders & Job Management** – Record cleaning jobs, waste collection requests, generate work orders, and handle adjustments.  
- **Inventory Control** – Track supplies (cleaning agents, personal protective equipment), equipment, and consumables. Set reorder alerts and manage batches for chemicals.  
- **Client Management** – Maintain client profiles, view service history, and track contract details.  
- **Procurement** – Create purchase orders for supplies and receive stock seamlessly.  
- **Expense Tracking** – Log operational expenses by category (fuel, disposal fees, permits, etc.).  
- **Payroll** – Manage staff salaries, hours worked, and process payroll periods.  
- **Reports** – Gain insights with service summaries, profit/loss, and exportable data for compliance.  
- **Multi‑Branch & User Roles** – Support for multiple depots or service areas with role‑based access (Admin, Manager, Field Staff).  

This guide will walk you through the main functions of the system, helping you and your team maximize efficiency in environmental cleaning and waste management.

---

## Getting Started  

### Login  

1. Open your web browser and navigate to your company’s Environmental Cleaning System URL.  
2. You will see the **Login** page.  
3. Enter your **Username** and **Password** (provided by your administrator).  
4. Check **Remember Me** if you want to stay logged in on that device.  
5. Click **Login**.  

> **First‑time users:** Your administrator will provide credentials. After logging in, you can change your password via profile settings.

### Dashboard Overview  

After logging in, you are taken to the **Dashboard**, which provides a snapshot of key operational metrics:  

- **Today’s Service Revenue** – Total revenue from completed jobs for the current day.  
- **Today’s Expenses** – Total operational expenses recorded today (fuel, disposal fees, etc.).  
- **Low Stock Supplies** – Number of supply items (e.g., gloves, bags, chemicals) that have fallen below reorder level.  
- **Active Clients** – Number of clients with ongoing contracts or recent activity.  
- **Recent Service Orders** – A list of the latest jobs with links to details.  
- **Service Chart** – A graphical view of daily service revenue for the last 7 days.  
- **Payment Methods** – Breakdown of payments received by method (cash, card, invoice) over the last 30 days.  

From the dashboard, you can quickly access any module using the navigation menu at the top.

---

## Service Orders (Job Management)  

### Creating a Service Order  

1. From the top menu, click **Services** > **New Service Order**.  
2. Fill in the service order form:  
   - **Client** – Select a client from the dropdown, or leave as "One‑time" for new/unregistered clients.  
   - **Payment Method** – Choose Cash, Card, Invoice, etc.  
   - **Items / Services** – In the **Items** text area, you must enter a JSON array of services or supplies used. For example:  
     ```json
     [{"product_id": 1, "quantity": 2}, {"product_id": 3, "quantity": 1}]
     ```  
     *(Tip: Use the product search to build this JSON automatically – see section 10.)*  
3. Click **Submit**.  
4. The system will validate supply availability and create the service order. On success, you are redirected to the work order / invoice page.

### Viewing Service History  

- Go to **Services** > **All Service Orders**.  
- You will see a paginated list of jobs, showing order number, date, client, total amount, and payment method.  
- Click on any order to view its details or print the work order.

### Printing a Work Order / Invoice  

- From the service list, click the **Invoice** link next to an order, or go to **Services** > **Invoice** after creating a job.  
- The invoice page displays all details in a printable format. Use your browser’s print function (Ctrl+P) to print or save as PDF.

### Processing Returns / Adjustments  

If a client returns materials or a job needs adjustment (e.g., over‑charge correction):  

1. Navigate to **Services** > **Adjustments** and enter the original service order number, or go to the order detail page and click **Process Adjustment**.  
2. You will see the list of items from that order. For each item you want to adjust, enter the quantity to reverse.  
3. Choose whether to **restock** the items (return supplies to inventory).  
4. Select the **refund method** if a refund is due.  
5. Click **Process Adjustment**.  
6. The system will update stock (if restocked) and adjust the order status accordingly.

---

## Procurement & Inventory (Supplies & Equipment)  

### Creating a Purchase Order  

1. From the menu, go to **Procurement** > **Purchase Orders** > **New PO**.  
2. Fill in the form:  
   - **PO Number** – A unique identifier for the order.  
   - **Supplier** – Select from the list of approved vendors.  
   - **Order Date** – Defaults to today.  
   - **Expected Date** – When you anticipate receiving the supplies.  
   - **Notes** – Any additional information.  
3. In the **Items** section, add supplies by selecting them from the dropdown, entering quantity and unit price. You can add multiple rows.  
4. Click **Create Purchase Order**.  
5. The PO is saved with status **draft**. You can later mark it as ordered or received.

### Receiving Stock (Supplies)  

When the supplies arrive:  

1. Go to **Procurement** > **Purchase Orders**.  
2. Find the PO and click **Receive**.  
3. The system will increase stock quantities for each item and record a stock movement.  
4. If the supply item tracks batches (e.g., chemicals with expiry dates), you may be prompted to enter batch numbers and expiry dates.

### Managing Equipment & Consumables  

- To view all supply items, go to **Inventory** > **Supplies**.  
- Use the search bar to find an item by name, SKU, or barcode.  
- Click **Edit** to update details (price, reorder level, etc.).  
- To add a new supply item, click **New Supply** and fill in:  
  - **Name**, **SKU** (unique), **Barcode** (optional)  
  - **Cost** and **Selling Price** (if sold to clients)  
  - **Current Stock** (initial quantity)  
  - **Reorder Level** – The minimum stock before alert  
  - **Category** – e.g., PPE, Cleaning Agents, Bags, Fuel  
  - **Track Batches** – Check if you need batch/lot tracking (e.g., for chemicals with expiry).  
  - **Branch/Depot** – If you have multiple depots, assign the item to the correct one.  

### Low Stock Alerts  

- The dashboard shows a count of low‑stock items.  
- Managers receive notifications (email) when stock falls below reorder level (if configured).  
- You can also run the **Low Stock Report** from the Reports section.

---

## Client Relationship Management (CRM)  

### Adding a Client  

1. Go to **CRM** > **Clients** > **New Client**.  
2. Fill in the client’s details:  
   - Name (required)  
   - Email, Phone, Address  
   - Segment (Residential, Commercial, Industrial, Municipal)  
   - Contract Start/End (if applicable)  
3. Click **Save**.  

### Viewing Client History  

- From the client list, click on a client’s name.  
- You will see:  
  - **Service History** – All jobs performed for this client.  
  - **Communications** – Log of emails, calls, or site visits (you can add new communications).  
  - **Contract Details** – Active contracts, service level agreements.  
  - **Total Spent** – Lifetime revenue from this client.  

### Loyalty / Contract Points  

- For contract clients, you can track points or credits based on service volume.  
- Points are automatically added when a service is completed.  
- Future versions may include point redemption for discounts or additional services.

---

## Expenses  

### Recording an Expense  

1. Go to **Expenses** > **New Expense**.  
2. Fill in:  
   - **Description** – What the expense is for (e.g., fuel, landfill fees, equipment repair).  
   - **Amount** – The cost.  
   - **Category** – Select from predefined categories (Fuel, Disposal, Maintenance, Permits, etc.).  
   - **Date** – Defaults to today.  
3. Click **Save**.  

### Expense Categories  

- Categories are managed by administrators. If you need a new category, contact your admin.

---

## Payroll (Staff Management)  

*This module is accessible to users with Manager or Admin role.*

### Managing Employees  

- Employee records are stored in the **Users** table (see Admin Functions).  
- To set up an employee for payroll, ensure they have a **Salary** (or hourly rate) and **Pay Cycle** (monthly, biweekly, weekly) defined.  
- You can also track attendance and hours worked via the **Attendance** module (if enabled).

### Processing Payroll  

1. Go to **Payroll** > **Payroll Periods**.  
2. Click **Create New Period** (if not already created). Set a name, start date, and end date.  
3. Once the period ends, go to the period and click **Process Payroll**.  
4. The system generates pay slips for all active employees with a salary/hourly rate.  
5. Pay slips are saved with status **draft**. You can review and then mark as paid.

---

## Reports  

### Service Reports  

1. Navigate to **Reports** > **Reports Dashboard**.  
2. Select a date range (default is current month).  
3. The report shows:  
   - Total service revenue, number of jobs  
   - Total expenses  
   - Net profit/loss  
   - Most frequently used supplies / services  
4. You can export the report as CSV by clicking **Export CSV** for the specific report type (Services, Expenses, etc.).

### Profit & Loss  

- The profit calculation is automatically derived from service revenue minus expenses for the selected period.

### Exporting Data  

- From the reports page, click on **Export CSV** next to the report you want. A CSV file will be downloaded with the data for further analysis or compliance reporting.

---

## Admin Functions  

*These functions are available only to users with Admin role.*

### User Management  

1. Go to **Admin** > **Users**.  
2. Here you can view all users, add new users, or edit existing ones.  
3. When adding/editing a user, you can set:  
   - Username, Email, Password  
   - Role (Admin, Manager, Field Staff, Dispatcher)  
   - Branch/Depot assignment  
   - Salary / hourly rate and pay cycle (for payroll)  
   - Permissions (fine‑grained access to modules)  
   - Active status (deactivate users who leave)  

### Audit Logs  

- **Admin** > **Audit Logs** shows a chronological record of all changes made to important data (users, clients, service orders, supplies, etc.).  
- Each entry shows which user made the change, when, and what was changed (old vs new values).  

### Activity Logs  

- **Admin** > **Activity Logs** tracks user actions like login, logout, and failed login attempts. Useful for security monitoring and compliance.

---

## Tips and Best Practices  

- **Use the search** – Most lists (clients, supplies, service orders) have a search bar to quickly find records.  
- **Batch numbers for chemicals** – If you handle hazardous materials or chemicals with expiry dates, enable batch tracking. Always record batch numbers when receiving stock.  
- **Daily stock check** – Review low stock alerts daily to avoid running out of essential PPE or cleaning agents.  
- **Client communication log** – Use the CRM communication log to keep notes about site visits, special requests, or complaints – this helps maintain high service quality.  
- **Permissions** – Assign the minimum necessary permissions to field staff to maintain data security.  
- **Regular backups** – Your administrator should schedule regular database backups. The system includes a command‑line backup tool (`flask backup-db`).  
- **Compliance** – Use the audit logs to demonstrate compliance with environmental regulations and internal policies.

---

## Troubleshooting  

| Issue | Possible Solution |
|-------|-------------------|
| **Cannot log in** | Verify username and password. If forgotten, contact your administrator to reset it. |
| **Service order won’t save – "Insufficient stock"** | Check the current stock of the supply item. You may need to receive a purchase order first or adjust stock manually. |
| **Low stock alert not received** | Ensure your email is configured in the system and that the notification settings are enabled (contact admin). |
| **Report shows incorrect data** | Verify the date range. If problem persists, check that all service orders and expenses are correctly entered. |
| **Page not found (404)** | You may have followed an outdated link. Use the navigation menu instead. |
| **Internal server error (500)** | Something went wrong on the server. Try again later; if it persists, contact support. |

---

## Support  

If you encounter any issues not covered in this guide, or if you have suggestions for improvement, please contact:  

- **Email:** support@envclean.com  
- **Phone:** +1 (555) 987-6543  
- **Internal Help Desk:** Visit the IT department or submit a ticket through your company’s help portal.  

We are committed to helping you make the most of the **ENVIRONMENTAL CLEANING AND WASTE MANAGEMENT SYSTEM**.

---

*Thank you for using our system and for your commitment to a cleaner environment!*