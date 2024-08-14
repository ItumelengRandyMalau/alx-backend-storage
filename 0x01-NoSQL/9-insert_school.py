#!/usr/bin/env python3
"""inserts a new document in a collection based on kwargs"""
def insert_school(mongo_collection, **kwargs):
    """
    Insert a new document into the specified MongoDB collection.

    Args:
        mongo_collection (pymongo.collection.Collection): The pymongo collection object.
        **kwargs: The document fields and values to be inserted.

    Returns:
        The _id of the newly inserted document.
    """
    # Insert the document and get the result
    result = mongo_collection.insert_one(kwargs)
    
    # Return the _id of the new document
    return result.inserted_id
