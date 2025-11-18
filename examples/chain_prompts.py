"""Chain prompts example using the prompt engineering utilities."""

import asyncio
from src.prompt_engineering.chain import create_code_generation_chain


async def chain_prompts_example():
    """Example of using chain prompts for complex code generation."""
    
    print("🔗 Chain Prompts Example")
    print("=" * 50)
    
    # Create a code generation chain
    chain = create_code_generation_chain()
    
    # User request context
    context = {
        "user_request": "Create a Python web scraper that extracts product information from an e-commerce website and saves it to a CSV file"
    }
    
    print(f"📝 User Request: {context['user_request']}")
    print("\n🔄 Processing through chain steps...")
    
    # Simulate processing each step
    steps_results = {
        "analysis": """
Analysis:
1. Programming language: Python
2. Key functionality: Web scraping, data extraction, CSV export
3. Input/output: URL input, CSV file output
4. Constraints: Handle rate limiting, respect robots.txt
5. Complexity: Intermediate
        """.strip(),
        
        "planning": """
Implementation Plan:
1. Components: HTTP client, HTML parser, CSV writer, rate limiter
2. Data structures: Product class, scraped data list
3. Algorithm: Request -> Parse -> Extract -> Store -> Export
4. Error handling: Network errors, parsing errors, file I/O errors
5. Testing: Unit tests for each component
        """.strip(),
        
        "generation": """
```python
import requests
from bs4 import BeautifulSoup
import csv
import time
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Product:
    name: str
    price: str
    description: str
    url: str

class WebScraper:
    def __init__(self, delay: float = 1.0):
        self.session = requests.Session()
        self.delay = delay
        
    def scrape_products(self, urls: List[str]) -> List[Product]:
        products = []
        for url in urls:
            try:
                response = self.session.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                product = self._extract_product_info(soup, url)
                
                if product:
                    products.append(product)
                    
                time.sleep(self.delay)
                
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                
        return products
    
    def _extract_product_info(self, soup: BeautifulSoup, url: str) -> Optional[Product]:
        # Implementation depends on website structure
        pass
    
    def save_to_csv(self, products: List[Product], filename: str):
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Name', 'Price', 'Description', 'URL'])
            
            for product in products:
                writer.writerow([product.name, product.price, product.description, product.url])
```
        """.strip(),
        
        "validation": """
Validation Results:
✅ Syntax: Code is syntactically correct
✅ Logic: Proper error handling and rate limiting
✅ Edge cases: Handles network errors and parsing failures
✅ Best practices: Uses dataclasses, type hints, proper structure
⚠️  Performance: Consider adding async support for better performance
✅ Security: Uses session for connection pooling
        """.strip()
    }
    
    # Process each step in the chain
    for step_name in chain.execution_order:
        print(f"\n🔧 Step: {step_name.upper()}")
        
        # Get the formatted prompt for this step
        try:
            prompt = chain.format_step_prompt(step_name, context)
            print(f"📋 Prompt preview: {prompt[:100]}...")
            
            # Simulate execution (in real scenario, this would call the LLM)
            result = steps_results.get(step_name, f"Result for {step_name}")
            chain.execute_step(step_name, result, context)
            
            print(f"✅ Completed: {step_name}")
            print(f"📄 Result preview: {result[:150]}...")
            
        except Exception as e:
            print(f"❌ Error in step {step_name}: {e}")
            break
    
    # Get final result
    if chain.is_complete():
        final_result = chain.get_final_result()
        print(f"\n🎉 Chain completed successfully!")
        print(f"📊 Final result preview: {final_result[:200]}...")
    else:
        print(f"\n⚠️  Chain incomplete. Next step: {chain.get_next_step()}")


if __name__ == "__main__":
    asyncio.run(chain_prompts_example())