from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.sqltypes import Boolean

# FastAPI instance
app = FastAPI()

# Database configuration (SQLite for local development)
DATABASE_URL = "postgresql://arthecs:oUq5AMTHHbHJGOyhyjO3@booksdb.c5uo2eyg2y7i.ap-south-1.rds.amazonaws.com/booksdb" # use localdb address("sqlite:///./test.db") for using in local IDE 
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Book model
class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    quantity = Column(Integer,index = True)
    availability = Column(Boolean , index = True)

# Pydantic model
class AddBook(BaseModel):
    title: str
    author: str
    quantity:int
    availability:bool = True

#book model for creating multiple books at same time
class AddBooks(BaseModel):
    books: list[AddBook]
#books model for updating books
class UpdateBook(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    quantity: Optional[int] = None
    availability:Optional[bool] = None

# Create database tables
Base.metadata.create_all(bind=engine)
#post request for creating new books
@app.post("/books/", response_model=dict)
def create_books(add_books: AddBooks):
    db = SessionLocal()
    book_ids =[]
    try:
        for book in add_books.books:
            db_book = Book(title=book.title, author=book.author , quantity = book.quantity , availability = book.availability)
            db.add(db_book)
            db.commit()
            db.refresh(db_book)
            book_ids.append(db_book.id)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error saving books")
    finally:
        db.close()
    return {"message": "Books added successfully", "book_ids": book_ids}

#Get response for retrieving all books

@app.get("/books", response_model=List[dict])
def get_all_books():
    db = SessionLocal()
    books = db.query(Book).all()
    db.close()
    if not books:
        raise HTTPException(status_code=404, detail="No books found")
    return [{"id": book.id, "title": book.title, "author": book.author , "quantity": book.quantity , "availability": book.availability} for book in books]
#Get book with id
@app.get("/books/{book_id}", response_model=dict)
def search_book(book_id: int):
    db = SessionLocal()
    db_book = db.query(Book).filter(Book.id == book_id).first()
    db.close()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"id": db_book.id, "title": db_book.title, "author": db_book.author , "quantity": db_book.quantity , "availability": db_book.availability}
#update book details with id
@app.put("/books/{book_id}", response_model=dict)
def update_book(book_id: int, book: UpdateBook):
    db = SessionLocal()
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if book.title is not None:
        db_book.title = book.title
    if book.author is not None:
        db_book.author = book.author
    if book.quantity is not None:
        db_book.quantity = book.quantity
    if book.availability is not None:
        db_book.availability = book.availability
    db.commit()
    db.refresh(db_book)
    db.close()
    return {"message": "Book updated successfully", "book_id": book_id}
#delete single book with id
@app.delete("/books/{book_id}", response_model=dict)
def delete_book(book_id: int):
    db = SessionLocal()
    db_task = db.query(Book).filter(Book.id == book_id).first()
    if not db_task:
        db.close()
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    db.close()
    return {"detail": "book deleted successfully"}
#delete multiple books with ids
@app.delete("/books", response_model=dict)
def delete_books(book_ids: List[int]):
    db = SessionLocal()
    try:
        books_to_delete = db.query(Book).filter(Book.id.in_(book_ids)).all()
        if not books_to_delete:
            raise HTTPException(status_code=404, detail="No books found with the given IDs")
        
        for book in books_to_delete:
            db.delete(book)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error deleting books")
    finally:
        db.close()
    
    return {"message": "Books deleted successfully", "deleted_ids": book_ids}
