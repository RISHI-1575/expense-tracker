# app.py - Flask Application

from flask import Flask, render_template, request, jsonify, redirect, url_for
import mysql.connector
from datetime import datetime, timedelta
import json
import plotly
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import calendar
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Database configuration
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'expense_tracker')
}

# Database setup function
def setup_database():
    try:
        conn = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password']
        )
        cursor = conn.cursor()
        
        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
        cursor.execute(f"USE {db_config['database']}")
        
        # Create expenses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                amount DECIMAL(10, 2) NOT NULL,
                payment_type VARCHAR(10) NOT NULL,
                category VARCHAR(50) NOT NULL,
                expense_date DATE NOT NULL,
                description VARCHAR(255) NOT NULL,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Database setup complete.")
    except Exception as e:
        print(f"Database setup error: {e}")

# Run database setup
setup_database()

# Helper function to get database connection
def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# API Endpoints
@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category = request.args.get('category')
        month = request.args.get('month')
        year = request.args.get('year')
        
        query = "SELECT * FROM expenses WHERE 1=1"
        params = []
        
        if start_date and end_date:
            query += " AND expense_date BETWEEN %s AND %s"
            params.extend([start_date, end_date])
        elif month and year:
            query += " AND MONTH(expense_date) = %s AND YEAR(expense_date) = %s"
            params.extend([month, year])
        
        if category and category != 'All':
            query += " AND category = %s"
            params.append(category)
            
        query += " ORDER BY expense_date DESC"
        
        cursor.execute(query, params)
        expenses = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Convert date objects to string for JSON serialization
        for expense in expenses:
            expense['expense_date'] = expense['expense_date'].strftime('%Y-%m-%d')
            expense['created_at'] = expense['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
        return jsonify(expenses)
    except Exception as e:
        print(f"Error fetching expenses: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    try:
        data = request.json
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            INSERT INTO expenses 
            (amount, payment_type, category, expense_date, description, comment)
            VALUES (%s, %s, %s, %s, %s, %s)
        '''
        
        cursor.execute(query, (
            data['amount'],
            data['payment_type'],
            data['category'],
            data['expense_date'],
            data['description'],
            data.get('comment', '')
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Expense added successfully"}), 201
    except Exception as e:
        print(f"Error adding expense: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/expenses/<int:expense_id>', methods=['PUT'])
def update_expense(expense_id):
    try:
        data = request.json
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            UPDATE expenses 
            SET amount = %s, payment_type = %s, category = %s, 
                expense_date = %s, description = %s, comment = %s
            WHERE id = %s
        '''
        
        cursor.execute(query, (
            data['amount'],
            data['payment_type'],
            data['category'],
            data['expense_date'],
            data['description'],
            data.get('comment', ''),
            expense_id
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Expense updated successfully"})
    except Exception as e:
        print(f"Error updating expense: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "DELETE FROM expenses WHERE id = %s"
        cursor.execute(query, (expense_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Expense deleted successfully"})
    except Exception as e:
        print(f"Error deleting expense: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/reports/total', methods=['GET'])
def get_total_report():
    try:
        period = request.args.get('period', 'month')  # day, week, month
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if period == 'day':
            # Today's expenses
            today = datetime.now().strftime('%Y-%m-%d')
            query = '''
                SELECT 
                    SUM(amount) as total,
                    payment_type,
                    expense_date
                FROM expenses 
                WHERE expense_date = %s
                GROUP BY payment_type, expense_date
            '''
            cursor.execute(query, (today,))
        elif period == 'week':
            # This week's expenses
            today = datetime.now()
            start_of_week = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
            end_of_week = (today + timedelta(days=6-today.weekday())).strftime('%Y-%m-%d')
            query = '''
                SELECT 
                    SUM(amount) as total,
                    payment_type,
                    DATE_FORMAT(expense_date, '%%Y-%%U') as week
                FROM expenses 
                WHERE expense_date BETWEEN %s AND %s
                GROUP BY payment_type, week
            '''
            cursor.execute(query, (start_of_week, end_of_week))
        else:  # month
            # This month's expenses
            today = datetime.now()
            start_of_month = datetime(today.year, today.month, 1).strftime('%Y-%m-%d')
            # Determine the last day of the month
            if today.month == 12:
                end_of_month = datetime(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_of_month = datetime(today.year, today.month + 1, 1) - timedelta(days=1)
            end_of_month = end_of_month.strftime('%Y-%m-%d')
            
            query = '''
                SELECT 
                    SUM(amount) as total,
                    payment_type,
                    DATE_FORMAT(expense_date, '%%Y-%%m') as month
                FROM expenses 
                WHERE expense_date BETWEEN %s AND %s
                GROUP BY payment_type, month
            '''
            cursor.execute(query, (start_of_month, end_of_month))
        
        results = cursor.fetchall()
        
        # Also get the overall total
        if period == 'day':
            query = "SELECT SUM(amount) as grand_total FROM expenses WHERE expense_date = %s"
            cursor.execute(query, (today,))
        elif period == 'week':
            query = "SELECT SUM(amount) as grand_total FROM expenses WHERE expense_date BETWEEN %s AND %s"
            cursor.execute(query, (start_of_week, end_of_week))
        else:  # month
            query = "SELECT SUM(amount) as grand_total FROM expenses WHERE expense_date BETWEEN %s AND %s"
            cursor.execute(query, (start_of_month, end_of_month))
            
        grand_total = cursor.fetchone()['grand_total'] or 0
        
        cursor.close()
        conn.close()
        
        # Format the response
        totals = {
            'grand_total': float(grand_total),
            'by_type': {}
        }
        
        for result in results:
            payment_type = result['payment_type']
            total = float(result['total']) if result['total'] else 0
            totals['by_type'][payment_type] = total
            
        return jsonify(totals)
    except Exception as e:
        print(f"Error getting total report: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/reports/category', methods=['GET'])
def get_category_report():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = '''
            SELECT 
                category,
                SUM(amount) as total
            FROM expenses 
        '''
        
        params = []
        if start_date and end_date:
            query += " WHERE expense_date BETWEEN %s AND %s"
            params.extend([start_date, end_date])
            
        query += " GROUP BY category ORDER BY total DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Create chart data
        categories = [item['category'] for item in results]
        values = [float(item['total']) for item in results]
        
        fig = px.pie(
            names=categories,
            values=values,
            title="Expenses by Category",
            hole=0.3,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        # Return both raw data and chart
        return jsonify({
            "data": results,
            "chart": chart_json
        })
    except Exception as e:
        print(f"Error getting category report: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/reports/monthly-trend', methods=['GET'])
def get_monthly_trend():
    try:
        year = request.args.get('year', datetime.now().year)
        show_split = request.args.get('show_split', 'false').lower() == 'true'
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get monthly totals
        if show_split:
            query = '''
                SELECT 
                    MONTH(expense_date) as month,
                    payment_type,
                    SUM(amount) as total
                FROM expenses 
                WHERE YEAR(expense_date) = %s
                GROUP BY MONTH(expense_date), payment_type
                ORDER BY month
            '''
        else:
            query = '''
                SELECT 
                    MONTH(expense_date) as month,
                    SUM(amount) as total
                FROM expenses 
                WHERE YEAR(expense_date) = %s
                GROUP BY MONTH(expense_date)
                ORDER BY month
            '''
            
        cursor.execute(query, (year,))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Prepare data for chart
        month_names = [calendar.month_abbr[i] for i in range(1, 13)]
        
        if show_split:
            # Initialize data structure with zeros
            bank_data = [0] * 12
            cash_data = [0] * 12
            
            for row in results:
                month_idx = int(row['month']) - 1  # Adjust for 0-based index
                if row['payment_type'] == 'Bank':
                    bank_data[month_idx] = float(row['total'])
                else:  # Cash
                    cash_data[month_idx] = float(row['total'])
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=month_names,
                y=bank_data,
                mode='lines+markers',
                name='Bank',
                line=dict(color='royalblue', width=3),
                marker=dict(size=8)
            ))
            fig.add_trace(go.Scatter(
                x=month_names,
                y=cash_data,
                mode='lines+markers',
                name='Cash',
                line=dict(color='orange', width=3),
                marker=dict(size=8)
            ))
        else:
            # Initialize with zeros
            monthly_data = [0] * 12
            
            for row in results:
                month_idx = int(row['month']) - 1  # Adjust for 0-based index
                monthly_data[month_idx] = float(row['total'])
                
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=month_names,
                y=monthly_data,
                mode='lines+markers',
                name='Total Expenses',
                line=dict(color='mediumseagreen', width=3),
                marker=dict(size=8)
            ))
            
        fig.update_layout(
            title=f"Monthly Expense Trend ({year})",
            xaxis_title="Month",
            yaxis_title="Total Expenses",
            legend_title="Payment Type" if show_split else None,
            template="plotly_white"
        )
        
        chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        return jsonify({
            "data": results,
            "chart": chart_json
        })
    except Exception as e:
        print(f"Error getting monthly trend: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)