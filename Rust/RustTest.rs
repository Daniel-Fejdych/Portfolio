// =====================================
// Library Management System Test
// =====================================
//
// This program models a library that holds books and users.
// Users can borrow and return books. All operations are tracked
// and errors are handled gracefully using Rust's `Result` type.
//
// Key Rust concepts demonstrated:
// - Structs and enums
// - Ownership, borrowing, and references
// - Methods and associated functions (impl blocks)
// - `HashMap` and `Vec` collections
// - `Result` and custom error types
// - Pattern matching (`match`, `if let`)
// - `println!` formatting and `derive` attributes

use std::collections::HashMap;

// ===========================
// 1. Data Definitions
// ===========================

/// A unique identifier for a book. We'll use a simple `u32`.
type BookId = u32;

/// A unique identifier for a user.
type UserId = u32;

/// Represents a book in the library.
#[derive(Debug, Clone)] // `derive` automatically implements common traits
struct Book {
    id: BookId,
    title: String,
    author: String,
    year: u16,
}

/// Represents a library user.
#[derive(Debug, Clone)]
struct User {
    id: UserId,
    name: String,
    // This user currently holds the IDs of borrowed books.
    borrowed_books: Vec<BookId>,
}

/// Custom error type for library operations.
/// Using `#[derive(Debug)]` allows us to print errors.
#[derive(Debug)]
enum LibraryError {
    BookNotFound(BookId),
    UserNotFound(UserId),
    BookAlreadyBorrowed(BookId),
    BookNotBorrowedByUser(BookId, UserId),
}

// We implement the standard `std::fmt::Display` trait for user-friendly error messages.
impl std::fmt::Display for LibraryError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            LibraryError::BookNotFound(id) => write!(f, "Book with ID {} not found", id),
            LibraryError::UserNotFound(id) => write!(f, "User with ID {} not found", id),
            LibraryError::BookAlreadyBorrowed(id) => write!(f, "Book {} is already borrowed", id),
            LibraryError::BookNotBorrowedByUser(id, uid) => {
                write!(f, "User {} has not borrowed book {}", uid, id)
            }
        }
    }
}

// `Result` with our custom error type will be used in library methods.
type Result<T> = std::result::Result<T, LibraryError>;

// ===========================
// 2. Library Core
// ===========================

/// The main library structure. It owns all books and users.
struct Library {
    // Maps a book ID to its Book struct.
    books: HashMap<BookId, Book>,
    // Maps a user ID to its User struct.
    users: HashMap<UserId, User>,
    // Simple counters to generate new IDs.
    next_book_id: BookId,
    next_user_id: UserId,
}

impl Library {
    /// Creates a new empty library.
    /// This is an associated function (like a static method).
    fn new() -> Self {
        Library {
            books: HashMap::new(),
            users: HashMap::new(),
            next_book_id: 1,  // start IDs from 1
            next_user_id: 1,
        }
    }

    /// Adds a new book to the library. The ID is auto-generated.
    /// Takes ownership of `title` and `author` (`String`).
    /// Returns the ID of the newly added book.
    fn add_book(&mut self, title: String, author: String, year: u16) -> BookId {
        let id = self.next_book_id;
        self.next_book_id += 1;
        let book = Book {
            id,
            title,
            author,
            year,
        };
        // Insert the book into the HashMap, keyed by ID.
        self.books.insert(id, book);
        id
    }

    /// Adds a new user. Returns the user's ID.
    fn add_user(&mut self, name: String) -> UserId {
        let id = self.next_user_id;
        self.next_user_id += 1;
        let user = User {
            id,
            name,
            borrowed_books: Vec::new(),
        };
        self.users.insert(id, user);
        id
    }

    /// Allows a user to borrow a book.
    /// - `user_id`: ID of the user borrowing.
    /// - `book_id`: ID of the book to borrow.
    /// Returns `Ok(())` on success, or a `LibraryError` if:
    ///   - User or book doesn't exist.
    ///   - Book is already borrowed (by any user).
    ///
    /// Note: The method takes `&mut self` because it modifies the library's state.
    /// It borrows `user_id` and `book_id` by value (they are `Copy` types).
    fn borrow_book(&mut self, user_id: UserId, book_id: BookId) -> Result<()> {
        // 1. Check that the book exists and is not already borrowed.
        //    We need to peek at the book's status without moving it out of the map.
        let book_exists = self.books.contains_key(&book_id);
        if !book_exists {
            return Err(LibraryError::BookNotFound(book_id));
        }

        // Determine if the book is already borrowed by any user.
        // We iterate over all users to see if any user's `borrowed_books` contains this book_id.
        let already_borrowed = self.users.values().any(|user| user.borrowed_books.contains(&book_id));
        if already_borrowed {
            return Err(LibraryError::BookAlreadyBorrowed(book_id));
        }

        // 2. Get mutable reference to the user (if exists).
        let user = self.users.get_mut(&user_id).ok_or(LibraryError::UserNotFound(user_id))?;
        // Add the book ID to the user's borrowed list.
        user.borrowed_books.push(book_id);
        Ok(())
    }

    /// Returns a book that was borrowed.
    /// - `user_id`: the user returning the book.
    /// - `book_id`: the book being returned.
    fn return_book(&mut self, user_id: UserId, book_id: BookId) -> Result<()> {
        // Get mutable reference to the user.
        let user = self.users.get_mut(&user_id).ok_or(LibraryError::UserNotFound(user_id))?;
        // Find the position of the book in the user's borrowed list.
        let pos = user.borrowed_books.iter().position(|&id| id == book_id);
        match pos {
            Some(index) => {
                // Remove the book from the vector (it's a `Vec`, so removal by index shifts elements).
                user.borrowed_books.remove(index);
                Ok(())
            }
            None => Err(LibraryError::BookNotBorrowedByUser(book_id, user_id)),
        }
    }

    /// Lists all books in the library with their current availability.
    /// This method only reads data, so it takes `&self` (immutable borrow).
    fn list_books(&self) {
        println!("===== Library Books =====");
        for (id, book) in &self.books {
            // Check if the book is currently borrowed.
            let borrowed = self.users.values().any(|user| user.borrowed_books.contains(id));
            let status = if borrowed { "Borrowed" } else { "Available" };
            println!(
                "ID: {} | \"{}\" by {} ({}) - {}",
                id, book.title, book.author, book.year, status
            );
        }
    }

    /// Lists all registered users and the books they currently have.
    fn list_users(&self) {
        println!("===== Library Users =====");
        for (id, user) in &self.users {
            println!("User ID: {} | Name: {}", id, user.name);
            if user.borrowed_books.is_empty() {
                println!("  No books borrowed.");
            } else {
                println!("  Borrowed books:");
                for book_id in &user.borrowed_books {
                    // `get` returns an `Option<&Book>`. We use `if let` to handle it gracefully.
                    if let Some(book) = self.books.get(book_id) {
                        println!("    - ID {}: \"{}\"", book_id, book.title);
                    } else {
                        // This should never happen if our data is consistent, but we handle it.
                        println!("    - ID {}: (unknown book)", book_id);
                    }
                }
            }
        }
    }
}

// ===========================
// 3. Main Program
// ===========================

fn main() {
    // Create a new library (mutable because we will add and modify).
    let mut library = Library::new();

    // Add some books. Note that we pass `String` values (using `to_string()`).
    let book1_id = library.add_book("The Rust Programming Language".to_string(), "Steve Klabnik".to_string(), 2018);
    let book2_id = library.add_book("Programming Rust".to_string(), "Jim Blandy".to_string(), 2016);
    let book3_id = library.add_book("Rust in Action".to_string(), "Tim McNamara".to_string(), 2021);

    // Add some users.
    let alice_id = library.add_user("Alice".to_string());
    let bob_id = library.add_user("Bob".to_string());

    // Initial state: all books available.
    library.list_books();
    library.list_users();

    println!("\n--- Alice borrows 'The Rust Programming Language' ---");
    // Attempt to borrow a book. `match` is used to handle the `Result`.
    match library.borrow_book(alice_id, book1_id) {
        Ok(()) => println!("Alice successfully borrowed book {}", book1_id),
        Err(e) => println!("Error: {}", e),
    }

    println!("\n--- Bob borrows 'Programming Rust' ---");
    if let Err(e) = library.borrow_book(bob_id, book2_id) {
        // `if let` is a concise way to match only one variant.
        println!("Error: {}", e);
    } else {
        println!("Bob successfully borrowed book {}", book2_id);
    }

    println!("\n--- Alice tries to borrow the same book again (should fail) ---");
    // This should fail because the book is already borrowed by Alice.
    match library.borrow_book(alice_id, book1_id) {
        Ok(()) => println!("Alice borrowed the book again?"),
        Err(e) => println!("Error (expected): {}", e),
    }

    // Show updated library state.
    println!();
    library.list_books();
    library.list_users();

    println!("\n--- Alice returns 'The Rust Programming Language' ---");
    match library.return_book(alice_id, book1_id) {
        Ok(()) => println!("Alice returned the book."),
        Err(e) => println!("Error: {}", e),
    }

    println!("\n--- Bob tries to return a book he never borrowed (should fail) ---");
    match library.return_book(bob_id, book3_id) {
        Ok(()) => println!("Bob returned a book he didn't have?"),
        Err(e) => println!("Error (expected): {}", e),
    }

    // Final snapshot.
    println!();
    library.list_books();
    library.list_users();
}
