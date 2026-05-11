from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import os
from dotenv import load_dotenv

load_dotenv()

# Sample Clothes Catalog
PRODUCTS = [
    {
        "id": "1",
        "name": "Classic Blue Linen Shirt",
        "description": "A breathable, lightweight linen shirt in sky blue. Perfect for beach weddings or summer outings.",
        "category": "Shirts",
        "price": 45.00,
        "image": "assets/shirt.png"
    },
    {
        "id": "2",
        "name": "Slim-Fit Black Chinos",
        "description": "Versatile black chinos made from premium stretch cotton. Great for casual Friday or a night out.",
        "category": "Pants",
        "price": 60.00,
        "image": "assets/chinos.png"
    },
    {
        "id": "3",
        "name": "Vintage Floral Summer Dress",
        "description": "A beautiful knee-length dress with a 1950s floral pattern. Elegant and feminine for garden parties.",
        "category": "Dresses",
        "price": 85.00,
        "image": "assets/dress.png"
    },
    {
        "id": "4",
        "name": "Waterproof Hiking Jacket",
        "description": "Heavy-duty waterproof shell in forest green. Features adjustable hood and multiple pockets.",
        "category": "Outerwear",
        "price": 120.00,
        "image": "assets/jacket.png"
    },
    {
        "id": "5",
        "name": "Minimalist White Sneakers",
        "description": "Clean, vegan leather sneakers in optic white. A staple for any modern wardrobe.",
        "category": "Shoes",
        "price": 75.00,
        "image": "assets/sneakers.png"
    }
]

def ingest():
    print("Initializing embeddings...")
    embeddings = OpenAIEmbeddings()
    
    print("Preparing documents...")
    documents = []
    for p in PRODUCTS:
        # Create a detailed text representation for the vector search
        text = f"Name: {p['name']}\nDescription: {p['description']}\nCategory: {p['category']}\nPrice: ${p['price']}"
        doc = Document(
            page_content=text,
            metadata={"id": p['id'], "category": p['category'], "price": p['price'], "image": p['image']}
        )
        documents.append(doc)
    
    print(f"Ingesting {len(documents)} products into ChromaDB...")
    # Persist the DB in a local folder called 'chroma_db'
    db = Chroma.from_documents(
        documents, 
        embeddings, 
        persist_directory="./chroma_db"
    )
    # Chroma 0.4+ persists automatically on destruction, 
    # but some versions require a call. 
    # In latest langchain-community, it persists on exit.
    print("Successfully created chroma_db!")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in .env file.")
    else:
        ingest()
