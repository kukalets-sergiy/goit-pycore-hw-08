"""Console assistant for managing contacts and birthdays."""

# pickle is used for serializing and deserializing Python objects to and from disk
import pickle
# functools is used to create decorators that preserve the original function's metadata
from functools import wraps
from contact_book import AddressBook, Record


# Define the default filename for storing the address book data
DATA_FILE = "addressbook.pkl"


# Write the address book to disk using pickle serialization
def save_data(book, filename=DATA_FILE):
    """Serialize the address book to disk."""
    # Use a context manager to open the file in binary write mode
    with open(filename, "wb") as file:
        # Serialize the address book object and write it to the file
        pickle.dump(book, file)


# Read the address book from disk using pickle deserialization
def load_data(filename=DATA_FILE):
    """Load the saved address book, or create an empty one if none exists."""
    try:
        # Use a context manager to open the file in binary read mode
        with open(filename, "rb") as file:
            # Deserialize the address book object from the file
            book = pickle.load(file)
    except FileNotFoundError:
        return AddressBook()

    if not isinstance(book, AddressBook):
        raise TypeError(f"Saved data in {filename} is not an address book.")
    return book


# Parameterized decorator to validate command argument counts and translate expected input errors
def input_error(expected_args: int, usage: str):
    """Validate command argument counts and translate expected input errors."""
    # Define a decorator that takes a function as an argument
    def decorator(func):
        # Use functools.wraps to preserve the original function's metadata
        @wraps(func)
        # Define an inner function that wraps the decorated function
        def inner(args, *handler_args, **handler_kwargs):
            # Validate the argument count before calling the command handler
            if len(args) != expected_args:
                return usage
            try:
                # Execute the command handler with validated arguments
                return func(args, *handler_args, **handler_kwargs)
            except KeyError:
                # Convert missing contacts into a user-friendly message
                return "Contact not found."
            except ValueError as error:
                # Return validation errors directly to the user
                return str(error)
            except Exception as error:
                # Catch any unexpected exceptions and return a generic error message
                return f"An unexpected error occurred: {error}"

        # Return the wrapped command handler
        return inner

    # Return the decorator configured for the command
    return decorator


def parse_input(user_input):
    """Split user input into a lowercase command and its arguments."""
    # Split the input string into parts based on whitespace
    parts = user_input.split()
    # If the input is empty, return an empty command and no arguments
    if not parts:
        return "", []
    # Unpack the first part as the command and the rest as arguments
    command, *args = parts
    # Return the command in lowercase along with its arguments
    return command.lower(), args


# Use the parameterized decorator to validate argument counts for each command handler
@input_error(2, "Usage: add name phone")
def add_contact(args, book):
    """Add a new contact or add a phone to an existing contact."""
    # Unpack the contact name and phone number
    name, phone = args
    # Search for the contact without considering letter case
    record = book.find(name)
    if record is None:
        # Create and store a new contact when it does not exist
        record = Record(name)
        record.add_phone(phone)
        book.add_record(record)
        return "Contact added."

    # Add another phone number to an existing contact
    record.add_phone(phone)
    return "Contact updated."


@input_error(3, "Usage: change name old_phone new_phone")
def change_contact(args, book):
    """Change an existing contact's phone number."""
    # Unpack the contact name and both phone numbers
    name, old_phone, new_phone = args
    # Find the contact using case-insensitive lookup
    record = book.find(name)
    if record is None:
        return "Contact not found."
    # Replace the old phone number with the new one
    record.edit_phone(old_phone, new_phone)
    return "Contact updated."


@input_error(1, "Usage: phone name")
def show_phone(args, book):
    """Return all phone numbers saved for a contact."""
    # Find the requested contact by name
    record = book.find(args[0])
    if record is None:
        return "Contact not found."
    # Handle contacts that do not have phone numbers
    if not record.phones:
        return "No phone numbers saved."
    # Return all saved phone numbers in a readable format
    return "; ".join(str(phone) for phone in record.phones)


def show_all(book):
    """Return all saved contacts as a formatted string."""
    # Check if there are any contacts saved
    if not book:
        return "No contacts saved."
    # Return all contacts as formatted strings
    return "\n".join(str(record) for record in book.data.values())


@input_error(2, "Usage: add-birthday name DD.MM.YYYY")
def add_birthday(args, book):
    """Add a birthday to an existing contact."""
    # Unpack the contact name and birthday date
    name, birthday = args
    # Find the contact using case-insensitive lookup
    record = book.find(name)
    if record is None:
        return "Contact not found."
    # Validate and save the birthday
    record.add_birthday(birthday)
    return "Birthday added."


@input_error(1, "Usage: show-birthday name")
def show_birthday(args, book):
    """Return the birthday saved for a contact."""
    # Find the requested contact by name
    record = book.find(args[0])
    if record is None:
        return "Contact not found."
    # Report when the contact does not have a birthday
    if record.birthday is None:
        return "Birthday not set."
    # Format the stored date for display
    return record.birthday.value.strftime("%d.%m.%Y")


@input_error(0, "Usage: birthdays")
def birthdays(args, book):
    """Return contacts with birthdays during the following seven days."""
    # Get upcoming birthdays from the address book
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the next 7 days."
    # Format each upcoming birthday for display
    return "\n".join(
        f"{item['name']}: {item['congratulation_date']}" for item in upcoming
    )


# The main function to run the assistant command loop
def main():
    """Run the assistant command loop."""
    # Restore the address book from the saved file or create a new one if it doesn't exist
    book = load_data()
    # Map command names to their handler functions
    handlers = {
        "add": add_contact,
        "change": change_contact,
        "phone": show_phone,
        # Handle the "show all" command with a lambda function to pass the address book
        "all": lambda args, address_book: show_all(address_book),
        "add-birthday": add_birthday,
        "show-birthday": show_birthday,
        "birthdays": birthdays,
    }
    # Print a welcome message to the user
    print("Welcome to the assistant bot!")

    # Use a try-finally block to ensure that data is saved even if an error occurs
    try:
        # Start an infinite loop to continuously prompt the user for commands
        while True:
            try:
                # Prompt the user for input and store it in the variable user_input
                user_input = input("Enter a command: ")
            # Handle exceptions for end-of-file (EOF) => (Ctrl+D) or keyboard interrupt (Ctrl+C)
            except (EOFError, KeyboardInterrupt):
                print("\nGood bye!")
                break

            # Parse the user input into a command and its arguments
            command, args = parse_input(user_input)
            # Check if the command is "close" or "exit" to terminate the loop
            if command in ("close", "exit"):
                print("Good bye!")
                break
            # Handle the "hello" command by greeting the user
            if command == "hello":
                print("How can I help you?")
            # Handle all registered commands through their handlers
            elif command in handlers:
                # Call the appropriate command handler and print its result
                print(handlers[command](args, book))
            else:
                print("Invalid command.")
    # finally block ensures that the address book is saved to disk even if an error occurs
    finally:
        # Save the address book to disk before exiting
        save_data(book)


# If the script is being run directly, call the main function
if __name__ == "__main__":
    main()
