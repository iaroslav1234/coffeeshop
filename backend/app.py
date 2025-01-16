from flask import Flask, request, jsonify, send_from_directory, Response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask_migrate import Migrate
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
migrate = Migrate(app, db)

# Helper function for unit conversion
def convert_to_base_unit(value, from_unit):
    """Convert a value to its base unit (g or ml)"""
    if from_unit == 'kg':
        return value * 1000  # Convert to grams (1 kg = 1000g)
    elif from_unit == 'l':
        return value * 1000  # Convert to milliliters (1 l = 1000ml)
    return value  # Already in base unit (g or ml)

def convert_from_base_unit(value, to_unit):
    """Convert a value from its base unit (g or ml) to the target unit"""
    if to_unit == 'kg':
        return value / 1000  # Convert from grams to kg (1000g = 1 kg)
    elif to_unit == 'l':
        return value / 1000  # Convert from milliliters to l (1000ml = 1 l)
    return value  # Keep in base unit (g or ml)

def calculate_ingredient_cost(ingredient, quantity, unit):
    """Calculate the cost of an ingredient with proper unit conversion"""
    # Convert ingredient quantity to base unit (g or ml)
    base_quantity = convert_to_base_unit(quantity, unit)
    
    # Get cost in base unit
    base_cost = ingredient.current_cost_per_unit
    if ingredient.cost_unit == 'kg':
        base_cost = base_cost / 1000  # Convert from per kg to per g
    elif ingredient.cost_unit == 'l':
        base_cost = base_cost / 1000  # Convert from per l to per ml
    
    # Calculate total cost
    return base_quantity * base_cost

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
        """Calculate the total cost of the product based on its ingredients"""
        total_cost = 0
        for ingredient in self.ingredients:
            total_cost += calculate_ingredient_cost(ingredient.ingredient_ref, ingredient.quantity, ingredient.unit)
        return round(total_cost, 2)

    def calculate_profit(self):
        """Calculate the profit margin of the product"""
        cost = self.calculate_cost()
        return round(self.selling_price - cost, 2)

class IngredientCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    ingredients = db.relationship('Ingredient', backref='category_ref', lazy=True)

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('ingredient_category.id'), nullable=False)
    current_stock = db.Column(db.Float, nullable=False, default=0)
    stock_unit = db.Column(db.String(10), nullable=False)  # 'g', 'ml'
    min_threshold = db.Column(db.Float, nullable=False)
    threshold_unit = db.Column(db.String(10), nullable=False)  # 'g', 'ml'
    current_cost_per_unit = db.Column(db.Float, nullable=False)  # Current price, can be updated without affecting history
    cost_unit = db.Column(db.String(10), nullable=False)  # 'g', 'ml'
    products = db.relationship('ProductIngredient', backref='ingredient_ref', lazy=True)
    stock_updates = db.relationship('StockUpdate', backref='ingredient', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category_id': self.category_id,
            'category_name': self.category_ref.name,
            'current_stock': self.current_stock,
            'stock_unit': self.stock_unit,
            'min_threshold': self.min_threshold,
            'threshold_unit': self.threshold_unit,
            'current_cost_per_unit': self.current_cost_per_unit,
            'cost_unit': self.cost_unit
        }

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
    original_unit = db.Column(db.String(10), nullable=False)
    original_cost_per_unit = db.Column(db.Float, nullable=False)
    cost_unit = db.Column(db.String(10), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.Text)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def calculate_metrics(self):
        try:
            if not self.product_ref:
                print(f"No product reference found for sale {self.id}")
                return {
                    'cost': 0,
                    'revenue': 0,
                    'profit': 0
                }

            # Get the selling price and quantity
            selling_price = float(self.product_ref.selling_price)
            quantity = int(self.quantity)
            revenue = selling_price * quantity
            
            print(f"DEBUG: Product: {self.product_ref.name}")
            print(f"DEBUG: Selling price: {selling_price}")
            print(f"DEBUG: Quantity: {quantity}")
            print(f"DEBUG: Calculated revenue: {revenue}")

            # Try to calculate cost, default to 0 if there's an error
            try:
                cost = self.product_ref.calculate_cost() * quantity
                print(f"DEBUG: Calculated cost: {cost}")
            except Exception as cost_error:
                print(f"Error calculating cost: {str(cost_error)}")
                cost = 0

            profit = revenue - cost
            print(f"DEBUG: Final metrics - Cost: {cost}, Revenue: {revenue}, Profit: {profit}")
            
            return {
                'cost': round(cost, 2),
                'revenue': round(revenue, 2),
                'profit': round(profit, 2)
            }
        except Exception as e:
            print(f"Error in calculate_metrics: {str(e)}")
            # Return a safe fallback
            return {
                'cost': 0,
                'revenue': 0,
                'profit': 0
            }

class FinanceOverview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    starting_balance = db.Column(db.Float, nullable=False)
    total_income = db.Column(db.Float, nullable=False)
    total_expenses = db.Column(db.Float, nullable=False)
    current_balance = db.Column(db.Float, nullable=False)

class CashTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    type = db.Column(db.String(20), nullable=False)  # 'deposit' or 'withdrawal'
    amount = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    balance_after = db.Column(db.Float, nullable=False)

# Routes
@app.route('/api/ingredients', methods=['GET', 'POST'])
def handle_ingredients():
    if request.method == 'POST':
        try:
            data = request.json
            
            # Validate required fields
            required_fields = ['name', 'category_id', 'current_stock', 'stock_unit', 
                             'min_threshold', 'threshold_unit', 'current_cost_per_unit']
            for field in required_fields:
                if field not in data:
                    return jsonify({'message': f'Missing required field: {field}'}), 400
                if data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
                    return jsonify({'message': f'Field cannot be empty: {field}'}), 400
            
            # Validate numeric fields
            numeric_fields = ['current_stock', 'min_threshold', 'current_cost_per_unit']
            for field in numeric_fields:
                try:
                    float(data[field])
                except (TypeError, ValueError):
                    return jsonify({'message': f'Invalid numeric value for {field}'}), 400
            
            # Validate category exists
            category = IngredientCategory.query.get(data['category_id'])
            if not category:
                return jsonify({'message': 'Invalid category ID'}), 400
            
            # Get values from request
            current_stock = float(data['current_stock'])
            min_threshold = float(data['min_threshold'])
            current_cost_per_unit = float(data['current_cost_per_unit'])
            
            ingredient = Ingredient(
                name=data['name'],
                category_id=data['category_id'],
                current_stock=current_stock,
                stock_unit=data['stock_unit'],
                min_threshold=min_threshold,
                threshold_unit=data['threshold_unit'],
                current_cost_per_unit=current_cost_per_unit,
                cost_unit=data['stock_unit']
            )
            
            db.session.add(ingredient)
            db.session.commit()
            
            return jsonify({
                'message': 'Ingredient added successfully',
                'ingredient': ingredient.to_dict()
            }), 201
        except Exception as e:
            print('Error creating ingredient:', str(e))
            db.session.rollback()
            return jsonify({'message': f'Error creating ingredient: {str(e)}'}), 500
    
    # GET request - return ingredients with category information
    ingredients = Ingredient.query.join(IngredientCategory).order_by(IngredientCategory.name, Ingredient.name).all()
    return jsonify([i.to_dict() for i in ingredients])

@app.route('/api/ingredients/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def handle_ingredient(id):
    ingredient = Ingredient.query.get_or_404(id)
    
    if request.method == 'PUT':
        try:
            data = request.json
            
            # Validate required fields
            required_fields = ['name', 'category_id', 'current_stock', 'stock_unit', 'min_threshold', 'threshold_unit', 'current_cost_per_unit']
            for field in required_fields:
                if field not in data:
                    return jsonify({'message': f'Missing required field: {field}'}), 400
                if data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
                    return jsonify({'message': f'Field cannot be empty: {field}'}), 400
            
            # Validate numeric fields
            numeric_fields = ['current_stock', 'min_threshold', 'current_cost_per_unit']
            for field in numeric_fields:
                try:
                    float(data[field])
                except (TypeError, ValueError):
                    return jsonify({'message': f'Invalid numeric value for {field}'}), 400
            
            # Validate category exists
            if data['category_id'] != ingredient.category_id:
                category = IngredientCategory.query.get(data['category_id'])
                if not category:
                    return jsonify({'message': 'Invalid category ID'}), 400
            
            # Get values from request
            current_stock = float(data['current_stock'])
            min_threshold = float(data['min_threshold'])
            current_cost_per_unit = float(data['current_cost_per_unit'])
            
            # Update ingredient
            ingredient.name = data['name']
            ingredient.category_id = data['category_id']
            ingredient.current_stock = current_stock
            ingredient.stock_unit = data['stock_unit']  
            ingredient.min_threshold = min_threshold
            ingredient.threshold_unit = data['threshold_unit']  
            ingredient.current_cost_per_unit = current_cost_per_unit
            ingredient.cost_unit = data['stock_unit']  
            
            db.session.commit()
            
            return jsonify({
                'message': 'Ingredient updated successfully',
                'ingredient': ingredient.to_dict()
            })
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
    
    # GET request
    return jsonify(ingredient.to_dict())

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
            
            # Get the product and validate it exists
            product = Product.query.get(data['product_id'])
            if not product:
                return jsonify({'message': 'Product not found'}), 404

            # Check if we have enough stock for all ingredients
            quantity = data['quantity']
            
            # Skip stock check if product has no ingredients
            if product.ingredients:
                for product_ingredient in product.ingredients:
                    ingredient = product_ingredient.ingredient_ref
                    print(f"DEBUG: Processing ingredient {ingredient.name}")
                    print(f"DEBUG: Recipe requires {product_ingredient.quantity} {product_ingredient.unit}")
                    print(f"DEBUG: Sale quantity is {quantity}")
                    print(f"DEBUG: Current stock is {ingredient.current_stock} {ingredient.stock_unit}")
                    
                    # First convert recipe amount to base unit (g/ml)
                    recipe_amount_base = convert_to_base_unit(
                        product_ingredient.quantity * quantity,
                        product_ingredient.unit
                    )
                    
                    # Convert current stock to base unit
                    current_stock_base = convert_to_base_unit(
                        ingredient.current_stock,
                        ingredient.stock_unit
                    )
                    
                    print(f"DEBUG: Recipe needs {recipe_amount_base}g")
                    print(f"DEBUG: Current stock is {current_stock_base}g")
                    
                    # Check if we have enough stock
                    if current_stock_base < recipe_amount_base:
                        return jsonify({
                            'message': f'Insufficient stock for ingredient: {ingredient.name}. ' +
                                     f'Need {recipe_amount_base}g but only have {current_stock_base}g'
                        }), 400

                    # Calculate new stock in base unit
                    new_stock_base = current_stock_base - recipe_amount_base
                    print(f"DEBUG: New stock will be {new_stock_base}g")
                    
                    # Convert new stock back to stock unit
                    new_stock = convert_from_base_unit(
                        new_stock_base,
                        ingredient.stock_unit
                    )
                    print(f"DEBUG: Setting new stock to {new_stock} {ingredient.stock_unit}")
                    
                    # Update the stock
                    ingredient.current_stock = round(new_stock, 3)

            # Create the sale
            sale = Sale(
                date=datetime.fromisoformat(data['date']),
                product_id=data['product_id'],
                quantity=quantity
            )
            
            # Calculate metrics
            metrics = sale.calculate_metrics()
            if not metrics:
                return jsonify({'message': 'Error: Could not calculate sale metrics'}), 500
            
            # Update finance overview
            overview = FinanceOverview.query.first()
            if not overview:
                overview = FinanceOverview(
                    starting_balance=10000,  # Default starting balance
                    total_income=0,
                    total_expenses=0,
                    current_balance=10000
                )
                db.session.add(overview)
            
            # Calculate sale amount and cost
            sale_amount = product.selling_price * quantity
            cost_amount = product.calculate_cost() * quantity if product.ingredients else 0
            
            # For debugging
            print(f"DEBUG: Before sale - Current balance: {overview.current_balance}")
            print(f"DEBUG: Sale amount: {sale_amount}")
            
            # Update finance overview totals and balance
            overview.total_income += sale_amount
            if cost_amount > 0:
                overview.total_expenses += cost_amount
            overview.current_balance += sale_amount  # Only add sale amount to balance
            
            print(f"DEBUG: After sale - Current balance: {overview.current_balance}")

            # Create a cash transaction for the sale revenue
            transaction = CashTransaction(
                date=sale.date,
                type='sale',
                amount=sale_amount,  
                notes=f'Sale of {quantity}x {product.name}',
                balance_after=overview.current_balance
            )
            db.session.add(transaction)
            
            # Save the sale
            db.session.add(sale)
            db.session.commit()
            
            return jsonify({
                'message': 'Sale created successfully',
                'metrics': metrics
            }), 201
            
        except Exception as e:
            print('Error creating sale:', str(e))
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
        metrics = sale.calculate_metrics()
        return jsonify({
            'id': sale.id,
            'date': sale.date.isoformat(),
            'product_id': sale.product_id,
            'product_name': sale.product_ref.name,
            'quantity': sale.quantity,
            **(metrics if metrics else {})
        })
    
    elif request.method == 'DELETE':
        try:
            # Calculate metrics before deleting
            metrics = sale.calculate_metrics()
            if metrics:
                # Update finance overview
                overview = FinanceOverview.query.first()
                if overview:
                    # Subtract this sale's numbers from totals
                    overview.total_income -= metrics['revenue']
                    overview.total_expenses -= metrics['cost']
                    overview.current_balance = overview.starting_balance + overview.total_income

            # Return ingredients to stock
            for product_ingredient in sale.product_ref.ingredients:
                ingredient = product_ingredient.ingredient_ref
                required_amount = convert_to_base_unit(
                    product_ingredient.quantity * sale.quantity,
                    product_ingredient.unit
                )
                
                # Convert the amount to the ingredient's stock unit
                amount_in_stock_unit = convert_from_base_unit(
                    required_amount,
                    ingredient.stock_unit
                )
                
                # Add back to stock
                ingredient.current_stock += amount_in_stock_unit
            
            db.session.delete(sale)
            db.session.commit()
            return jsonify({'message': 'Sale deleted successfully'})
        except Exception as e:
            print('Error deleting sale:', str(e))
            db.session.rollback()
            return jsonify({'message': f'Error deleting sale: {str(e)}'}), 500

@app.route('/api/low-stock-alerts', methods=['GET'])
def get_low_stock_alerts():
    low_stock_ingredients = Ingredient.query.filter(
        Ingredient.current_stock <= Ingredient.min_threshold
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
    if request.method == 'GET':
        stock_updates = StockUpdate.query.order_by(StockUpdate.date.desc()).all()
        return jsonify([{
            'id': update.id,
            'ingredient_id': update.ingredient_id,
            'ingredient_name': update.ingredient.name,
            'category_name': update.ingredient.category_ref.name,
            'quantity': update.quantity,
            'original_unit': update.original_unit,
            'original_cost_per_unit': update.original_cost_per_unit,
            'cost_unit': update.cost_unit,
            'notes': update.notes,
            'date': update.date.isoformat()
        } for update in stock_updates])

    elif request.method == 'POST':
        try:
            data = request.json
            print("Received stock update data:", data)
            
            # Get the ingredient
            ingredient = Ingredient.query.get(data['ingredient_id'])
            if not ingredient:
                return jsonify({'message': 'Ingredient not found'}), 404
            
            # Create the stock update
            stock_update = StockUpdate(
                ingredient_id=data['ingredient_id'],
                quantity=data['quantity'],
                original_unit=data['unit'],
                original_cost_per_unit=data['cost_per_unit'],
                cost_unit=data['cost_unit'],
                date=datetime.fromisoformat(data['date']),
                notes=data.get('notes', '')
            )
            
            # Convert quantity to match the ingredient's stock unit
            if stock_update.original_unit != ingredient.stock_unit:
                # First convert to base unit
                base_quantity = convert_to_base_unit(
                    stock_update.quantity,
                    stock_update.original_unit
                )
                # Then convert to stock unit
                stock_quantity = convert_from_base_unit(
                    base_quantity,
                    ingredient.stock_unit
                )
            else:
                stock_quantity = stock_update.quantity
            
            # Update the ingredient's stock and cost
            ingredient.current_stock += stock_quantity
            
            # If cost unit matches, update the cost directly
            if stock_update.cost_unit == ingredient.cost_unit:
                ingredient.current_cost_per_unit = stock_update.original_cost_per_unit
            else:
                # Convert cost to match the ingredient's cost unit
                if stock_update.cost_unit in ['kg', 'l'] and ingredient.cost_unit in ['g', 'ml']:
                    # If update is per kg but ingredient tracks per g, divide by 1000
                    ingredient.current_cost_per_unit = stock_update.original_cost_per_unit / 1000
                elif stock_update.cost_unit in ['g', 'ml'] and ingredient.cost_unit in ['kg', 'l']:
                    # If update is per g but ingredient tracks per kg, multiply by 1000
                    ingredient.current_cost_per_unit = stock_update.original_cost_per_unit * 1000
            
            # Save everything
            db.session.add(stock_update)
            db.session.commit()
            
            return jsonify({
                'message': 'Stock update created successfully',
                'current_stock': ingredient.current_stock,
                'current_cost_per_unit': ingredient.current_cost_per_unit
            }), 201
            
        except Exception as e:
            print('Error creating stock update:', str(e))
            db.session.rollback()
            return jsonify({'message': f'Error creating stock update: {str(e)}'}), 500

@app.route('/api/stock-updates/<int:id>', methods=['DELETE'])
def handle_stock_update(id):
    stock_update = StockUpdate.query.get_or_404(id)
    ingredient = stock_update.ingredient
    
    try:
        # Revert the stock update
        ingredient.current_stock -= stock_update.quantity
        
        # Revert the cost per unit (simplified version)
        if ingredient.current_stock > 0:
            total_value = (ingredient.current_stock + stock_update.quantity) * ingredient.current_cost_per_unit
            total_value -= stock_update.quantity * stock_update.original_cost_per_unit
            ingredient.current_cost_per_unit = total_value / ingredient.current_stock
        
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
    if not overview:
        # Initialize finance overview if it doesn't exist
        overview = FinanceOverview(
            starting_balance=10000.0,
            total_income=0.0,
            total_expenses=0.0,
            current_balance=10000.0
        )
        db.session.add(overview)
        db.session.commit()
        
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
            metrics = sale.calculate_metrics()
            if not metrics:
                continue
                
            key = sale.date.strftime(group_format)
            profits[key]['revenue'] += metrics['revenue']
            profits[key]['cost'] += metrics['cost']
            profits[key]['profit'] = profits[key]['revenue'] - profits[key]['cost']
            profits[key]['sales_count'] += 1
            
            total_revenue += metrics['revenue']
            total_cost += metrics['cost']
        
        # Convert to list and sort by date
        data = [{
            'date': key,
            'revenue': values['revenue'],
            'cost': values['cost'],
            'profit': values['profit'],
            'sales_count': values['sales_count']
        } for key, values in profits.items()]
        data.sort(key=lambda x: x['date'])
        
        return jsonify({
            'data': data,
            'total_revenue': total_revenue,
            'total_cost': total_cost,
            'total_profit': total_revenue - total_cost,
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
        
    except Exception as e:
        print('Error getting profit report:', str(e))
        return jsonify({'message': f'Error getting profit report: {str(e)}'}), 500

@app.route('/api/debug/ingredient/<int:id>', methods=['GET'])
def debug_ingredient(id):
    ingredient = Ingredient.query.get_or_404(id)
    return jsonify({
        'id': ingredient.id,
        'name': ingredient.name,
        'current_cost_per_unit': ingredient.current_cost_per_unit,
        'cost_unit': ingredient.cost_unit,
        'stock_updates': [{
            'quantity': update.quantity,
            'original_unit': update.original_unit,
            'original_cost_per_unit': update.original_cost_per_unit,
            'cost_unit': update.cost_unit,
            'date': update.date.isoformat()
        } for update in ingredient.stock_updates]
    })

@app.route('/api/cash-transactions', methods=['GET', 'POST'])
def handle_cash_transactions():
    if request.method == 'POST':
        try:
            data = request.json
            transaction_type = data['type']
            amount = float(data['amount'])
            notes = data.get('notes', '')

            # Get current balance
            overview = FinanceOverview.query.first()
            if not overview:
                return jsonify({'message': 'Finance overview not found'}), 404

            # For debugging
            print(f"DEBUG: Before transaction - Current balance: {overview.current_balance}")
            print(f"DEBUG: Transaction type: {transaction_type}")
            print(f"DEBUG: Amount: {amount}")

            # Calculate new balance based on transaction type
            if transaction_type == 'deposit':
                # For deposits, just add to current balance (don't affect total_income)
                new_balance = overview.current_balance + amount
            else:  # withdrawal
                # For withdrawals, check if we have enough funds
                if overview.current_balance < amount:
                    return jsonify({'message': 'Insufficient funds'}), 400
                new_balance = overview.current_balance - amount

            print(f"DEBUG: New balance: {new_balance}")

            # Create transaction with proper amount sign
            transaction = CashTransaction(
                type=transaction_type,
                amount=amount if transaction_type in ['deposit', 'sale'] else -amount,  
                notes=notes,
                balance_after=new_balance
            )
            
            # Update current balance only (don't modify total_income or total_expenses)
            overview.current_balance = new_balance

            db.session.add(transaction)
            db.session.commit()

            # For debugging
            print(f"DEBUG: After commit - Current balance: {overview.current_balance}")
            print(f"DEBUG: Total income: {overview.total_income}")  # Should not change for deposits/withdrawals
            
            return jsonify({
                'message': f'Cash {transaction_type} successful',
                'transaction': {
                    'id': transaction.id,
                    'date': transaction.date.isoformat(),
                    'type': transaction.type,
                    'amount': transaction.amount,
                    'notes': transaction.notes,
                    'balance_after': transaction.balance_after
                }
            }), 201

        except Exception as e:
            print('Error creating cash transaction:', str(e))
            db.session.rollback()
            return jsonify({'message': f'Error creating cash transaction: {str(e)}'}), 500

    # GET method
    transactions = CashTransaction.query.order_by(CashTransaction.date.desc()).all()
    return jsonify([{
        'id': t.id,
        'date': t.date.isoformat(),
        'type': t.type,
        'amount': t.amount,
        'notes': t.notes,
        'balance_after': t.balance_after
    } for t in transactions])

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
