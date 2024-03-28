"""
This example script demonstrates how to update a Checkpoint's Validation Definitions
  and Actions list, and persist those changes to the Data Context.

The <snippet> tags are used to insert the corresponding code into the
 Great Expectations documentation.  They can be disregarded by anyone
 reviewing this script.
"""

# <snippet name="/core/validate_data/checkpoints/_examples/update_a_checkpoint.py full example script">
import great_expectations as gx

context = gx.get_context()

checkpoint_name = "my_checkpoint"
checkpoint = context.checkpoints.get(name=checkpoint_name)

# <snippet name="/core/validate_data/checkpoints/_examples/update_a_checkpoint.py full update values">
new_validations_list = [context.validation_definitions.get(name="new_validation")]
new_actions_list = [gx.UpdateDataDocs(...)]

# highlight-start
checkpoint.validations = new_validations_list
checkpoint.actions = new_actions_list
# highlight-end
# </snippet>

# highlight-start
# <snippet name="/core/validate_data/checkpoints/_examples/update_a_checkpoint.py full save updates">
checkpoint.save()
# </snippet>
# highlight-end
# </snippet>
