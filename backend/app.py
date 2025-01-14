from flask import Flask, request, jsonify, send_from_directory, Response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Database configuration
db_path = os.environ.get('DATABASE_URL', 'sqlite:///coffee_shop.db')
if db_path.startswith('postgres://'):
    db_path = db_path.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Helper function for unit conversion
def convert_to_base_unit(value, from_unit):
    """Convert a value to its base unit (g or ml)"""
    if from_unit == 'kg':
        return value * 1000  # Convert to grams
    elif from_unit == 'l':
        return value * 1000  # Convert to milliliters
    return value

def convert_from_base_unit(value, to_unit):
    """Convert a value from its base unit (g or ml) to the target unit"""
    if to_unit == 'kg':
        return value / 1000  # Convert from grams
    elif to_unit == 'l':
        return value / 1000  # Convert from milliliters
    return value

def calculate_ingredient_cost(ingredient, quantity, unit):
    """Calculate the cost of an ingredient with proper unit conversion"""
    # Convert quantity to base unit (g or ml)
    base_quantity = convert_to_base_unit(quantity, unit)
    
    # Get the cost per base unit
    if ingredient.cost_unit in ['kg', 'l']:
        # If cost is per kg/l, convert to cost per g/ml
        base_cost = ingredient.cost_per_unit / 1000
    else:
        base_cost = ingredient.cost_per_unit
    
    return base_cost * base_quantity

# Models
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    selling_price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    ingredients = db.relationship('ProductIngredient', backref='product', lazy=True, cascade="all, delete-orphan")
    sales = db.relationship('Sale', backref='product_ref', lazy=True)

    def calculate_cost(self):
        total_cost = 0
        for ingredient in self.ingredients:
            ingredient_cost = calculate_ingredient_cost(
                ingredient.ingredient_ref,
                ingredient.quantity,
                ingredient.unit
            )
            total_cost += ingredient_cost
        return total_cost

    def calculate_profit(self):
        return self.selling_price - self.calculate_cost()

class IngredientCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    ingredients = db.relationship('Ingredient', backref='category_ref', lazy=True)

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('ingredient_category.id'), nullable=False)
    current_stock = db.Column(db.Float, nullable=False)
    stock_unit = db.Column(db.String(20), nullable=False)
    min_threshold = db.Column(db.Float, nullable=False)
    threshold_unit = db.Column(db.String(20), nullable=False)
    cost_per_unit = db.Column(db.Float, nullable=False)
    cost_unit = db.Column(db.String(20), nullable=False)
    products = db.relationship('ProductIngredient', backref='ingredient_ref', lazy=True)
    stock_updates = db.relationship('StockUpdate', backref='ingredient', lazy=True)

    def get_stock_in_base_unit(self):
        return convert_to_base_unit(self.current_stock, self.stock_unit)

    def get_threshold_in_base_unit(self):
        return convert_to_base_unit(self.min_threshold, self.threshold_unit)

class ProductIngredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)

class StockUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    cost_per_unit = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.String(200))

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def calculate_metrics(self):
        if not self.product_ref:
            return None
            
        cost = self.product_ref.calculate_cost() * self.quantity
        revenue = self.product_ref.selling_price * self.quantity
        profit = revenue - cost
        
        return {
            'cost': cost,
            'revenue': revenue,
            'profit': profit
        }

class FinanceOverview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    starting_balance = db.Column(db.Float, nullable=False)
    total_income = db.Column(db.Float, nullable=False)
    total_expenses = db.Column(db.Float, nullable=False)
    current_balance = db.Column(db.Float, nullable=False)

# Routes
@app.route('/api/ingredients', methods=['GET', 'POST'])
def handle_ingredients():
    if request.method == 'POST':
        try:
            data = request.json
            
            # Validate required fields
            required_fields = ['name', 'category_id', 'current_stock', 'stock_unit', 'min_threshold', 'threshold_unit', 'cost_per_unit']
            for field in required_fields:
                if field not in data:
                    return jsonify({'message': f'Missing required field: {field}'}), 400
                if data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
                    return jsonify({'message': f'Field cannot be empty: {field}'}), 400
            
            # Validate numeric fields
            numeric_fields = ['current_stock', 'min_threshold', 'cost_per_unit']
            for field in numeric_fields:
                try:
                    float(data[field])
                except (TypeError, ValueError):
                    return jsonify({'message': f'Invalid numeric value for {field}'}), 400
            
            # Validate category exists
            category = IngredientCategory.query.get(data['category_id'])
            if not category:
                return jsonify({'message': 'Invalid category ID'}), 400
            
            ingredient = Ingredient(
                name=data['name'],
                category_id=data['category_id'],
                current_stock=float(data['current_stock']),
                stock_unit=data['stock_unit'],
                min_threshold=float(data['min_threshold']),
                threshold_unit=data['threshold_unit'],
                cost_per_unit=float(data['cost_per_unit']),
                cost_unit=data['stock_unit']
            )
            
            db.session.add(ingredient)
            db.session.commit()
            
            return jsonify({
                'message': 'Ingredient added successfully',
                'ingredient': {
                    'id': ingredient.id,
                    'name': ingredient.name,
                    'category_id': ingredient.category_id,
                    'category_name': ingredient.category_ref.name,
                    'current_stock': ingredient.current_stock,
                    'stock_unit': ingredient.stock_unit,
                    'min_threshold': ingredient.min_threshold,
                    'threshold_unit': ingredient.threshold_unit,
                    'cost_per_unit': ingredient.cost_per_unit,
                    'cost_unit': ingredient.cost_unit,
                    'low_stock': ingredient.get_stock_in_base_unit() <= ingredient.get_threshold_in_base_unit()
                }
            }), 201
        except Exception as e:
            print('Error creating ingredient:', str(e))
            db.session.rollback()
            return jsonify({'message': f'Error creating ingredient: {str(e)}'}), 500
    
    # GET request - return ingredients with category information
    ingredients = Ingredient.query.join(IngredientCategory).order_by(IngredientCategory.name, Ingredient.name).all()
    return jsonify([{
        'id': i.id,
        'name': i.name,
        'category_id': i.category_id,
        'category_name': i.category_ref.name,
        'current_stock': i.current_stock,
        'stock_unit': i.stock_unit,
        'min_threshold': i.min_threshold,
        'threshold_unit': i.threshold_unit,
        'cost_per_unit': i.cost_per_unit,
        'cost_unit': i.cost_unit,
        'low_stock': i.get_stock_in_base_unit() <= i.get_threshold_in_base_unit()
    } for i in ingredients])

@app.route('/api/ingredients/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def handle_ingredient(id):
    ingredient = Ingredient.query.get_or_404(id)
    
    if request.method == 'PUT':
        try:
            data = request.json
            
            # Validate required fields
            required_fields = ['name', 'category_id', 'current_stock', 'stock_unit', 'min_threshold', 'threshold_unit', 'cost_per_unit']
            for field in required_fields:
                if field not in data:
                    return jsonify({'message': f'Missing required field: {field}'}), 400
                if data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
                    return jsonify({'message': f'Field cannot be empty: {field}'}), 400
            
            # Validate numeric fields
            numeric_fields = ['current_stock', 'min_threshold', 'cost_per_unit']
            for field in numeric_fields:
                try:
                    float(data[field])
                except (TypeError, ValueError):
                    return jsonify({'message': f'Invalid numeric value for {field}'}), 400
            
            # Validate category exists
            category = IngredientCategory.query.get(data['category_id'])
            if not category:
                return jsonify({'message': 'Invalid category ID'}), 400
            
            ingredient.name = data['name']
            ingredient.category_id = data['category_id']
            ingredient.current_stock = float(data['current_stock'])
            ingredient.stock_unit = data['stock_unit']
            ingredient.min_threshold = float(data['min_threshold'])
            ingredient.threshold_unit = data['threshold_unit']
            ingredient.cost_per_unit = float(data['cost_per_unit'])
            ingredient.cost_unit = data['stock_unit']
            
            db.session.commit()
            return jsonify({'message': 'Ingredient updated successfully'})
        except Exception as e:
            print('Error updating ingredient:', str(e))
            db.session.rollback()
            return jsonify({'message': f'Error updating ingredient: {str(e)}'}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(ingredient)
            db.session.commit()
            return jsonify({'message': 'Ingredient deleted successfully'})
        except Exception as e:
            print('Error deleting ingredient:', str(e))
            db.session.rollback()
            return jsonify({'message': f'Error deleting ingredient: {str(e)}'}), 500

@app.route('/api/ingredient-categories', methods=['GET', 'POST'])
def handle_ingredient_categories():
    if request.method == 'POST':
        try:
            data = request.json
            if not data.get('name'):
                return jsonify({'message': 'Category name is required'}), 400

            # Check if category already exists
            existing = IngredientCategory.query.filter_by(name=data['name']).first()
            if existing:
                return jsonify({'message': 'Category already exists'}), 400

            category = IngredientCategory(name=data['name'])
            db.session.add(category)
            db.session.commit()
            return jsonify({
                'message': 'Category added successfully',
                'category': {'id': category.id, 'name': category.name}
            }), 201
        except Exception as e:
            print('Error creating category:', str(e))
            db.session.rollback()
            return jsonify({'message': f'Error creating category: {str(e)}'}), 500

    # GET request
    categories = IngredientCategory.query.order_by(IngredientCategory.name).all()
    return jsonify([{'id': c.id, 'name': c.name} for c in categories])

@app.route('/api/ingredient-categories/<int:id>', methods=['PUT', 'DELETE'])
def handle_ingredient_category(id):
    category = IngredientCategory.query.get_or_404(id)
    
    if request.method == 'PUT':
        try:
            data = request.json
            if not data.get('name'):
                return jsonify({'message': 'Category name is required'}), 400

            # Check if new name already exists for another category
            existing = IngredientCategory.query.filter(
                IngredientCategory.name == data['name'],
                IngredientCategory.id != id
            ).first()
            if existing:
                return jsonify({'message': 'Category name already exists'}), 400

            category.name = data['name']
            db.session.commit()
            return jsonify({'message': 'Category updated successfully'})
        except Exception as e:
            print('Error updating category:', str(e))
            db.session.rollback()
            return jsonify({'message': f'Error updating category: {str(e)}'}), 500

    elif request.method == 'DELETE':
        try:
            # Check if category has ingredients
            if category.ingredients:
                return jsonify({'message': 'Cannot delete category that has ingredients'}), 400
                
            db.session.delete(category)
            db.session.commit()
            return jsonify({'message': 'Category deleted successfully'})
        except Exception as e:
            print('Error deleting category:', str(e))
            db.session.rollback()
            return jsonify({'message': f'Error deleting category: {str(e)}'}), 500

@app.route('/api/products', methods=['GET', 'POST'])
def handle_products():
    if request.method == 'POST':
        try:
            data = request.json
            
            # Validate required fields
            required_fields = ['name', 'selling_price', 'category', 'ingredients']
            for field in required_fields:
                if field not in data:
                    return jsonify({'message': f'Missing required field: {field}'}), 400
            
            # Validate ingredients
            if not isinstance(data['ingredients'], list) or len(data['ingredients']) == 0:
                return jsonify({'message': 'Invalid ingredients'}), 400
            
            product = Product(
                name=data['name'],
                description=data.get('description', ''),
                selling_price=data['selling_price'],
                category=data['category'],
                is_active=data.get('is_active', True)
            )
            
            # Add ingredients with unit conversion
            for ingredient_data in data['ingredients']:
                ingredient = Ingredient.query.get(ingredient_data['ingredient_id'])
                if not ingredient:
                    return jsonify({'message': f'Ingredient not found: {ingredient_data["ingredient_id"]}'}), 404
                
                # Convert quantity to base unit if needed
                quantity = convert_to_base_unit(
                    float(ingredient_data['quantity']), 
                    ingredient_data['unit']
                )
                
                product_ingredient = ProductIngredient(
                    ingredient_id=ingredient_data['ingredient_id'],
                    quantity=quantity,
                    unit=ingredient_data['unit']
                )
                product.ingredients.append(product_ingredient)
            
            db.session.add(product)
            db.session.commit()
            return jsonify({'message': 'Product created successfully', 'id': product.id}), 201
        except Exception as e:
            print('Error creating product:', str(e))
            db.session.rollback()
            return jsonify({'message': f'Error creating product: {str(e)}'}), 500
    
    # Get all products
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'selling_price': p.selling_price,
        'category': p.category,
        'is_active': p.is_active,
        'ingredients': [{
            'id': pi.id,
            'ingredient_id': pi.ingredient_id,
            'ingredient_name': pi.ingredient_ref.name,
            'quantity': pi.quantity,
            'unit': pi.unit,
            'cost': calculate_ingredient_cost(
                ingredient=pi.ingredient_ref,
                quantity=pi.quantity,
                unit=pi.unit
            )
        } for pi in p.ingredients],
        'total_cost': p.calculate_cost(),
        'profit': {
            'amount': p.selling_price - p.calculate_cost(),
            'percentage': ((p.selling_price - p.calculate_cost()) / p.calculate_cost() * 100) if p.calculate_cost() > 0 else 0
        }
    } for p in products])

@app.route('/api/products/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def handle_product(id):
    product = Product.query.get_or_404(id)
    
    if request.method == 'GET':
        cost = product.calculate_cost()
        return jsonify({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'selling_price': product.selling_price,
            'category': product.category,
            'is_active': product.is_active,
            'ingredients': [{
                'id': pi.id,
                'ingredient_id': pi.ingredient_id,
                'ingredient_name': pi.ingredient_ref.name,
                'quantity': pi.quantity,
                'unit': pi.unit,
                'cost': calculate_ingredient_cost(
                    ingredient=pi.ingredient_ref,
                    quantity=pi.quantity,
                    unit=pi.unit
                )
            } for pi in product.ingredients],
            'total_cost': cost,
            'profit': {
                'amount': product.selling_price - cost,
                'percentage': ((product.selling_price - cost) / cost * 100) if cost > 0 else 0
            }
        })
    
    elif request.method == 'PUT':
        try:
            data = request.json
            
            # Validate required fields
            required_fields = ['name', 'selling_price', 'category', 'ingredients']
            for field in required_fields:
                if field not in data:
                    return jsonify({'message': f'Missing required field: {field}'}), 400
            
            # Validate ingredients
            if not isinstance(data['ingredients'], list) or len(data['ingredients']) == 0:
                return jsonify({'message': 'Invalid ingredients'}), 400
            
            # Update basic product info
            product.name = data['name']
            product.description = data.get('description', '')
            product.selling_price = data['selling_price']
            product.category = data['category']
            product.is_active = data.get('is_active', True)
            
            # Remove all existing ingredients
            for pi in product.ingredients:
                db.session.delete(pi)
            
            # Add new ingredients
            for ingredient_data in data['ingredients']:
                ingredient = Ingredient.query.get(ingredient_data['ingredient_id'])
                if not ingredient:
                    return jsonify({'message': f'Ingredient not found: {ingredient_data["ingredient_id"]}'}), 404
                
                # Convert quantity to base unit if needed
                quantity = convert_to_base_unit(
                    float(ingredient_data['quantity']), 
                    ingredient_data['unit']
                )
                
                product_ingredient = ProductIngredient(
                    ingredient_id=ingredient_data['ingredient_id'],
                    quantity=quantity,
                    unit=ingredient_data['unit']
                )
                product.ingredients.append(product_ingredient)
            
            db.session.commit()
            return jsonify({'message': 'Product updated successfully'})
        except Exception as e:
            print('Error updating product:', str(e))
            db.session.rollback()
            return jsonify({'message': f'Error updating product: {str(e)}'}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(product)
            db.session.commit()
            return jsonify({'message': 'Product deleted successfully'})
        except Exception as e:
            print('Error deleting product:', str(e))
            db.session.rollback()
            return jsonify({'message': f'Error deleting product: {str(e)}'}), 500

@app.route('/api/product-categories', methods=['GET'])
def get_product_categories():
    categories = db.session.query(Product.category).distinct().all()
    return jsonify([category[0] for category in categories])

@app.route('/api/sales', methods=['GET', 'POST'])
def handle_sales():
    if request.method == 'POST':
        try:
            data = request.json
            sale = Sale(
                date=datetime.fromisoformat(data['date']),
                product_id=data['product_id'],
                quantity=data['quantity']
            )
            db.session.add(sale)
            db.session.commit()
            return jsonify({'message': 'Sale created successfully'}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': f'Error creating sale: {str(e)}'}), 500
    
    # GET method
    sales = Sale.query.order_by(Sale.date.desc()).all()
    return jsonify([{
        'id': sale.id,
        'date': sale.date.isoformat(),
        'product_id': sale.product_id,
        'product_name': sale.product_ref.name,
        'quantity': sale.quantity,
        **sale.calculate_metrics()
    } for sale in sales])

@app.route('/api/sales/<int:id>', methods=['GET', 'DELETE'])
def handle_sale(id):
    sale = Sale.query.get_or_404(id)
    
    if request.method == 'GET':
        return jsonify({
            'id': sale.id,
            'date': sale.date.isoformat(),
            'product_id': sale.product_id,
            'product_name': sale.product_ref.name,
            'quantity': sale.quantity,
            **sale.calculate_metrics()
        })
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(sale)
            db.session.commit()
            return jsonify({'message': 'Sale deleted successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': f'Error deleting sale: {str(e)}'}), 500

@app.route('/api/low-stock-alerts', methods=['GET'])
def get_low_stock_alerts():
    low_stock_ingredients = Ingredient.query.filter(
        Ingredient.get_stock_in_base_unit(Ingredient) <= Ingredient.get_threshold_in_base_unit(Ingredient)
    ).all()
    
    return jsonify([{
        'id': i.id,
        'name': i.name,
        'current_stock': i.current_stock,
        'min_threshold': i.min_threshold,
        'unit': i.stock_unit
    } for i in low_stock_ingredients])

@app.route('/api/stock-updates', methods=['GET', 'POST'])
def handle_stock_updates():
    if request.method == 'POST':
        try:
            data = request.json
            
            # Validate required fields
            required_fields = ['ingredient_id', 'quantity', 'cost_per_unit']
            for field in required_fields:
                if field not in data:
                    return jsonify({'message': f'Missing required field: {field}'}), 400
            
            ingredient = Ingredient.query.get_or_404(data['ingredient_id'])
            
            # Calculate total cost
            total_cost = data['quantity'] * data['cost_per_unit']
            
            # Create stock update record
            stock_update = StockUpdate(
                ingredient_id=data['ingredient_id'],
                quantity=data['quantity'],
                cost_per_unit=data['cost_per_unit'],
                total_cost=total_cost,
                notes=data.get('notes', '')
            )
            
            # Update ingredient stock
            ingredient.current_stock += data['quantity']
            # Update ingredient cost per unit with weighted average
            total_old_value = ingredient.current_stock * ingredient.cost_per_unit
            total_new_value = data['quantity'] * data['cost_per_unit']
            new_total_stock = ingredient.current_stock + data['quantity']
            ingredient.cost_per_unit = (total_old_value + total_new_value) / new_total_stock
            
            db.session.add(stock_update)
            db.session.commit()
            
            return jsonify({
                'message': 'Stock update recorded successfully',
                'new_stock_level': ingredient.current_stock,
                'new_cost_per_unit': ingredient.cost_per_unit
            }), 201
        except Exception as e:
            print('Error recording stock update:', str(e))
            db.session.rollback()
            return jsonify({'message': f'Error recording stock update: {str(e)}'}), 500
    
    # GET request - return all stock updates with ingredient details
    stock_updates = StockUpdate.query.order_by(StockUpdate.date.desc()).all()
    return jsonify([{
        'id': su.id,
        'ingredient_name': su.ingredient.name,
        'quantity': su.quantity,
        'unit': su.ingredient.stock_unit,
        'cost_per_unit': su.cost_per_unit,
        'total_cost': su.total_cost,
        'date': su.date.isoformat(),
        'notes': su.notes
    } for su in stock_updates])

@app.route('/api/stock-updates/<int:id>', methods=['DELETE'])
def handle_stock_update(id):
    stock_update = StockUpdate.query.get_or_404(id)
    ingredient = stock_update.ingredient
    
    try:
        # Revert the stock update
        ingredient.current_stock -= stock_update.quantity
        
        # Revert the cost per unit (simplified version)
        if ingredient.current_stock > 0:
            total_value = (ingredient.current_stock + stock_update.quantity) * ingredient.cost_per_unit
            total_value -= stock_update.quantity * stock_update.cost_per_unit
            ingredient.cost_per_unit = total_value / ingredient.current_stock
        
        db.session.delete(stock_update)
        db.session.commit()
        
        return jsonify({'message': 'Stock update deleted successfully'}), 200
    except Exception as e:
        print('Error deleting stock update:', str(e))
        db.session.rollback()
        return jsonify({'message': f'Error deleting stock update: {str(e)}'}), 500

@app.route('/api/finance', methods=['GET'])
def get_finance_overview():
    overview = FinanceOverview.query.first()
    return jsonify({
        'starting_balance': overview.starting_balance,
        'total_income': overview.total_income,
        'total_expenses': overview.total_expenses,
        'current_balance': overview.current_balance
    })

@app.route('/api/profit-report', methods=['GET'])
def get_profit_report():
    try:
        period = request.args.get('period', 'daily')  # daily, weekly, or monthly
        selected_date = request.args.get('date')
        
        if selected_date:
            selected_date = datetime.fromisoformat(selected_date.replace('Z', '+00:00'))
        else:
            selected_date = datetime.utcnow()
            
        if period == 'daily':
            start_date = selected_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
            group_format = '%Y-%m-%d %H:00:00'
            interval = 'hour'
        elif period == 'weekly':
            # Start from Monday of the selected week
            start_date = selected_date - timedelta(days=selected_date.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=7)
            group_format = '%Y-%m-%d'
            interval = 'day'
        else:  # monthly
            # Start from first day of the selected month
            start_date = selected_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Go to first day of next month
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year + 1, month=1)
            else:
                end_date = start_date.replace(month=start_date.month + 1)
            group_format = '%Y-%m-%d'
            interval = 'day'

        # Get all sales in the period
        sales = Sale.query.filter(
            Sale.date >= start_date,
            Sale.date < end_date
        ).all()

        # Calculate profits
        profits = {}
        total_revenue = 0
        total_cost = 0
        
        # Initialize all intervals in the range
        current = start_date
        while current < end_date:
            key = current.strftime(group_format)
            profits[key] = {
                'revenue': 0,
                'cost': 0,
                'profit': 0,
                'sales_count': 0
            }
            if interval == 'hour':
                current += timedelta(hours=1)
            else:
                current += timedelta(days=1)
        
        for sale in sales:
            # Get the date key based on the interval
            date_key = sale.date.strftime(group_format)
            
            # Calculate metrics for this sale
            metrics = sale.calculate_metrics()
            revenue = metrics['revenue']
            cost = metrics['cost']
            profit = metrics['profit']
            
            # Add to totals
            total_revenue += revenue
            total_cost += cost
            
            # Group by interval
            if date_key in profits:
                profits[date_key]['revenue'] += revenue
                profits[date_key]['cost'] += cost
                profits[date_key]['profit'] += profit
                profits[date_key]['sales_count'] += 1

        # Convert to list and sort by date
        profit_data = [
            {
                'date': key,
                'revenue': data['revenue'],
                'cost': data['cost'],
                'profit': data['profit'],
                'sales_count': data['sales_count']
            }
            for key, data in profits.items()
        ]
        profit_data.sort(key=lambda x: x['date'])

        return jsonify({
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_revenue': total_revenue,
            'total_cost': total_cost,
            'total_profit': total_revenue - total_cost,
            'data': profit_data
        })

    except Exception as e:
        print('Error getting profit report:', str(e))
        return jsonify({'message': f'Error getting profit report: {str(e)}'}), 500

@app.route('/api/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "version": "1.0.1",
        "message": "Coffee Shop Manager is running!"
    }), 200

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"404 error: {error}")
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {error}")
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# Root path handler
@app.route('/')
def index():
    try:
        logger.info("Serving index.html")
        return send_from_directory(app.static_folder, 'index.html')
    except Exception as e:
        logger.error(f"Error serving index: {str(e)}")
        return Response("Application is running", mimetype='text/plain')

# Serve React App - this should be after all API routes
@app.route('/<path:path>')
def serve(path):
    try:
        logger.info(f"Serving path: {path}")
        if path.startswith('api/'):
            return jsonify({'error': 'Not found'}), 404
        if os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, 'index.html')
    except Exception as e:
        logger.error(f"Error serving {path}: {str(e)}")
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    with app.app_context():
        # Create all tables
        db.create_all()

        # Add initial data only if tables are empty
        if not IngredientCategory.query.first():
            categories = [
                IngredientCategory(name='Coffee Beans'),
                IngredientCategory(name='Milk'),
                IngredientCategory(name='Syrups'),
                IngredientCategory(name='Toppings')
            ]
            db.session.add_all(categories)
            db.session.commit()

        if not FinanceOverview.query.first():
            overview = FinanceOverview(
                starting_balance=10000.0,
                total_income=0.0,
                total_expenses=0.0,
                current_balance=10000.0
            )
            db.session.add(overview)
            db.session.commit()

    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
