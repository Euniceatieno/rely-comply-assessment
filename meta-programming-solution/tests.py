from unittest import TestCase
import unittest
from textwrap import dedent
from dataclasses import dataclass
from typing import Callable, Any, Dict


@dataclass
class Field:
    """
    Defines a field with a label and preconditions
    """
    label: str
    precondition: Callable[[Any], bool] = None

# Record and supporting classes here
class RecordMeta(type):
    def __new__(cls, name, bases, attrs):
        fields_dict = {}
        for base in bases:
            if hasattr(base, 'fields'):
                fields_dict.update(base.fields) # update the fields_dict with fields from the base class if they exist
        for key, value in attrs.items():
            if isinstance(value, Field):
                fields_dict[key] = value

        attrs['fields'] = fields_dict
        
        new_cls = super(RecordMeta, cls).__new__(cls, name, bases, attrs)
        # generate a constructor that takes the appropriate keyword arguments.
        def __init__(self, **kwargs):

            for kwarg in kwargs:
                # If an extra argument is given it must raise a TypeError
                if kwarg not in new_cls.fields:
                    raise TypeError(f"{kwarg} is an extra argument !")

            for field_name, field in new_cls.fields.items():
                # If an argument is missing it must raise a TypeError
                if field_name not in kwargs:
                    raise TypeError(f"{field_name} is missing")
                
                value = kwargs[field_name]
                
                # Getting the field type from annotations in the parent class if exists
                field_type = new_cls.__annotations__.get(field_name)
                for clas in new_cls.mro():
                    if field_name in getattr(clas, '__annotations__', {}):
                        field_type =  clas.__annotations__[field_name]

                # If the argument is given with the incorrect type it must raise a TypeError 
                if type(value) is not field_type:
                    raise TypeError(f"Error : got {type(value)} intead of {field_type}")
                
                # arguments must check the precondition is one is given,
                # and raise a TypeError if the precondition is violated
                if field.precondition and not field.precondition(value):
                    raise TypeError(f"The value:{value} does not match the precondition for field:{field_name}")
                
                setattr(self, f"_{field_name}", value)
                def getter(self, field_name=field_name):
                    return getattr(self, f"_{field_name}")

                def setter(self, value, field_name=field_name):
                    # raise an AttributeError if an attempt is made to set a read only property after construction.
                    raise AttributeError(f" {field_name} is read only field and cannot be set")

                setattr(new_cls, field_name, property(getter, setter))  
        new_cls.__init__ = __init__      
        return new_cls

class Record(metaclass=RecordMeta):
    def __str__(self):
        output = [] #here we store the list of strings we want to print for each field
        count = len(self.fields)
        for i, (field_name, field) in enumerate(self.fields.items()):
            value = getattr(self, field_name)
            label = field.label if field.label else field_name
            output.append(f"  # {label}\n  {field_name}={value!r}\n")
            if i < count - 1:
                output.append("\n") #append an extra line for every string expect the last one
        return f"{self.__class__.__name__}(\n{''.join(output)})"

# Usage of Record
class Person(Record):
    """
    A simple person record
    """ 
    name: str = Field(label="The name") 
    age: int = Field(label="The person's age", precondition=lambda x: 0 <= x <= 150)
    income: float = Field(label="The person's income", precondition=lambda x: 0 <= x)

class Named(Record):
    """
    A base class for things with names
    """
    name: str = Field(label="The name") 

class Animal(Named):
    """
    An animal
    """
    habitat: str = Field(label="The habitat", precondition=lambda x: x in ["air", "land","water"])
    weight: float = Field(label="The animals weight (kg)", precondition=lambda x: 0 <= x)

class Dog(Animal):
    """
    A type of animal
    """
    bark: str = Field(label="Sound of bark")

# Tests 
class RecordTests(TestCase):
    def test_creation(self):
        Person(name="JAMES", age=110, income=24000.0)
        with self.assertRaises(TypeError): 
            Person(name="JAMES", age=160, income=24000.0)
        with self.assertRaises(TypeError): 
            Person(name="JAMES")
        with self.assertRaises(TypeError): 
            Person(name="JAMES", age=-1, income=24000.0)
        with self.assertRaises(TypeError): 
            Person(name="JAMES", age="150", income=24000.0)
        with self.assertRaises(TypeError): 
            Person(name="JAMES", age="150", wealth=24000.0)
    
    def test_properties(self):
        james = Person(name="JAMES", age=34, income=24000.0)
        self.assertEqual(james.age, 34)
        with self.assertRaises(AttributeError):
            james.age = 32
    
    def test_str(self):
        james = Person(name="JAMES", age=34, income=24000.0)
        correct = dedent("""
        Person(
          # The name
          name='JAMES'

          # The person's age
          age=34

          # The person's income
          income=24000.0
        )
        """).strip()
        self.assertEqual(str(james), correct)

    def test_dog(self):
        mike = Dog(name="mike", habitat="land", weight=50., bark="ARF")
        self.assertEqual(mike.weight, 50)
        
if __name__ == '__main__':
    unittest.main()