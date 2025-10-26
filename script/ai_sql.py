import os
from query_runner import SQLAnalysisRunner
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))



class AISQLRunner:
    def __init__(self):
        self.ai_result = {}
        self.sql_runner = SQLAnalysisRunner()
        self.sql_result = None
        self.chat_history = [{"role": "system", "content": "You are an experienced data analyst. Based on the SQL results provided, analyze the data and provide comprehensive findings. Focus on key insights, trends, and business implications."},]
            
    def ask_ai(self, prompt):
        
        print("\n" + "="*80)
        print(f"AI ANALYST: {prompt}")
        print("="*80)
        
        # Use AI to determine if this question
        classification_prompt = f"""
        Analyze this question and determine if it requires SQL database querying or is a conversational question.
        
        Question: "{prompt}"
        
        Respond with ONLY one word:
        - "SQL" if the question needs database data/analysis
        - "CONVERSATIONAL" if it's asking for opinions, suggestions, or general advice
        
        Examples:
        - "What are the top selling products?" → SQL
        - "What is your suggestion?" → CONVERSATIONAL
        - "Show me sales by category" → SQL
        - "How can I improve sales?" → CONVERSATIONAL
        """
        
        classification_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": classification_prompt}]
        )
        
        question_type = classification_response.choices[0].message.content.strip().upper()
        
        if question_type == "CONVERSATIONAL":
            # Handle conversational questions
            print(f"\nCONVERSATIONAL RESPONSE:")
            print("=" * 60)
            
            self.chat_history.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.chat_history
            )
            
            self.chat_history.append({'role':'assistant', 'content': response.choices[0].message.content})
            
            print(response.choices[0].message.content)
            print("=" * 60)
            print("\n")
            
        else:
            # Handle SQL-based questions
            query = self.generate_sql(prompt)
            print(f"\nGenerated SQL Query:")
            print("-" * 50)
            print(query)
            print("-" * 50)
            
            # Execute the generated SQL query
            self.sql_results = self.sql_runner.run_single_query(query, prompt)
            
            all_results_str = ""
            for result in self.sql_results:
                all_results_str += f"\n{result['description']}:\n"
                all_results_str += result['data'].to_string()
                all_results_str += "\n" + "="*50 + "\n"

            self.chat_history.append( {"role": "user", "content": f"Here are the SQL query results:\n{all_results_str}, {prompt}"})
             
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages= self.chat_history
            )

            self.chat_history.append({'role':'assistant', 'content': response.choices[0].message.content})
            
            print(f"\nQUERY RESULTS:")
            print("=" * 60)
            for result in self.sql_results:
                print(f"\n{result['description']}:")
                print("-" * 40)
                print(result['data'])
                print("-" * 40)
            
            print(f"\nAI ANALYSIS:")
            print("=" * 60)
            print(response.choices[0].message.content)
            print("=" * 60)
            print("\n")
            
            return response.choices[0].message.content
    
    def ask_ai_api(self, prompt):
        """
        API-friendly version of ask_ai that returns structured JSON response
        """
        try:
            # Use AI to determine if this question
            classification_prompt = f"""
            Analyze this question and determine if it requires SQL database querying or is a conversational question.
            
            Question: "{prompt}"
            
            Respond with ONLY one word:
            - "SQL" if the question needs database data/analysis
            - "CONVERSATIONAL" if it's asking for opinions, suggestions, or general advice
            
            Examples:
            - "What are the top selling products?" → SQL
            - "What is your suggestion?" → CONVERSATIONAL
            - "Show me sales by category" → SQL
            - "How can I improve sales?" → CONVERSATIONAL
            """
            
            classification_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": classification_prompt}]
            )
            
            question_type = classification_response.choices[0].message.content.strip().upper()
            
            if question_type == "CONVERSATIONAL":
                # Handle conversational questions
                self.chat_history.append({"role": "user", "content": prompt})
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=self.chat_history
                )
                
                self.chat_history.append({'role':'assistant', 'content': response.choices[0].message.content})
                
                return {
                    "status": "success",
                    "question_type": "conversational",
                    "prompt": prompt,
                    "response": response.choices[0].message.content,
                    "sql_query": None,
                    "data": None
                }
            else:
                # Handle SQL-based questions
                query = self.generate_sql(prompt)
                
                # Execute the generated SQL query
                self.sql_results = self.sql_runner.run_single_query(query, prompt)
                
                # Format data for JSON response
                formatted_data = []
                for result in self.sql_results:
                    formatted_data.append({
                        "description": result['description'],
                        "data": result['data'].to_dict('records') if hasattr(result['data'], 'to_dict') else str(result['data']),
                        "row_count": len(result['data']) if hasattr(result['data'], '__len__') else 0
                    })
                
                all_results_str = ""
                for result in self.sql_results:
                    all_results_str += f"\n{result['description']}:\n"
                    all_results_str += result['data'].to_string()
                    all_results_str += "\n" + "="*50 + "\n"

                self.chat_history.append( {"role": "user", "content": f"Here are the SQL query results:\n{all_results_str}, {prompt}"})
                 
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages= self.chat_history
                )

                self.chat_history.append({'role':'assistant', 'content': response.choices[0].message.content})
                
                return {
                    "status": "success",
                    "question_type": "sql",
                    "prompt": prompt,
                    "sql_query": query,
                    "data": formatted_data,
                    "analysis": response.choices[0].message.content,
                    "total_results": len(formatted_data)
                }
                
        except Exception as e:
            return {
                "status": "error",
                "prompt": prompt,
                "error": str(e),
                "message": "An error occurred while processing your request"
            }
    
    def generate_sql(self, prompt): 
        sys_prompt ="""
        You are a SQL expert. Generate ONLY a valid SQL query for PostgreSQL. Do not include any explanations, markdown formatting, or additional text. Return only the SQL query that can be executed directly.

        Database Schema Context:
        - department(depart_id, depart_name): Organization departments (e.g., Electronics, Fashion)
        - staff(staff_id, department_id, last_name, first_name): Employees who manage departments
        - seller(seller_id, description, address, state_province): Vendors who list products
        - customer(customer_id, first_name, last_name, email, address, state): Buyers (customers)
        - app_user(user_id, customer_id, seller_id, first_name, last_name, password, email, registed_date): Users (customers or sellers) of the application
        - product(product_id, seller_id, description, category, product_price, product_name): Items listed for sale
        - bid(bid_id, product_id, customer_id, bid_amount, bid_date): Customer bids on products
        - order_header(order_id, customer_id, bid_id, product_id, shipping_id, quantity, order_date): Records of completed purchases
        - shipping(shipping_id, carrier, shipping_date): Shipping information
        - payment(payment_id, order_id, amount): Payments associated with orders
        - order_history(history_id, customer_id, order_id): Historical record of customer orders
        - import_distribution(import_id, shipping_id, received_date): Logistics tracking for international shipments
        - export_distribution(export_id, shipping_id, delivered_date): Logistics tracking for international shipments
        - customer_service(cservice_id, staff_id, customer_id, duration_hours, service_date, description): Support tickets and service logs
        - seller_service(sservice_id, seller_id, staff_id, duration_hours, service_date, description): Support tickets and service logs
        - customer_review(review_id, customer_id, product_id, description, rating): Reviews for products
        - seller_review(sreview_id, seller_id, description): Reviews for sellers

        Important: To calculate total sales/revenue, use: SUM(order_header.quantity * product.product_price)
        The order_header table does NOT have a total_amount column.

        Return ONLY the SQL query, nothing else.
        """
        
        response = client.chat.completions.create(
            model='gpt-4o',
            messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": f"Convert this question to SQL: {prompt}"}
            ]
        )
        
        sql_response = response.choices[0].message.content.strip()
        
        # Remove any markdown formatting or explanatory text
        if "```sql" in sql_response:
            start = sql_response.find("```sql") + 6
            end = sql_response.find("```", start)
            if end != -1:
                sql_response = sql_response[start:end].strip()
        elif "```" in sql_response:
            start = sql_response.find("```") + 3
            end = sql_response.find("```", start)
            if end != -1:
                sql_response = sql_response[start:end].strip()
        
        # Remove any remaining explanatory text (lines that don't look like SQL)
        lines = sql_response.split('\n')
        sql_lines = []
        for line in lines:
            line = line.strip()
            # Skip lines that are clearly not SQL (explanatory text)
            if (line and 
                not line.startswith('--') and 
                not line.startswith('1.') and 
                not line.startswith('2.') and 
                not line.startswith('3.') and 
                not line.startswith('**') and
                not line.startswith('Here') and
                not line.startswith('The') and
                not line.startswith('This')):
                sql_lines.append(line)
        
        return '\n'.join(sql_lines)
   
if __name__ == "__main__":
    ai = AISQLRunner()
    
    while True:
        print("ask me questions about e-commerce dataset! Type 'exit' or 'end' to exit!")
        user_input = input('You: ')
        
        if user_input.lower() in ['exit', 'end']:
            print('goodbye!')
            break
        
        # Run analysis queries
        ai.ask_ai(prompt=user_input)
        


