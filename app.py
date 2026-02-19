import os
import logging
import json
import io
from datetime import datetime, date, timedelta
from functools import wraps
from decimal import Decimal, ROUND_HALF_UP

from flask import Flask, render_template, redirect, url_for, flash, request, abort, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, FloatField, IntegerField, DateField, SelectField, TextAreaField, BooleanField, SelectMultipleField
from wtforms.validators import DataRequired, Email, Length, ValidationError, NumberRange, Optional
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import event, Index, and_, or_, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import attributes, joinedload
from sqlalchemy.ext.declarative import declared_attr
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from flask_login import AnonymousUserMixin
from flask_caching import Cache
from flask_babel import Babel, gettext as _
import click
from redis import Redis
import rq
from rq import Queue
from rq.job import Job

# ------------------------------
# App Configuration
# ------------------------------
app = Flask(__name__)

# Define locale selector BEFORE initializing Babel
def get_locale():
    if current_user.is_authenticated and hasattr(current_user, 'locale'):
        return current_user.locale
    return request.accept_languages.best_match(['en', 'es', 'fr']) or 'en'

# Initialize Babel with locale_selector
babel = Babel(app, locale_selector=get_locale)

# Load config from environment
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise ValueError("SECRET_KEY must be set in environment")

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///business.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
    'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 3600)),
}

# Security
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=int(os.environ.get('REMEMBER_DAYS', 30)))
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Mail settings
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')

# Cache (Redis)
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_REDIS_URL'] = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
app.config['CACHE_DEFAULT_TIMEOUT'] = 300

# Babel i18n
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
csrf = CSRFProtect(app)
mail = Mail(app)
cache = Cache(app)

# Redis queue for background tasks (optional)
redis_conn = Redis.from_url(app.config['CACHE_REDIS_URL'])
task_queue = Queue('business-tasks', connection=redis_conn)

# ------------------------------
# Permission definitions
# ------------------------------
ALL_PERMISSIONS = [
    ('access_dashboard', 'Access Dashboard'),
    ('view_sales', 'View Sales'),
    ('create_sale', 'Create Sale'),
    ('edit_sale', 'Edit Sale'),
    ('delete_sale', 'Delete Sale'),
    ('view_inventory', 'View Inventory'),
    ('edit_inventory', 'Edit Inventory'),
    ('view_expenses', 'View Expenses'),
    ('create_expense', 'Create Expense'),
    ('edit_expense', 'Edit Expense'),
    ('view_reports', 'View Reports'),
    ('view_customers', 'View Customers'),
    ('edit_customers', 'Edit Customers'),
    ('view_purchases', 'View Purchases'),
    ('create_purchase', 'Create Purchase Order'),
    ('manage_team', 'Manage Team'),
    ('manage_users', 'Manage Users'),
]

# ------------------------------
# Mixins
# ------------------------------
class AnonymousUser(AnonymousUserMixin):
    """Anonymous user with default permissions."""
    def has_permission(self, perm):
        return False

    @property
    def is_admin(self):
        return False

    @property
    def is_manager(self):
        return False

login_manager.anonymous_user = AnonymousUser

class SoftDeleteMixin:
    @declared_attr
    def deleted_at(cls):
        return db.Column(db.DateTime, nullable=True)

    def soft_delete(self):
        self.deleted_at = datetime.utcnow()
        db.session.add(self)

    def restore(self):
        self.deleted_at = None
        db.session.add(self)

    @classmethod
    def query_active(cls):
        return cls.query.filter(cls.deleted_at.is_(None))

class AuditMixin:
    @declared_attr
    def created_at(cls):
        return db.Column(db.DateTime, default=datetime.utcnow)

    @declared_attr
    def updated_at(cls):
        return db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @declared_attr
    def created_by_id(cls):
        return db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    @declared_attr
    def updated_by_id(cls):
        return db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    @declared_attr
    def created_by(cls):
        return db.relationship('User', foreign_keys=[cls.created_by_id])

    @declared_attr
    def updated_by(cls):
        return db.relationship('User', foreign_keys=[cls.updated_by_id])

# ------------------------------
# Models
# ------------------------------
class Branch(db.Model):
    __tablename__ = 'branches'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    currency = db.Column(db.String(3), default='USD')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(UserMixin, db.Model, AuditMixin, SoftDeleteMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='Staff')
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    active = db.Column(db.Boolean, default=True)
    locale = db.Column(db.String(5), default='en')
    phone = db.Column(db.String(20))
    avatar = db.Column(db.String(200))
    last_login = db.Column(db.DateTime)
    branch = db.relationship('Branch', backref='users')
    permissions = db.Column(db.JSON, default=list)

    salary = db.Column(db.Float, nullable=True)
    pay_cycle = db.Column(db.String(20), default='monthly')
    bank_account = db.Column(db.String(50))
    tax_id = db.Column(db.String(50))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'Admin'

    @property
    def is_manager(self):
        return self.role in ['Admin', 'Manager']

    def has_permission(self, perm):
        if self.is_admin:
            return True
        return perm in (self.permissions or [])

    def __repr__(self):
        return f'<User {self.username}>'

class Customer(db.Model, AuditMixin, SoftDeleteMixin):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    loyalty_points = db.Column(db.Integer, default=0)
    segment = db.Column(db.String(50), default='Regular')
    birth_date = db.Column(db.Date)
    tax_id = db.Column(db.String(50))
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    branch = db.relationship('Branch')
    communications = db.relationship('CommunicationLog', backref='customer', lazy='dynamic')

class CommunicationLog(db.Model, AuditMixin):
    __tablename__ = 'communication_logs'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    type = db.Column(db.String(20))
    subject = db.Column(db.String(200))
    content = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', foreign_keys=[user_id])

class LoyaltyTransaction(db.Model):
    __tablename__ = 'loyalty_transactions'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(100))
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    customer = db.relationship('Customer', backref='loyalty_transactions')

class Product(db.Model, AuditMixin, SoftDeleteMixin):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    barcode = db.Column(db.String(50), unique=True, nullable=True)
    price = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float)
    current_stock = db.Column(db.Integer, default=0)
    reorder_level = db.Column(db.Integer, default=5)
    category = db.Column(db.String(50))
    brand = db.Column(db.String(50))
    weight = db.Column(db.Float)
    is_service = db.Column(db.Boolean, default=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    branch = db.relationship('Branch')
    track_batches = db.Column(db.Boolean, default=False)
    batches = db.relationship('StockBatch', backref='product', lazy='dynamic')

    __table_args__ = (
        Index('ix_product_sku', sku),
        Index('ix_product_barcode', barcode),
    )

class StockBatch(db.Model):
    __tablename__ = 'stock_batches'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    batch_no = db.Column(db.String(50), nullable=False)
    expiry_date = db.Column(db.Date, nullable=True)
    quantity = db.Column(db.Integer, default=0)
    purchase_price = db.Column(db.Float)
    received_date = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('product_id', 'batch_no', name='uq_product_batch'),
        Index('ix_batch_expiry', expiry_date),
    )

class Supplier(db.Model, AuditMixin, SoftDeleteMixin):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    tax_id = db.Column(db.String(50))
    payment_terms = db.Column(db.String(100))
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    branch = db.relationship('Branch')
    products = db.relationship('Product', secondary='supplier_products', backref='suppliers')

class SupplierProduct(db.Model):
    __tablename__ = 'supplier_products'
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), primary_key=True)

class PurchaseOrder(db.Model, AuditMixin):
    __tablename__ = 'purchase_orders'
    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(50), unique=True, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    order_date = db.Column(db.Date, default=date.today)
    expected_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='draft')
    subtotal = db.Column(db.Float, default=0)
    tax = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    supplier = db.relationship('Supplier')
    branch = db.relationship('Branch')
    items = db.relationship('PurchaseOrderItem', backref='po', cascade='all, delete-orphan')

    def calculate_totals(self):
        self.subtotal = sum(item.total for item in self.items)
        self.total = self.subtotal + self.tax

class PurchaseOrderItem(db.Model):
    __tablename__ = 'purchase_order_items'
    id = db.Column(db.Integer, primary_key=True)
    po_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity_ordered = db.Column(db.Integer, nullable=False)
    quantity_received = db.Column(db.Integer, default=0)
    unit_price = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float)
    batch_no = db.Column(db.String(50))
    expiry_date = db.Column(db.Date)
    product = db.relationship('Product')

    def calculate_total(self):
        self.total = self.quantity_ordered * self.unit_price

class StockMovement(db.Model):
    __tablename__ = 'stock_movements'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('stock_batches.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    movement_type = db.Column(db.String(20), nullable=False)
    reference = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Product', backref='movements')
    batch = db.relationship('StockBatch')

class Sale(db.Model, AuditMixin):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    invoice_no = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    total_amount = db.Column(db.Float, nullable=False)
    tax = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    payment_method = db.Column(db.String(50))
    status = db.Column(db.String(20), default='completed')
    notes = db.Column(db.Text)
    customer = db.relationship('Customer')
    user = db.relationship('User', foreign_keys=[user_id])
    branch = db.relationship('Branch')
    items = db.relationship('SaleItem', backref='sale', cascade='all, delete-orphan')
    returns = db.relationship('Return', backref='sale', lazy='dynamic')

class SaleItem(db.Model):
    __tablename__ = 'sale_items'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('stock_batches.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    product = db.relationship('Product')
    batch = db.relationship('StockBatch')
    returns = db.relationship('ReturnItem', backref='sale_item', lazy='dynamic')

class Return(db.Model, AuditMixin):
    __tablename__ = 'returns'
    id = db.Column(db.Integer, primary_key=True)
    return_no = db.Column(db.String(50), unique=True, nullable=False)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    return_date = db.Column(db.Date, default=date.today)
    reason = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')
    refund_amount = db.Column(db.Float, default=0)
    refund_method = db.Column(db.String(50))
    notes = db.Column(db.Text)
    user = db.relationship('User', foreign_keys=[user_id])
    branch = db.relationship('Branch')
    items = db.relationship('ReturnItem', backref='return_', cascade='all, delete-orphan')

class ReturnItem(db.Model):
    __tablename__ = 'return_items'
    id = db.Column(db.Integer, primary_key=True)
    return_id = db.Column(db.Integer, db.ForeignKey('returns.id'), nullable=False)
    sale_item_id = db.Column(db.Integer, db.ForeignKey('sale_items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_refund = db.Column(db.Float, nullable=False)
    total_refund = db.Column(db.Float, nullable=False)
    condition = db.Column(db.String(50))
    restocked = db.Column(db.Boolean, default=True)

class ExpenseCategory(db.Model):
    __tablename__ = 'expense_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)

class Expense(db.Model, AuditMixin):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_categories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    date = db.Column(db.Date, default=date.today)
    receipt = db.Column(db.String(200))
    category = db.relationship('ExpenseCategory')
    user = db.relationship('User', foreign_keys=[user_id])
    branch = db.relationship('Branch')

class Attendance(db.Model):
    __tablename__ = 'attendances'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='attendances')

class Task(db.Model, AuditMixin):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='pending')
    assignee = db.relationship('User', foreign_keys=[assigned_to])
    assigner = db.relationship('User', foreign_keys=[assigned_by])

class PayrollPeriod(db.Model):
    __tablename__ = 'payroll_periods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    processed = db.Column(db.Boolean, default=False)
    processed_date = db.Column(db.Date)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'))
    branch = db.relationship('Branch')

class PaySlip(db.Model, AuditMixin):
    __tablename__ = 'pay_slips'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    period_id = db.Column(db.Integer, db.ForeignKey('payroll_periods.id'), nullable=False)
    basic_pay = db.Column(db.Float, nullable=False)
    allowances = db.Column(db.Float, default=0)
    deductions = db.Column(db.Float, default=0)
    net_pay = db.Column(db.Float, nullable=False)
    tax = db.Column(db.Float, default=0)
    payment_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='draft')
    notes = db.Column(db.Text)
    user = db.relationship('User', foreign_keys=[user_id])
    period = db.relationship('PayrollPeriod')

class Budget(db.Model, AuditMixin):
    __tablename__ = 'budgets'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    category = db.Column(db.String(50))
    amount = db.Column(db.Float, nullable=False)
    actual = db.Column(db.Float, default=0)
    branch = db.relationship('Branch')

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(10), nullable=False)
    old_values = db.Column(db.Text, nullable=True)
    new_values = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', foreign_keys=[user_id]) 

    __table_args__ = (
        Index('ix_audit_table_record', table_name, record_id),
        Index('ix_audit_timestamp', timestamp.desc()),
    )

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)
    user = db.relationship('User', foreign_keys=[user_id]) 

# ------------------------------
# Audit Logging
# ------------------------------
def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def log_audit(mapper, connection, target, action):
    from flask import has_request_context, request
    if target.__class__.__name__ == 'AuditLog':
        return

    user_id = None
    if has_request_context() and hasattr(request, 'user') and request.user:
        user_id = request.user.id
    elif hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
        user_id = current_user.id

    sensitive_fields = {'password_hash', 'reset_token', 'verification_token'}

    table_name = target.__tablename__
    record_id = target.id
    old_values = None
    new_values = None

    if action == 'UPDATE':
        state = db.inspect(target)
        changes = {}
        for attr in state.attrs:
            if attr.key in sensitive_fields:
                continue
            hist = state.get_history(attr.key, True)
            if hist.has_changes():
                if hasattr(attr, 'is_relation') and attr.is_relation:
                    continue
                old_val = hist.deleted[0] if hist.deleted else None
                new_val = hist.added[0] if hist.added else None
                try:
                    old_val = json.dumps(old_val, default=json_serial)
                except:
                    old_val = str(old_val)
                try:
                    new_val = json.dumps(new_val, default=json_serial)
                except:
                    new_val = str(new_val)
                changes[attr.key] = {'old': old_val, 'new': new_val}
        if changes:
            old_values = json.dumps({k: v['old'] for k, v in changes.items()}, default=json_serial)
            new_values = json.dumps({k: v['new'] for k, v in changes.items()}, default=json_serial)
    elif action == 'INSERT':
        new_vals = {}
        for c in target.__table__.columns:
            if c.key in sensitive_fields:
                continue
            val = getattr(target, c.key)
            try:
                val = json.dumps(val, default=json_serial)
            except:
                val = str(val)
            new_vals[c.key] = val
        new_values = json.dumps(new_vals, default=json_serial)
    elif action == 'DELETE':
        old_vals = {}
        for c in target.__table__.columns:
            if c.key in sensitive_fields:
                continue
            val = getattr(target, c.key)
            try:
                val = json.dumps(val, default=json_serial)
            except:
                val = str(val)
            old_vals[c.key] = val
        old_values = json.dumps(old_vals, default=json_serial)

    if old_values is not None or new_values is not None:
        connection.execute(
            AuditLog.__table__.insert().values(
                table_name=table_name,
                record_id=record_id,
                action=action,
                old_values=old_values,
                new_values=new_values,
                user_id=user_id,
                timestamp=datetime.utcnow()
            )
        )

audit_models = [User, Customer, Product, Sale, Expense, PurchaseOrder, Return, Supplier, PaySlip, Budget, Task]
for model in audit_models:
    event.listen(model, 'after_insert', lambda m, c, t: log_audit(m, c, t, 'INSERT'))
    event.listen(model, 'after_update', lambda m, c, t: log_audit(m, c, t, 'UPDATE'))
    event.listen(model, 'after_delete', lambda m, c, t: log_audit(m, c, t, 'DELETE'))

# ------------------------------
# Authentication & Authorization Helpers
# ------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query_active().filter_by(id=int(user_id)).first()

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated

def manager_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_manager:
            abort(403)
        return f(*args, **kwargs)
    return decorated

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if not current_user.has_permission(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def branch_filter(query, model):
    if current_user.is_admin:
        return query
    if current_user.branch_id:
        return query.filter(model.branch_id == current_user.branch_id)
    return query.filter(False)

# ------------------------------
# Forms
# ------------------------------
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Optional(), Length(min=6)])
    role = SelectField('Role', choices=[('Admin', 'Admin'), ('Manager', 'Manager'), ('Staff', 'Staff')])
    branch_id = SelectField('Branch', coerce=int, validators=[Optional()])
    salary = FloatField('Salary', validators=[Optional()])
    active = BooleanField('Active', default=True)
    pay_cycle = SelectField('Pay Cycle', choices=[('monthly', 'Monthly'), ('biweekly', 'Bi-Weekly'), ('weekly', 'Weekly')])
    permissions = SelectMultipleField('Permissions', choices=ALL_PERMISSIONS, coerce=str)

class CustomerForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone')
    address = TextAreaField('Address')
    segment = SelectField('Segment', choices=[('Regular', 'Regular'), ('VIP', 'VIP'), ('Inactive', 'Inactive')])
    birth_date = DateField('Birth Date', validators=[Optional()])

class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    sku = StringField('SKU', validators=[DataRequired()])
    barcode = StringField('Barcode', validators=[Optional()])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    cost = FloatField('Cost', validators=[Optional(), NumberRange(min=0)])
    current_stock = IntegerField('Current Stock', validators=[Optional(), NumberRange(min=0)])
    reorder_level = IntegerField('Reorder Level', validators=[Optional(), NumberRange(min=0)])
    category = StringField('Category')
    track_batches = BooleanField('Track Batches')
    branch_id = SelectField('Branch', coerce=int, validators=[Optional()])

class SaleForm(FlaskForm):
    customer_id = SelectField('Customer', coerce=int, validators=[Optional()])
    payment_method = SelectField('Payment Method', choices=[('cash', 'Cash'), ('card', 'Card'), ('mobile', 'Mobile Money')])
    items = TextAreaField('Items (JSON)', validators=[DataRequired()])

class ExpenseForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[Optional()], default=date.today)


def log_activity(action, details=None):
    log = ActivityLog(
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string if request.user_agent else None,
        details=details
    )
    db.session.add(log)
    db.session.commit()

class UserAdminView(ModelView):
    form_columns = ['username', 'email', 'role', 'branch_id', 'active', 'salary', 'pay_cycle', 'permissions']
    form_overrides = {
        'permissions': SelectMultipleField
    }
    form_args = {
        'permissions': {
            'choices': ALL_PERMISSIONS,
            'coerce': str
        }
    }
    column_list = ['username', 'email', 'role', 'branch', 'active', 'last_login', 'permissions']
    column_searchable_list = ['username', 'email']
    column_filters = ['role', 'active', 'branch']

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return abort(403)

class AdminModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    def inaccessible_callback(self, name, **kwargs):
        return abort(403)

# Initialize Flask-Admin (without template_mode for older versions)
admin = Admin(app, name='Business Control', endpoint='flask_admin')
admin.add_view(UserAdminView(User, db.session))
admin.add_view(AdminModelView(Customer, db.session))
admin.add_view(AdminModelView(Product, db.session))
admin.add_view(AdminModelView(StockMovement, db.session))
admin.add_view(AdminModelView(Sale, db.session))
admin.add_view(AdminModelView(Expense, db.session))
admin.add_view(AdminModelView(Attendance, db.session))
admin.add_view(AdminModelView(Task, db.session))
admin.add_view(AdminModelView(Branch, db.session))
admin.add_view(AdminModelView(AuditLog, db.session))
admin.add_view(AdminModelView(Supplier, db.session))
admin.add_view(AdminModelView(PurchaseOrder, db.session))
admin.add_view(AdminModelView(Return, db.session))
admin.add_view(AdminModelView(PaySlip, db.session))
admin.add_view(AdminModelView(Budget, db.session))

# ------------------------------
# Blueprints and Routes
# ------------------------------
from flask import Blueprint

# ----------------------------------------------------------------------
# Auth Blueprint
# ----------------------------------------------------------------------
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query_active().filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data) and user.active:
            login_user(user, remember=form.remember.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            log_activity('login', details=f"User {user.username} logged in")
            next_page = request.args.get('next')
            flash(_('Logged in successfully.'), 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
        flash(_('Invalid username or password.'), 'danger')
        log_activity('failed_login', details=f"Failed login for {form.username.data}")
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    log_activity('logout', details=f"User {current_user.username} logged out")
    logout_user()
    flash(_('You have been logged out.'), 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_request():
    # Placeholder for password reset
    pass

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    # Placeholder
    pass

# ----------------------------------------------------------------------
# Dashboard Blueprint
# ----------------------------------------------------------------------
dashboard_bp = Blueprint('dashboard', __name__)

def dashboard_cache_key():
    return f'dashboard_{current_user.id}'

@dashboard_bp.route('/')
@login_required
@cache.cached(timeout=60, key_prefix=dashboard_cache_key)
def index():
    today_date = date.today()
    sales_query = branch_filter(Sale.query, Sale)
    expenses_query = branch_filter(Expense.query, Expense)
    products_query = branch_filter(Product.query, Product)

    sales_today = sales_query.filter(func.date(Sale.created_at) == today_date).with_entities(func.sum(Sale.total_amount)).scalar() or 0
    expenses_today = expenses_query.filter(Expense.date == today_date).with_entities(func.sum(Expense.amount)).scalar() or 0
    low_stock = products_query.filter(Product.current_stock <= Product.reorder_level).count()
    total_customers = Customer.query_active().count()
    recent_sales = sales_query.order_by(Sale.created_at.desc()).limit(10).all()

    # For charts – compute real data
    last_7_days = [(today_date - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    daily_sales = []
    for day in last_7_days:
        total = sales_query.filter(func.date(Sale.created_at) == day).with_entities(func.sum(Sale.total_amount)).scalar() or 0
        daily_sales.append({'date': day, 'total': total})

    payment_methods = db.session.query(
        Sale.payment_method,
        func.count(Sale.id).label('count'),
        func.sum(Sale.total_amount).label('total')
    ).filter(
        Sale.branch_id == (current_user.branch_id if not current_user.is_admin else Sale.branch_id),
        func.date(Sale.created_at) >= (date.today() - timedelta(days=30))
    ).group_by(Sale.payment_method).all()

    context = {
        'sales_today': sales_today,
        'expenses_today': expenses_today,
        'low_stock': low_stock,
        'total_customers': total_customers,
        'recent_sales': recent_sales,
        'daily_sales': daily_sales,
        'payment_methods': payment_methods,
    }
    return render_template('dashboard/index.html', **context)

# ----------------------------------------------------------------------
# Sales Blueprint
# ----------------------------------------------------------------------
sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/')
@login_required
@permission_required('view_sales')
def list():
    page = request.args.get('page', 1, type=int)
    per_page = app.config.get('ITEMS_PER_PAGE', 20)
    query = branch_filter(Sale.query, Sale).options(joinedload(Sale.customer), joinedload(Sale.user))
    pagination = query.order_by(Sale.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('sales/list.html', pagination=pagination)

@sales_bp.route('/new', methods=['GET', 'POST'])
@login_required
@permission_required('create_sale')
def new():
    form = SaleForm()
    form.customer_id.choices = [(0, 'Walk-in')] + [(c.id, c.name) for c in Customer.query_active().all()]
    if form.validate_on_submit():
        try:
            items_data = json.loads(form.items.data)
            # Stock validation
            for item in items_data:
                product = Product.query.get(item['product_id'])
                if product and product.current_stock < item['quantity']:
                    flash(_('Insufficient stock for %(product)s', product=product.name), 'danger')
                    return render_template('sales/new.html', form=form)

            invoice = f"INV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            sale = Sale(
                invoice_no=invoice,
                customer_id=form.customer_id.data if form.customer_id.data != 0 else None,
                user_id=current_user.id,
                branch_id=current_user.branch_id,
                total_amount=0,
                payment_method=form.payment_method.data,
                status='completed'
            )
            db.session.add(sale)
            db.session.flush()

            total = 0
            for item in items_data:
                product = Product.query.get(item['product_id'])
                unit_price = product.price
                item_total = unit_price * item['quantity']
                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=product.id,
                    quantity=item['quantity'],
                    unit_price=unit_price,
                    total=item_total
                )
                db.session.add(sale_item)
                total += item_total

                product.current_stock -= item['quantity']
                movement = StockMovement(
                    product_id=product.id,
                    quantity=-item['quantity'],
                    movement_type='sale',
                    reference=sale.invoice_no
                )
                db.session.add(movement)

                if product.track_batches and 'batch_id' in item:
                    batch = StockBatch.query.get(item['batch_id'])
                    if batch:
                        batch.quantity -= item['quantity']
                        movement.batch_id = batch.id

            sale.total_amount = total
            db.session.commit()

            # Loyalty points
            if sale.customer_id:
                points = int(total / 10)
                if points > 0:
                    lt = LoyaltyTransaction(
                        customer_id=sale.customer_id,
                        points=points,
                        reason='purchase',
                        sale_id=sale.id
                    )
                    db.session.add(lt)
                    customer = Customer.query.get(sale.customer_id)
                    customer.loyalty_points += points
                    db.session.commit()

            flash(_('Sale recorded successfully.'), 'success')
            return redirect(url_for('sales.invoice', sale_id=sale.id))
        except Exception as e:
            db.session.rollback()
            logger.exception("Error creating sale")
            flash(_('Error creating sale: %(error)s', error=str(e)), 'danger')
    return render_template('sales/new.html', form=form, customers=Customer.query_active().all(), products=Product.query_active().all())

@sales_bp.route('/<int:sale_id>/invoice')
@login_required
@permission_required('view_sales')
def invoice(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template('sales/invoice.html', sale=sale)

# ----------------------------------------------------------------------
# Returns Blueprint
# ----------------------------------------------------------------------
returns_bp = Blueprint('returns', __name__)

@returns_bp.route('/')
@login_required
@permission_required('view_sales')  # same as sales for now
def list():
    page = request.args.get('page', 1, type=int)
    per_page = app.config.get('ITEMS_PER_PAGE', 20)
    query = branch_filter(Return.query, Return).options(joinedload(Return.sale), joinedload(Return.user))
    pagination = query.order_by(Return.return_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('returns/list.html', pagination=pagination)

@returns_bp.route('/new/<int:sale_id>', methods=['GET', 'POST'])
@login_required
@permission_required('view_sales')
def new_for_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    if sale.status in ['returned', 'partially_returned']:
        flash(_('This sale has already been processed for return.'), 'info')
        return redirect(url_for('sales.list'))
    if request.method == 'POST':
        try:
            return_no = f"RET-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            ret = Return(
                return_no=return_no,
                sale_id=sale.id,
                user_id=current_user.id,
                branch_id=current_user.branch_id or sale.branch_id,
                reason=request.form['reason'],
                status='approved'
            )
            db.session.add(ret)
            db.session.flush()

            total_refund = 0
            items = request.form.getlist('item_id')
            quantities = request.form.getlist('return_qty')
            for i, item_id in enumerate(items):
                qty = int(quantities[i])
                if qty <= 0:
                    continue
                sale_item = SaleItem.query.get(item_id)
                if not sale_item or sale_item.sale_id != sale.id:
                    continue
                unit_refund = sale_item.unit_price
                item_refund = unit_refund * qty
                return_item = ReturnItem(
                    return_id=ret.id,
                    sale_item_id=sale_item.id,
                    quantity=qty,
                    unit_refund=unit_refund,
                    total_refund=item_refund,
                    condition=request.form.get('condition', 'resellable'),
                    restocked=request.form.get('restock', 'true') == 'true'
                )
                db.session.add(return_item)
                total_refund += item_refund

                if return_item.restocked:
                    product = sale_item.product
                    product.current_stock += qty
                    movement = StockMovement(
                        product_id=product.id,
                        quantity=qty,
                        movement_type='return',
                        reference=ret.return_no,
                        notes=f"Return from sale {sale.invoice_no}"
                    )
                    db.session.add(movement)
                    if product.track_batches and sale_item.batch_id:
                        batch = StockBatch.query.get(sale_item.batch_id)
                        batch.quantity += qty
                        movement.batch_id = batch.id

            ret.refund_amount = total_refund
            ret.refund_method = request.form['refund_method']

            total_returned_qty = db.session.query(func.sum(ReturnItem.quantity)).join(Return).filter(Return.sale_id == sale.id).scalar() or 0
            total_sold_qty = db.session.query(func.sum(SaleItem.quantity)).filter(SaleItem.sale_id == sale.id).scalar() or 0
            if total_returned_qty >= total_sold_qty:
                sale.status = 'returned'
            else:
                sale.status = 'partially_returned'

            db.session.commit()
            flash(_('Return processed successfully.'), 'success')
            return redirect(url_for('returns.list'))
        except Exception as e:
            db.session.rollback()
            logger.exception("Error processing return")
            flash(_('Error processing return: %(error)s', error=str(e)), 'danger')
    return render_template('returns/new.html', sale=sale)

# ----------------------------------------------------------------------
# Purchasing Blueprint
# ----------------------------------------------------------------------
purchasing_bp = Blueprint('purchasing', __name__)

@purchasing_bp.route('/purchase-orders')
@login_required
@manager_required
def purchase_order_list():
    page = request.args.get('page', 1, type=int)
    per_page = app.config.get('ITEMS_PER_PAGE', 20)
    query = branch_filter(PurchaseOrder.query, PurchaseOrder).options(joinedload(PurchaseOrder.supplier))
    pagination = query.order_by(PurchaseOrder.order_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('purchasing/list.html', pagination=pagination)

@purchasing_bp.route('/purchase-orders/new', methods=['GET', 'POST'])
@login_required
@manager_required
def purchase_order_new():
    if request.method == 'POST':
        po = PurchaseOrder(
            po_number=request.form['po_number'],
            supplier_id=request.form['supplier_id'],
            order_date=datetime.strptime(request.form['order_date'], '%Y-%m-%d').date() if request.form.get('order_date') else date.today(),
            expected_date=datetime.strptime(request.form['expected_date'], '%Y-%m-%d').date() if request.form.get('expected_date') else None,
            status='draft',
            branch_id=current_user.branch_id,
            notes=request.form.get('notes')
        )
        db.session.add(po)
        db.session.flush()
        products = request.form.getlist('product_id')
        quantities = request.form.getlist('quantity')
        prices = request.form.getlist('price')
        for i in range(len(products)):
            if not products[i] or not quantities[i]:
                continue
            item = PurchaseOrderItem(
                po_id=po.id,
                product_id=int(products[i]),
                quantity_ordered=int(quantities[i]),
                unit_price=float(prices[i]),
            )
            item.calculate_total()
            db.session.add(item)
        po.calculate_totals()
        db.session.commit()
        flash(_('Purchase order created.'), 'success')
        return redirect(url_for('purchasing.purchase_order_list'))
    suppliers = Supplier.query_active().all()
    products = Product.query_active().all()
    return render_template('purchasing/form.html', suppliers=suppliers, products=products)

@purchasing_bp.route('/purchase-orders/<int:po_id>/receive', methods=['POST'])
@login_required
@manager_required
def receive_po(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    if po.status != 'ordered':
        flash(_('PO must be in ordered status to receive.'), 'warning')
        return redirect(url_for('purchasing.purchase_order_list'))
    try:
        for item in po.items:
            to_receive = item.quantity_ordered - item.quantity_received
            if to_receive > 0:
                product = item.product
                product.current_stock += to_receive
                movement = StockMovement(
                    product_id=product.id,
                    quantity=to_receive,
                    movement_type='purchase',
                    reference=po.po_number,
                    notes=f"Received from PO {po.po_number}"
                )
                db.session.add(movement)
                if product.track_batches:
                    batch_no = item.batch_no or f"BATCH-{datetime.utcnow().strftime('%Y%m%d')}"
                    batch = StockBatch.query.filter_by(product_id=product.id, batch_no=batch_no).first()
                    if not batch:
                        batch = StockBatch(
                            product_id=product.id,
                            batch_no=batch_no,
                            expiry_date=item.expiry_date,
                            quantity=0,
                            purchase_price=item.unit_price,
                            received_date=date.today()
                        )
                        db.session.add(batch)
                        db.session.flush()
                    batch.quantity += to_receive
                    movement.batch_id = batch.id

                item.quantity_received += to_receive

        po.status = 'received'
        po.expected_date = date.today()
        db.session.commit()
        flash(_('PO received successfully.'), 'success')
    except Exception as e:
        db.session.rollback()
        logger.exception("Error receiving PO")
        flash(_('Error: %(error)s', error=str(e)), 'danger')
    return redirect(url_for('purchasing.purchase_order_list'))
# ----------------------------------------------------------------------
# CRM Blueprint
# ----------------------------------------------------------------------
crm_bp = Blueprint('crm', __name__)

@crm_bp.route('/customers')
@login_required
@permission_required('view_customers')
def customer_list():
    page = request.args.get('page', 1, type=int)
    per_page = app.config.get('ITEMS_PER_PAGE', 20)
    query = Customer.query_active()
    pagination = query.order_by(Customer.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('crm/list.html', pagination=pagination)

@crm_bp.route('/customers/new', methods=['GET', 'POST'])
@login_required
@permission_required('edit_customers')
def new_customer():
    form = CustomerForm()
    if form.validate_on_submit():
        customer = Customer(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            segment=form.segment.data,
            birth_date=form.birth_date.data,
            branch_id=current_user.branch_id
        )
        db.session.add(customer)
        db.session.commit()
        flash(_('Customer added successfully.'), 'success')
        return redirect(url_for('crm.customer_list'))
    return render_template('crm/form.html', form=form)

@crm_bp.route('/customers/<int:customer_id>')
@login_required
@permission_required('view_customers')
def customer_detail_view(customer_id):  # renamed to avoid conflict
    customer = Customer.query_active().filter_by(id=customer_id).first_or_404()
    sales = Sale.query.filter_by(customer_id=customer_id).order_by(Sale.created_at.desc()).all()
    communications = customer.communications.order_by(CommunicationLog.date.desc()).all()
    total_spent = db.session.query(func.sum(Sale.total_amount)).filter_by(customer_id=customer_id).scalar() or 0
    return render_template('crm/detail.html', customer=customer, sales=sales, comms=communications, total_spent=total_spent)

@crm_bp.route('/customers/<int:customer_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('edit_customers')
def edit_customer(customer_id):
    customer = Customer.query_active().filter_by(id=customer_id).first_or_404()
    form = CustomerForm(obj=customer)
    if form.validate_on_submit():
        customer.name = form.name.data
        customer.email = form.email.data
        customer.phone = form.phone.data
        customer.address = form.address.data
        customer.segment = form.segment.data
        customer.birth_date = form.birth_date.data
        db.session.commit()
        flash(_('Customer updated successfully.'), 'success')
        return redirect(url_for('crm.customer_list'))
    return render_template('crm/form.html', form=form, customer=customer)

@crm_bp.route('/customers/<int:customer_id>/communication', methods=['POST'])
@login_required
@permission_required('edit_customers')
def add_communication(customer_id):
    customer = Customer.query_active().filter_by(id=customer_id).first_or_404()
    comm = CommunicationLog(
        customer_id=customer.id,
        type=request.form['type'],
        subject=request.form['subject'],
        content=request.form['content'],
        user_id=current_user.id
    )
    db.session.add(comm)
    db.session.commit()
    flash(_('Communication logged.'), 'success')
    return redirect(url_for('crm.customer_detail_view', customer_id=customer.id)) 

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/products')
@login_required
@permission_required('view_inventory')
def product_list():
    page = request.args.get('page', 1, type=int)
    per_page = app.config.get('ITEMS_PER_PAGE', 20)
    query = branch_filter(Product.query_active(), Product)
    pagination = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('inventory/list.html', pagination=pagination)

@inventory_bp.route('/products/<int:product_id>/batches')
@login_required
@permission_required('view_inventory')
def product_batches(product_id):
    product = Product.query_active().get_or_404(product_id)
    batches = product.batches.order_by(StockBatch.expiry_date).all()
    return render_template('inventory/batches.html', product=product, batches=batches)

@inventory_bp.route('/products/new', methods=['GET', 'POST'])
@login_required
@permission_required('edit_inventory')
def new_product():
    form = ProductForm()
    # Populate branch choices for admin; non‑admin users are assigned to their branch
    if current_user.is_admin:
        form.branch_id.choices = [(b.id, b.name) for b in Branch.query.filter_by(is_active=True)]
    else:
        # Pre‑select the user's branch and hide the field in the template
        form.branch_id.choices = [(current_user.branch_id, current_user.branch.name)] if current_user.branch else []
        form.branch_id.data = current_user.branch_id

    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            sku=form.sku.data,
            barcode=form.barcode.data,
            price=form.price.data,
            cost=form.cost.data,
            current_stock=form.current_stock.data,
            reorder_level=form.reorder_level.data,
            category=form.category.data,
            track_batches=form.track_batches.data,
            branch_id=form.branch_id.data or current_user.branch_id
        )
        db.session.add(product)
        db.session.commit()
        flash(_('Product added successfully.'), 'success')
        return redirect(url_for('inventory.product_list'))
    return render_template('inventory/product_form.html', form=form)

# ----------------------------------------------------------------------
# Expenses Blueprint
# ----------------------------------------------------------------------
expense_bp = Blueprint('expenses', __name__)

@expense_bp.route('/')
@login_required
@permission_required('view_expenses')
def list():
    page = request.args.get('page', 1, type=int)
    per_page = app.config.get('ITEMS_PER_PAGE', 20)
    query = branch_filter(Expense.query, Expense).options(joinedload(Expense.category))
    pagination = query.order_by(Expense.date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('expenses/list.html', pagination=pagination)

@expense_bp.route('/new', methods=['GET', 'POST'])
@login_required
@permission_required('create_expense')
def new():
    form = ExpenseForm()
    # Populate category choices
    form.category_id.choices = [(c.id, c.name) for c in ExpenseCategory.query.all()]
    
    if form.validate_on_submit():
        expense = Expense(
            description=form.description.data,
            amount=form.amount.data,
            category_id=form.category_id.data,
            user_id=current_user.id,
            branch_id=current_user.branch_id,
            date=form.date.data or date.today()
        )
        db.session.add(expense)
        db.session.commit()
        flash(_('Expense added successfully.'), 'success')
        return redirect(url_for('expenses.list'))
    
    return render_template('expenses/new.html', form=form)

payroll_bp = Blueprint('payroll', __name__)

@payroll_bp.route('/')
@login_required
@manager_required
def index():
    periods = PayrollPeriod.query.order_by(PayrollPeriod.start_date.desc()).all()
    return render_template('payroll/index.html', periods=periods)

@payroll_bp.route('/period/<int:period_id>/payslips')
@login_required
@manager_required
def period_payslips(period_id):
    period = PayrollPeriod.query.get_or_404(period_id)
    payslips = PaySlip.query.filter_by(period_id=period_id).all()
    return render_template('payroll/payslips.html', period=period, payslips=payslips)

@payroll_bp.route('/process', methods=['POST'])
@login_required
@manager_required
def process_payroll():
    period_id = request.form['period_id']
    period = PayrollPeriod.query.get(period_id)
    if period.processed:
        flash(_('Period already processed.'), 'warning')
        return redirect(url_for('payroll.index'))
    employees = User.query_active().filter_by(branch_id=current_user.branch_id).filter(User.salary.isnot(None)).all()
    for emp in employees:
        slip = PaySlip(
            user_id=emp.id,
            period_id=period.id,
            basic_pay=emp.salary,
            net_pay=emp.salary
        )
        db.session.add(slip)
    period.processed = True
    period.processed_date = date.today()
    db.session.commit()
    flash(_('Payroll processed.'), 'success')
    return redirect(url_for('payroll.index'))

# ----------------------------------------------------------------------
# Reports Blueprint
# ----------------------------------------------------------------------
reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
@manager_required
def index():
    start_date = request.args.get('start_date', (date.today().replace(day=1)).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()

    sales_query = branch_filter(Sale.query, Sale).filter(func.date(Sale.created_at).between(start, end))
    total_sales = sales_query.with_entities(func.sum(Sale.total_amount)).scalar() or 0
    sales_count = sales_query.count()

    expenses_query = branch_filter(Expense.query, Expense).filter(Expense.date.between(start, end))
    total_expenses = expenses_query.with_entities(func.sum(Expense.amount)).scalar() or 0

    profit = total_sales - total_expenses

    best_sellers = db.session.query(
        Product.name,
        func.sum(SaleItem.quantity).label('qty')
    ).join(SaleItem).join(Sale).filter(
        Sale.branch_id == (current_user.branch_id if not current_user.is_admin else Sale.branch_id),
        func.date(Sale.created_at).between(start, end)
    ).group_by(Product.id).order_by(func.sum(SaleItem.quantity).desc()).limit(10).all()

    return render_template('reports/index.html',
                           start=start, end=end,
                           total_sales=total_sales,
                           sales_count=sales_count,
                           total_expenses=total_expenses,
                           profit=profit,
                           best_sellers=best_sellers)

@reports_bp.route('/export/csv/<string:report_type>')
@login_required
@manager_required
def export_csv(report_type):
    import csv
    from io import StringIO
    si = StringIO()
    cw = csv.writer(si)
    if report_type == 'sales':
        sales = branch_filter(Sale.query, Sale).all()
        cw.writerow(['Invoice No', 'Date', 'Customer', 'Total', 'Payment Method'])
        for s in sales:
            cw.writerow([s.invoice_no, s.created_at.date(), s.customer.name if s.customer else '', s.total_amount, s.payment_method])
    output = si.getvalue()
    return send_file(
        io.BytesIO(output.encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{report_type}_{date.today()}.csv'
    )

# ----------------------------------------------------------------------
# API Blueprint
# ----------------------------------------------------------------------
api_bp = Blueprint('api', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        if token != 'Bearer secret':
            return jsonify({'message': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

@api_bp.route('/low-stock')
@token_required
def low_stock():
    query = branch_filter(Product.query_active(), Product).filter(Product.current_stock <= Product.reorder_level)
    products = query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'stock': p.current_stock,
        'reorder': p.reorder_level,
        'branch': p.branch.name if p.branch else None
    } for p in products])

@api_bp.route('/sales-today')
@token_required
def sales_today():
    today = date.today()
    query = branch_filter(Sale.query, Sale).filter(func.date(Sale.created_at) == today)
    total = query.with_entities(func.sum(Sale.total_amount)).scalar() or 0
    count = query.count()
    return jsonify({'total': total, 'count': count})

# ----------------------------------------------------------------------
# Admin Blueprint (custom user management)
# ----------------------------------------------------------------------
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    per_page = app.config.get('ITEMS_PER_PAGE', 20)
    pagination = User.query_active().order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin/users.html', pagination=pagination)

@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    form = UserForm()
    form.branch_id.choices = [(b.id, b.name) for b in Branch.query.filter_by(is_active=True)]

    if form.validate_on_submit():
        if not form.password.data:
            flash('Password is required for new users.', 'danger')
            return render_template('admin/user_form.html', form=form)

        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data,
            branch_id=form.branch_id.data if form.branch_id.data else None,
            active=form.active.data,
            salary=form.salary.data,
            pay_cycle=form.pay_cycle.data,
            permissions=form.permissions.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash('User created successfully.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/user_form.html', form=form)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    form.branch_id.choices = [(b.id, b.name) for b in Branch.query.filter_by(is_active=True)]

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.branch_id = form.branch_id.data or None
        user.active = form.active.data
        user.salary = form.salary.data
        user.pay_cycle = form.pay_cycle.data
        user.permissions = form.permissions.data

        if form.password.data:
            user.set_password(form.password.data)

        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/user_form.html', form=form, user=user)

@admin_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    page = request.args.get('page', 1, type=int)
    per_page = app.config.get('ITEMS_PER_PAGE', 20)
    pagination = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin/audit_logs.html', pagination=pagination)

@admin_bp.route('/activity-logs')
@login_required
@admin_required
def activity_logs():
    page = request.args.get('page', 1, type=int)
    per_page = app.config.get('ITEMS_PER_PAGE', 20)
    pagination = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin/activity_logs.html', pagination=pagination)
# ----------------------------------------------------------------------
# Register all blueprints
# ----------------------------------------------------------------------
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(sales_bp, url_prefix='/sales')
app.register_blueprint(returns_bp, url_prefix='/returns')
app.register_blueprint(purchasing_bp, url_prefix='/purchasing')
app.register_blueprint(crm_bp, url_prefix='/crm')
app.register_blueprint(inventory_bp, url_prefix='/inventory')
app.register_blueprint(expense_bp, url_prefix='/expenses')
app.register_blueprint(payroll_bp, url_prefix='/payroll')
app.register_blueprint(reports_bp, url_prefix='/reports')
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/admin')


def send_notification(user_id, message, method='email'):
    user = User.query.get(user_id)
    if user:
        logger.info(f"Sending {method} to {user.email}: {message}")

def check_low_stock_and_notify():
    with app.app_context():
        low_products = Product.query_active().filter(Product.current_stock <= Product.reorder_level).all()
        for prod in low_products:
            managers = User.query_active().filter_by(role='Manager', branch_id=prod.branch_id).all()
            for mgr in managers:
                send_notification(mgr.id, f"Low stock: {prod.name} ({prod.sku}) only {prod.current_stock} left.")


@app.cli.command("init-db")
def init_db():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@example.com', role='Admin')
        admin.set_password('admin')
        db.session.add(admin)
        if not Branch.query.first():
            branch = Branch(name='Head Office', location='Main')
            db.session.add(branch)
            db.session.flush()
            admin.branch_id = branch.id
        for cat in ['Rent', 'Utilities', 'Salaries', 'Transport', 'Marketing', 'Other']:
            if not ExpenseCategory.query.filter_by(name=cat).first():
                db.session.add(ExpenseCategory(name=cat))
        db.session.commit()
        print("Database initialized with admin user (admin/admin) and default data.")
    else:
        print("Database already exists.")

@app.cli.command("backup-db")
def backup_db():
    import json
    data = {}
    for table in db.metadata.sorted_tables:
        rows = db.session.execute(table.select()).fetchall()
        data[table.name] = [dict(row) for row in rows]
    filename = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, default=json_serial, indent=2)
    print(f"Backup saved to {filename}")

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    logger.exception("Internal server error")
    return render_template('errors/500.html'), 500


@app.context_processor
def inject_now():
    return {'now': datetime.utcnow(), 'current_year': datetime.utcnow().year}

@app.template_filter('currency')
def currency_format(value):
    if value is None:
        return "$0.00"
    return f"${value:,.2f}"


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@example.com', role='Admin')
            admin.set_password('admin')
            db.session.add(admin)
            if not Branch.query.first():
                branch = Branch(name='Head Office', location='Main')
                db.session.add(branch)
                db.session.flush()
                admin.branch_id = branch.id
            db.session.commit()
    app.run(debug=app.config.get('DEBUG', True), host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))