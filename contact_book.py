"""Data models for the console address book."""

import re
from collections import UserDict
from datetime import datetime, timedelta


class Field:
    """A base class for fields in a contact record."""

    # Initialize the Field class with a value
    def __init__(self, value: str):
        self.value = value

    # Define a string representation for the Field class
    def __str__(self):
        return str(self.value)


# Define a Name class that inherits from Field
class Name(Field):
    """A required contact name."""

    # Initialize the Name class with a value and validate it
    def __init__(self, value):
        # Validate that the name is a non-empty string
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Name must be a non-empty string.")
        # Call the parent class constructor to set the value for the Name field
        super().__init__(value.strip())


class Phone(Field):
    """A phone number containing exactly 10 digits."""

    def __init__(self, value):
        # Validate that the phone number is a string of exactly 10 digits
        if not isinstance(value, str) or not re.fullmatch(r"[0-9]{10}", value):
            raise ValueError("Phone number must contain exactly 10 digits.")
        # Call the parent class constructor to set the value for the Phone field
        super().__init__(value)


class Birthday(Field):
    """A birthday stored as a datetime value."""

    def __init__(self, value):
        # Validate the required birthday format before parsing the date
        if not isinstance(value, str) or not re.fullmatch(r"[0-9]{2}\.[0-9]{2}\.[0-9]{4}", value):
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        try:
            # Convert the birthday string into a datetime object
            birthday = datetime.strptime(value, "%d.%m.%Y")
        except ValueError as error:
            # Report invalid calendar dates using the same format message
            raise ValueError("Invalid date format. Use DD.MM.YYYY") from error
        # Store the parsed birthday in the parent class
        super().__init__(birthday)


class Record:
    """A contact record containing phone numbers and an optional birthday."""

    # Initialize the Record class with a name, an empty list of phones, and an optional birthday
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone) -> Phone:
        """Add a phone number to the contact record."""
        # Validate and create a Phone object
        phone = Phone(phone)
        # Add the Phone object to the list of phones
        self.phones.append(phone)
        # Return the Phone object that was added
        return phone

    def find_phone(self, phone) -> Phone | None:
        """Find a phone number in the contact record."""
        # Use a generator expression to search for the phone number in the list of phones
        return next((item for item in self.phones if item.value == phone), None)

    def remove_phone(self, phone) -> None:
        """Remove a phone number from the contact record."""
        # Find the phone number in the list of phones
        found_phone = self.find_phone(phone)
        if found_phone is None:
            raise ValueError(f"Phone number {phone} not found.")
        # Remove the found phone number from the list of phones
        self.phones.remove(found_phone)

    def edit_phone(self, old_phone, new_phone) -> Phone:
        """Edit a phone number in the contact record."""
        # Find the phone number in the list of phones
        found_phone = self.find_phone(old_phone)
        if found_phone is None:
            raise ValueError(f"Phone number {old_phone} not found.")
        # Create a new Phone object with the new phone number
        replacement = Phone(new_phone)
        # Replace the old phone number with the new one in the list of phones
        self.phones[self.phones.index(found_phone)] = replacement
        # Return the new Phone object that was added
        return replacement

    def add_birthday(self, birthday) -> Birthday:
        """Add or replace the birthday for the contact."""
        # Keep an existing Birthday object or create one from the input string
        self.birthday = birthday if isinstance(birthday, Birthday) else Birthday(birthday)
        # Return the birthday object that was added
        return self.birthday

    def __str__(self):
        # Define a string representation for the Record class
        phones = "; ".join(str(phone) for phone in self.phones) or "no phones"
        birthday = ""
        if self.birthday:
            birthday = f", birthday: {self.birthday.value.strftime('%d.%m.%Y')}"
        # Return a formatted string with the contact name and phone numbers
        return f"Contact name: {self.name.value}, phones: {phones}{birthday}"


class AddressBook(UserDict):
    """A collection of contact records with case-insensitive name lookup."""

    def add_record(self, record) -> None:
        """Add a record to the address book."""
        # Look for an existing contact using case-insensitive search
        existing = self.find(record.name.value)
        if existing is not None:
            # Preserve the original spelling of an already saved name
            record.name = existing.name
            # Replace the existing record under its original key
            self.data[existing.name.value] = record
            return
        # Add the record to the address book
        self.data[record.name.value] = record

    def find(self, name) -> Record | None:
        """Find a record in the address book by name."""
        # Reject values that cannot be used as contact names
        if not isinstance(name, str):
            return None
        # Normalize the search value for a predictable case-insensitive lookup
        normalized_name = name.strip().casefold()
        # Compare normalized names while returning the original record
        return next(
            (record for record in self.data.values()
             if record.name.value.casefold() == normalized_name),
            None,
        )

    def delete(self, name) -> None:
        """Delete a record from the address book by name."""
        # Find the contact using the same case-insensitive lookup as other operations
        record = self.find(name)
        if record is None:
            raise KeyError(name)
        # Delete the record using its original name key
        del self.data[record.name.value]

    def get_upcoming_birthdays(self, today=None):
        """Return contacts whose birthdays are within the next seven days."""
        # Use the supplied date in tests or the current date in normal operation
        today = today or datetime.today().date()
        upcoming = []
        # Check every contact in the address book
        for record in self.data.values():
            # Contacts without birthdays are not included
            if record.birthday is None:
                continue

            # Extract the date from the Birthday field
            birthday = record.birthday.value
            birthday_date = birthday.date()
            birthday_this_year = None
            # Find the next occurrence, including a birthday near New Year
            for year in range(today.year, today.year + 5): # Check up to 5 years ahead
                try:
                    candidate = birthday_date.replace(year=year)
                except ValueError:
                    continue
                if candidate >= today:
                    birthday_this_year = candidate
                    break
            if birthday_this_year is None:
                continue

            # Keep birthdays that occur today or during the following seven days
            days_until_birthday = (birthday_this_year - today).days
            if not 0 <= days_until_birthday <= 7:
                continue

            # Move weekend congratulations to the following Monday
            congratulation_date = birthday_this_year
            if congratulation_date.weekday() == 5:
                congratulation_date += timedelta(days=2)
            elif congratulation_date.weekday() == 6:
                congratulation_date += timedelta(days=1)

            # Add the contact and its adjusted congratulations date to the result
            upcoming.append({
                "name": record.name.value,
                "congratulation_date": congratulation_date.strftime("%d.%m.%Y"),
            })

        # Return birthdays in chronological order
        return sorted(
            upcoming,
            key=lambda item: datetime.strptime(
                item["congratulation_date"], "%d.%m.%Y"
            ),
        )
