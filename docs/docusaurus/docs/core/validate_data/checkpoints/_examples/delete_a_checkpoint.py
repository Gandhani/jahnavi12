"""
This example script demonstrates how to retrieve an existing Checkpoint
 from a Data Context and then delete it from the Data Context configuration.

The <snippet> tags are used to insert the corresponding code into the
 Great Expectations documentation.  They can be disregarded by anyone
 reviewing this script.
"""

# <snippet name="/core/validate_data/checkpoints/_examples/delete_a_checkpoint.py full example script">
import great_expectations as gx

context = gx.get_context()

# <snippet name="/core/validate_data/checkpoints/_examples/delete_a_checkpoint.py delete checkpoint">
checkpoint_name = "my_checkpoint"
# highlight-start
context.checkpoints.delete(name=checkpoint_name)
# highlight-end
# </snippet>
# </snippet>
